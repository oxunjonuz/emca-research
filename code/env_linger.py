"""TerrariumLinger -- the SIMPLE environment: only the linger trap.

Owner directive (msg_00098 / op_94de348cf9ed): "make a simple new
environment with only this trap and check whether the new way of thinking
helps. Then immediately embed the trap into a large complex environment
and check everything together."

This is the simple half. Design = the validated linger form of TZ.md
direction 1 (runs 2-7 of turn 97, SANITY_TRAJECTORY_CONFOUNDER.md):
  * ONE hidden common cause: weather calm/storm.
  * In storm: a fruit tree spawns NEAR the bell (dist<=2) with MANY fruits
    (eat repeatedly, reward 8 each), and the bell rings with P=0.40.
  * In calm: berries bloom in the far shelter zone, ring P=0.01.
  * The bell is NEVER affected by any action (interventional oracle in
    verify_env_linger.py). The trap: a competent forager LINGERS at the
    storm tree next to the bell, so eat->bell_rang correlates without
    causing.
  * Energy is STATIC (80), exactly as in the validated toy LingerEnv:
    the toy check of THIS file's first draft (with survival pressure)
    measured that metabolism starves the agent before the goal scheduler
    ever issues the tree goal (fruits 0-1, deaths 3-4 per 6000 steps,
    decoy data absent) -- survival pressure breaks trap delivery, and the
    simple env's question is the IDENTIFIER, not survival. The complex
    env (env_terrarium_v3.py) keeps full survival, where the trap is
    load-bearing: the storm tree is the only storm food.
  * NO lever/key/door/treasure chain, NO regime flip, NO context reset:
    one question only -- does the stratified identifier v2.5c reject the
    linger decoy that defeats the pooled contrasts v2.1/v2.2, without
    breaking the true edges (eat->ate, eat->tree_ate)?
  * Lives are 16000 steps (not 6000): the agent's goal menu demotes the
    unachievable kinds (explore/key/treasure) only after ~6000 steps, so
    the tree goal / default-act foraging engages in the second half of a
    16k life (measured in the toy runs: 1105-1208 fruits per 16k).

Identical interface to Terrarium/TerrariumV2: obs()/step() with the same
action set, view format, scent convention, info flags. The agent files
are reused WITHOUT modification.
"""
import random

W, H = 9, 9
ACTIONS = ["up", "down", "left", "right", "eat", "grasp", "press", "wait"]

EMPTY, BERRY, LEVER, DOOR, TREASURE, WALL = ".", "b", "L", "D", "T", "#"
BELL_GLOW, BELL_DARK = "G", "Q"      # visible weather trace (ctx key req.)
TREE, KEY = "F", "K"

MAP = [
    "#########",
    "#..Q....#",
    "#.......#",
    "#.......#",
    "#.......#",
    "#.......#",
    "#.......#",
    "#.......#",
    "#########",
]
BELL_POS = (1, 3)
RING_STORM, RING_CALM = 0.40, 0.01
STORM_DWELL = (60, 100)
CALM_DWELL = (200, 300)
TREE_SPAWN_MAX_DIST = 2                 # tree spawns near the bell (the trap)
# far zone (rows 5-7): calm berries bloom here, away from the bell
SHELTER = [(r, c) for r in range(5, 8) for c in range(1, W - 1)
           if MAP[r][c] == EMPTY]


class TerrariumLinger:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.seed = seed
        self.t = 0
        self.pos = [4, 4]
        self.alive = True                   # static energy: no death
        self.phase = "calm"
        self.dwell = self.rng.randint(*CALM_DWELL)
        self.tree = None
        self.tree_fuel = 0
        self.berries = set()
        self.tree_eaten = 0
        self.berries_eaten = 0
        self.deaths = 0
        self.storm_steps = 0
        self._maintain_berries()

    # ---------- helpers ----------
    def _maintain_berries(self):
        if self.phase == "calm":
            if len(self.berries) < 3:
                free = [c for c in SHELTER if c not in self.berries]
                if free:
                    self.berries.add(self.rng.choice(free))
        else:
            self.berries = set()          # storm: no calm berries

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
                    ch = BELL_GLOW if self.phase == "storm" else BELL_DARK
                if ch == EMPTY and (rr, cc) in self.berries:
                    ch = BERRY
                if self.tree and (rr, cc) == self.tree:
                    ch = TREE
                view.append(ch)
        afford = ["grasp", "wait"]
        if (r, c) in self.berries or (self.tree and (r, c) == self.tree):
            afford.append("eat")
        scent = {}
        if self.tree is not None:
            orow, ocol = self.tree
            d = abs(r - orow) + abs(c - ocol)
            scent["tree"] = {
                "up": (abs(r - 1 - orow) + abs(c - ocol)) - d,
                "down": (abs(r + 1 - orow) + abs(c - ocol)) - d,
                "left": (abs(r - orow) + abs(c - 1 - ocol)) - d,
                "right": (abs(r - orow) + abs(c + 1 - ocol)) - d,
            }
        return {"view": "".join(view), "energy": 80,
                "afford": tuple(sorted(afford)), "t": self.t, "scent": scent}

    def step(self, action):
        assert action in ACTIONS, action
        self.t += 1
        self.dwell -= 1
        if self.dwell <= 0:
            if self.phase == "calm":
                self.phase = "storm"
                self.dwell = self.rng.randint(*STORM_DWELL)
                cands = [(r2, c2) for r2 in range(1, H - 1)
                         for c2 in range(1, W - 1)
                         if MAP[r2][c2] == EMPTY and (r2, c2) != BELL_POS
                         and abs(r2 - BELL_POS[0]) + abs(c2 - BELL_POS[1])
                         <= TREE_SPAWN_MAX_DIST]
                self.tree = self.rng.choice(cands)
                self.tree_fuel = self.dwell
            else:
                self.phase = "calm"
                self.dwell = self.rng.randint(*CALM_DWELL)
                self.tree = None
            self._maintain_berries()
        info = {}
        if self.phase == "storm":
            self.storm_steps += 1
        # the bell rings by itself: weather-driven world event, never
        # affected by any action or position (oracle-checked)
        if self.rng.random() < (RING_STORM if self.phase == "storm"
                                else RING_CALM):
            info["bell_rang"] = True
        r, c = self.pos
        reward = 0.0
        if action in ("up", "down", "left", "right"):
            dr, dc = {"up": (-1, 0), "down": (1, 0),
                      "left": (0, -1), "right": (0, 1)}[action]
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and MAP[nr][nc] != WALL:
                self.pos = [nr, nc]
        elif action == "eat":
            if self.tree and (r, c) == self.tree:
                self.tree_eaten += 1          # tree does not vanish: LINGER
                reward += 8.0
                info["tree_ate"] = True
            elif (r, c) in self.berries:
                self.berries.discard((r, c))
                self.berries_eaten += 1
                reward += 1.0
                info["ate"] = True
        elif action == "press":
            info["press_nothing"] = True      # no lever anywhere
        elif action == "grasp":
            info["grasp"] = True              # never any world effect
        if self.tree:
            self.tree_fuel -= 1
            if self.tree_fuel <= 0:
                self.phase = "calm"
                self.dwell = self.rng.randint(*CALM_DWELL)
                self.tree = None
                self._maintain_berries()
        self._maintain_berries()
        return self.obs(), reward, False, info

    # ---------- ground truth ----------
    def true_causal_edges(self):
        return {
            ("eat", "ate"): 1.0,
            ("eat", "tree_ate"): 1.0,
            ("grasp", "bell_rang"): 0.0,     # the decoy: NOT causal
            ("eat", "bell_rang"): 0.0,        # the linger decoy: NOT causal
            ("press", "lever"): 0.0,          # no lever in this world
        }

    def true_confounders(self):
        return {
            "weather->bell_rang": "storm rings 0.40, calm 0.01",
            "weather->tree_near_bell": "tree spawns within 2 of the bell",
            "linger": "forager stays at the storm tree -> eat co-occurs with ring",
        }
