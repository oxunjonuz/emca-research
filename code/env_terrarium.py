"""Terrarium: grid-world environment for EMCA falsification experiments.

Design goals (see research/HYPOTHESES.md):
  * A hidden confounder (season) that correlates with reward but is not its cause.
  * A mid-life regime flip (non-stationarity) that punishes slow adaptation.
  * A multi-step causal chain (lever -> door -> treasure) unreachable without planning.
  * Homeostatic survival pressure (energy) so goals are not all extrinsic.
  * Small state space so tabular baselines are strong (no unfair advantage).
"""
import random

W, H = 9, 9
ACTIONS = ["up", "down", "left", "right", "eat", "grasp", "press", "wait"]

# Tile codes
EMPTY, BERRY, LEVER, DOOR, TREASURE, WALL = ".", "b", "L", "D", "T", "#"

# Fixed map layout (walls border + inner chamber holding treasure behind door)
MAP = [
    "#########",
    "#..b....#",
    "#.b.....#",
    "#....L..#",
    "#........",   # row 3 col 7 has lever; door below at row 5? keep simple below
    "#...D...#",
    "#..b.T..#",
    "#.b.....#",
    "#########",
]
# NOTE: MAP[3] is "#....L..#" (lever at (3,5)); MAP[5] "#...D...#" door at (5,4);
# treasure at (6,5). Door blocks movement until pressed lever opens it.

class Terrarium:
    def __init__(self, seed, regime_flip_at=3000):
        self.rng = random.Random(seed)
        self.seed = seed
        self.t = 0
        self.regime_flip_at = regime_flip_at
        self.energy = 60.0
        self.season = "warm"          # hidden confounder: warm -> berries visible near top
        self.door_open = False
        self.lever_used = False
        self.treasure_taken = 0
        self.berries_eaten = 0
        self.lever_presses = 0
        self.pos = [4, 4]
        self.alive = True
        self._spawn_berries()

    # ---------- world dynamics ----------
    def _spawn_berries(self):
        self.berries = set()
        # confounder: in warm season berries cluster near top rows (correlates with
        # energy recovery but eating is what causes it; season itself is not causal)
        n = 6 if self.season == "warm" else 3
        rows = range(1, 4) if self.season == "warm" else range(4, 7)
        while len(self.berries) < n:
            r = self.rng.choice(list(rows))
            c = self.rng.randrange(1, W - 1)
            if (r, c) not in self.berries and MAP[r][c] == EMPTY:
                self.berries.add((r, c))

    def obs(self):
        """Agent observation: local 3x3 view + vitals + affordances. No season label."""
        r, c = self.pos
        view = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    view.append(WALL)
                    continue
                ch = MAP[rr][cc]
                if ch == EMPTY and (rr, cc) in self.berries:
                    ch = BERRY
                if ch == DOOR and self.door_open:
                    ch = EMPTY
                view.append(ch)
        afford = []
        here = MAP[r][c]
        if (r, c) in self.berries:
            afford.append("eat")
        if here == LEVER:
            afford.append("press")
        afford.append("grasp")  # always allowed; usually useless (confounder object)
        return {
            "view": "".join(view),
            "energy": int(self.energy),
            "afford": tuple(sorted(afford)),
            "t": self.t,
        }

    def step(self, action):
        assert action in ACTIONS, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        self.t += 1
        r, c = self.pos
        reward = 0.0
        info = {}
        # regime flip: mid-life the world changes - berries scarce & move, lever resets
        if self.t == self.regime_flip_at:
            self.season = "cold"
            self.door_open = False
            self.lever_used = False
            self._spawn_berries()
            info["regime_flip"] = True
        # metabolism
        self.energy -= 0.5
        if action == "up":
            self._move(r - 1, c)
        elif action == "down":
            self._move(r + 1, c)
        elif action == "left":
            self._move(r, c - 1)
        elif action == "right":
            self._move(r, c + 1)
        elif action == "eat":
            if (r, c) in self.berries:
                self.berries.discard((r, c))
                gain = 10.0 if self.season == "warm" else 6.0
                self.energy = min(100.0, self.energy + gain)
                self.berries_eaten += 1
                reward += 1.0
                info["ate"] = True
        elif action == "press":
            if MAP[r][c] == LEVER:
                self.lever_used = True
                self.door_open = True
                self.lever_presses += 1
                info["lever"] = True
        elif action == "grasp":
            info["grasp"] = True  # never has effect: pure confounder action
        elif action == "wait":
            pass
        # treasure through open door
        if MAP[r][c] == TREASURE and (r, c) == (6, 5) and self.door_open:
            if self.treasure_taken == 0:
                reward += 20.0
                self.treasure_taken = 1
                info["treasure"] = True
        # death
        if self.energy <= 0:
            self.alive = False
            reward -= 5.0
            info["died"] = True
        # berry regrowth
        if self.t % 40 == 0:
            self._spawn_berries()
        return self.obs(), reward, not self.alive, info

    def _move(self, nr, nc):
        if not (0 <= nr < H and 0 <= nc < W):
            return
        ch = MAP[nr][nc]
        if ch == WALL:
            return
        if ch == DOOR and not self.door_open:
            return
        self.pos = [nr, nc]

    # ---------- ground truth for verification ----------
    def true_causal_edges(self):
        return {
            ("press", "door_open"): 1.0,
            ("door_open", "treasure"): 1.0,
            ("eat", "energy"): 1.0,
            ("energy", "alive"): 1.0,
        }

    def true_confounders(self):
        # season correlates with berry density (observation) but causes nothing the
        # agent can influence; grasp is an action correlated with nothing.
        return {"season->berry_density": "observational only", "grasp": "no effect"}


def run_episode(agent, seed, steps=6000, on_flip=None, on_step=None):
    env = Terrarium(seed)
    total = 0.0
    for i in range(steps):
        o = env.obs()
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        total += r
        if on_flip and info.get("regime_flip"):
            on_flip(env.t)
        if on_step:
            on_step(env.t, env, a, r, info)
        if done:
            env = Terrarium(seed + 1000 + i)  # respawn fresh world, keep agent memory
    return total, env
