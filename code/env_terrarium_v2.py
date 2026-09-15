"""Terrarium v2 - grid-world with an ACTIVE confounder (decoy) and rare events.

Built per TZ.md continuation rule (turn 96) and idea.md §1+§7, on top of the
validated toy design of sanity_v2_confounder.py (run 3: S7 specificity fix
rejects the decoy 3/3, keeps true edges 3/3, both variants).

Design deltas vs v1 (each tied to a failure mode measured in v1):
  * ACTIVE DECOY (world-event): hidden phase warm/cold. In warm the bell GLOWS
    (visible phase trace -> ctx key, design requirement (b)), berries bloom
    around the bell, and the bell RINGS by itself often. `grasp` at the bell
    NEVER has an effect. A reasonable policy is attracted by the glow ->
    grasp correlates with bell_rang but causes nothing. The ring is a WORLD
    event: position-independent, action-independent (design requirement (a):
    decoy must be a world-event, not a view-effect).
  * RARE EVENT REQUIRING EXPLORATION: a wandering FRUIT TREE (tile F) that
    appears ~every 300 steps at a random free cell for 60 steps; eating from
    it gives +25 energy and reward 8 (vs berry +10 / reward 1). It is never
    visible until you are near it (3x3 view) -> found only by exploration.
  * BRUTE-FORCE-PROOF TREASURE: the vault door needs the lever AND a KEY. The
    key (tile K) materialises ONLY during COLD phase at a random cell, lives
    80 steps, and must be picked up by WALKING onto it (no action needed).
    Random policy over 6000 steps: expected key-intercepts ~0 (see
    verify_env_v2.py measurement) -> E3 separates planning from luck.
  * Homeostasis, regime flip, respawn-on-death (fresh world, agent memory
    kept) as in v1.
"""
import random

W, H = 9, 9
ACTIONS = ["up", "down", "left", "right", "eat", "grasp", "press", "wait"]

EMPTY, BERRY, LEVER, DOOR, TREASURE, WALL = ".", "b", "L", "D", "T", "#"
BELL_GLOW, BELL_DARK = "G", "Q"      # visible phase trace (design req. (b))
TREE, KEY = "F", "K"                 # rare event / brute-force gate

MAP = [
    "#########",
    "#..Q....#",
    "#.......#",
    "#.......#",
    "#...L...#",
    "#...##..#",
    "#...DT..#",
    "#...##..#",
    "#########",
]
BELL_POS = (1, 3)
RING_WARM, RING_COLD = 0.75, 0.03
AMB_WARM, AMB_COLD, METAB = 0.3, -0.2, 0.5
TREE_EVERY, TREE_LIFE = 300, 60
KEY_LIFE = 80
# cold-phase survival berries: far zone (rows 5-7), away from the bell
COLD_ZONE = [(r, c) for r in (5, 6, 7) for c in range(1, W - 1)
             if MAP[r][c] == EMPTY]


class TerrariumV2:
    def __init__(self, seed, regime_flip_at=3000):
        self.rng = random.Random(seed)
        self.seed = seed
        self.t = 0
        self.regime_flip_at = regime_flip_at
        self.energy = 60.0
        self.phase = "warm"
        self.dwell = self.rng.randint(80, 200)
        self.door_open = False
        self.has_key = False
        self.treasure_taken = 0
        self.berries_eaten = 0
        self.tree_fruits = 0
        self.keys_seen = 0
        self.lever_presses = 0
        self.pos = [3, 3]
        self.alive = True
        self.berries = set()
        self.tree = None            # (r, c) or None
        self.tree_fuel = 0          # remaining tree steps
        self.key = None             # (r, c) or None
        self.key_fuel = 0
        self._next_tree = self.rng.randint(150, 300)
        self._maintain_berries()

    # ---------- helpers ----------
    def _free_cells(self):
        out = []
        for r in range(1, H - 1):
            for c in range(1, W - 1):
                ch = MAP[r][c]
                if ch == EMPTY and (r, c) != BELL_POS:
                    out.append((r, c))
        return out

    def _maintain_berries(self):
        if self.phase == "warm":
            # confounder footprint: berries bloom around the bell (KEYED)
            zone = [(r, c) for r in range(1, 3) for c in range(2, 5)
                    if MAP[r][c] == EMPTY and (r, c) != BELL_POS]
            if len(self.berries) < 3 and zone:
                free = [c for c in zone if c not in self.berries]
                if free:
                    self.berries.add(self.rng.choice(free))
        else:
            # cold-phase survival berries: far zone (rows 5-7), away from the
            # bell -- cold must be survivable, just leaner (2 berries, no bloom
            # at the bell). v2 fix after V5 FAIL: without these the agent
            # starved in every cold phase.
            self.berries = {c for c in self.berries if c in COLD_ZONE}
            if len(self.berries) < 2:
                free = [c for c in COLD_ZONE if c not in self.berries]
                if free:
                    self.berries.add(self.rng.choice(free))

    def obs(self):
        r, c = self.pos
        view = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    view.append(WALL)
                    continue
                ch = MAP[rr][cc]
                if (rr, cc) == BELL_POS:
                    ch = BELL_GLOW if self.phase == "warm" else BELL_DARK
                if ch == EMPTY and (rr, cc) in self.berries:
                    ch = BERRY
                if self.tree and (rr, cc) == self.tree:
                    ch = TREE
                if self.key and (rr, cc) == self.key:
                    ch = KEY
                if ch == DOOR and self.door_open:
                    ch = EMPTY
                view.append(ch)
        afford = []
        if (r, c) in self.berries:
            afford.append("eat")
        if self.tree and (r, c) == self.tree:
            afford.append("eat")
        if MAP[r][c] == LEVER:
            afford.append("press")
        afford.append("grasp")
        # long-range scent (4-neighbour gradient): the only way a 3x3-view
        # agent can navigate to rare events without a map. Same signal for
        # every agent (no privileged access).
        scent = self._scent(r, c)
        return {
            "view": "".join(view),
            "energy": int(self.energy),
            "afford": tuple(sorted(afford)),
            "t": self.t,
            "scent": scent,
        }

    def _scent(self, r, c):
        """Manhattan-distance gradient to tree/key (if present), else None.
        4-neighbour: (up, down, left, right) deltas, positive = closer that way."""
        out = {}
        for name, obj in (("tree", self.tree), ("key", self.key)):
            if obj is None:
                continue
            orow, ocol = obj
            d_here = abs(r - orow) + abs(c - ocol)
            out[name] = {
                "up": (abs(r - 1 - orow) + abs(c - ocol)) - d_here,
                "down": (abs(r + 1 - orow) + abs(c - ocol)) - d_here,
                "left": (abs(r - orow) + abs(c - 1 - ocol)) - d_here,
                "right": (abs(r - orow) + abs(c + 1 - ocol)) - d_here,
            }
        return out

    def _move(self, nr, nc):
        if not (0 <= nr < H and 0 <= nc < W):
            return
        ch = MAP[nr][nc]
        if ch == WALL:
            return
        if ch == DOOR and not self.door_open:
            return
        self.pos = [nr, nc]
        # key pickup: automatic on walking onto the key cell
        if self.key and tuple(self.pos) == self.key:
            self.has_key = True
            self.key = None
            self.key_fuel = 0

    def step(self, action):
        assert action in ACTIONS, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        self.t += 1
        # phase dynamics (hidden confounder)
        self.dwell -= 1
        if self.dwell <= 0:
            self.phase = "cold" if self.phase == "warm" else "warm"
            self.dwell = self.rng.randint(80, 200)
            self._maintain_berries()
        info = {}
        # world event: the bell rings by itself (phase-driven, action/position
        # independent -- decoy design requirement (a))
        if self.rng.random() < (RING_WARM if self.phase == "warm" else RING_COLD):
            info["bell_rang"] = True
        self.energy += (AMB_WARM if self.phase == "warm" else AMB_COLD) - METAB
        r, c = self.pos
        reward = 0.0
        # regime flip: mid-life the world changes (season flips to cold, world
        # resets its levers/door)
        if self.t == self.regime_flip_at:
            self.phase = "cold"
            self.dwell = self.rng.randint(80, 200)
            self.door_open = False
            self.has_key = False
            self._maintain_berries()
            info["regime_flip"] = True
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
                self.energy = min(100.0, self.energy + 10.0)
                self.berries_eaten += 1
                reward += 1.0
                info["ate"] = True
            elif self.tree and (r, c) == self.tree:
                self.energy = min(100.0, self.energy + 25.0)
                self.tree_fruits += 1
                reward += 8.0
                info["tree_ate"] = True
        elif action == "press":
            if MAP[r][c] == LEVER:
                self.door_open = True
                self.lever_presses += 1
                info["lever"] = True
        elif action == "grasp":
            info["grasp"] = True      # never any world effect (decoy)
        elif action == "wait":
            pass
        # rare events: wandering fruit tree
        self._next_tree -= 1
        if self.tree:
            self.tree_fuel -= 1
            if self.tree_fuel <= 0:
                self.tree = None
        if self._next_tree <= 0 and self.tree is None:
            cell = self.rng.choice(self._free_cells())
            self.tree = cell
            self.tree_fuel = TREE_LIFE
            self._next_tree = self.rng.randint(TREE_EVERY - 100, TREE_EVERY + 100)
            info["tree_appeared"] = True
        # key materialises only in cold phase
        if self.key:
            self.key_fuel -= 1
            if self.key_fuel <= 0:
                self.key = None
        if self.key is None and self.phase == "cold" and self.rng.random() < 0.02:
            cell = self.rng.choice(self._free_cells())
            self.key = cell
            self.key_fuel = KEY_LIFE
            self.keys_seen += 1
            info["key_appeared"] = True
        # treasure: needs door open AND key in hand
        rr, cc = self.pos
        if MAP[rr][cc] == TREASURE and self.door_open and self.has_key \
                and self.treasure_taken == 0:
            self.treasure_taken = 1
            self.has_key = False
            reward += 20.0
            info["treasure"] = True
        # death
        if self.energy <= 0:
            self.alive = False
            reward -= 5.0
            info["died"] = True
        self._maintain_berries()
        return self.obs(), reward, not self.alive, info

    # ---------- ground truth ----------
    def true_causal_edges(self):
        return {
            ("press", "lever"): 1.0,
            ("lever", "door_open"): 1.0,
            ("door_open+key", "treasure"): 1.0,
            ("eat", "energy"): 1.0,
            ("energy", "alive"): 1.0,
            ("grasp", "bell_rang"): 0.0,     # the decoy: NOT causal
        }

    def true_confounders(self):
        return {
            "phase->glow": "visible trace (ctx key)",
            "phase->bell_rang": "world event, action-independent",
            "phase->berries_around_bell": "confounder footprint KEYED at bell",
            "grasp": "attracted by glow, causes nothing",
        }


def run_episode(agent, seed, steps=6000, regime_flip_at=3000, on_step=None):
    env = TerrariumV2(seed, regime_flip_at=regime_flip_at)
    total = 0.0
    for i in range(steps):
        o = env.obs()
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        total += r
        if on_step:
            on_step(env.t, env, a, r, info)
        if done:
            env = TerrariumV2(seed + 1000 + i, regime_flip_at=regime_flip_at)
    return total, env
