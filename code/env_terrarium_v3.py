"""Terrarium v3 -- the COMPLEX environment: the full v2 world + the linger
trap embedded (owner directive msg_00098: "insert this trap into a large
complex environment and check everything together").

Everything from TerrariumV2 is kept (turn 96, RESULTS_V2.md):
  * homeostasis (energy, metabolism, death -> respawn)
  * multi-step causal chain: lever -> door open; key (cold only) + door ->
    treasure (brute-force-proof: random policy measured 0 treasures)
  * rare event: wandering fruit tree (+25 energy, reward 8)
  * regime flip at t=3000 (season forced cold, door/key reset)
  * cold-phase survival berries in the far zone

The WEATHER LINGER TRAP replaces the v2 phase decoy (turn 97, runs 2-7):
  * hidden weather calm/storm (independent of the warm/cold SEASON --
    weather is the fast process, season the slow one; both are hidden
    common causes, but only weather carries the trap)
  * STORM: the wandering tree spawns NEAR the bell (dist<=2) and the bell
    RINGS with P=0.40. CALM: ring P=0.01.
  * The bell is never affected by any action (interventional oracle in
    verify_env_v3.py). The trap: in storms the competent forager lingers
    at the tree by the bell, so eat->bell_rang correlates without causing.
  * The storm tree is the ONLY food during a storm: berries bloom only in
    calm. In the simple env the trap was optional (static energy); here it
    is LOAD-BEARING -- a forager that refuses the storm tree starves.
    This is the "everything together" the owner asked for: survival,
    planning chain, rare events, AND the trajectory confounder.

Design requirement from turn 97 (mechanism audit): the confounder needs a
COMMON CAUSE (storm = tree-at-bell + frequent ring), and the visible trace
(bell glow) must be in the agent's ctx key -- both are satisfied.

Identifier question the matrix answers: does v2.5c (stratified + RR>=2 +
door_gone data fix) reject the linger decoy inside the complex world,
while v2.1/v2.2 accept it, WITHOUT losing the true edges the planner
needs (press->lever, eat->ate, eat->tree_ate)?
"""
import random

W, H = 9, 9
ACTIONS = ["up", "down", "left", "right", "eat", "grasp", "press", "wait"]

EMPTY, BERRY, LEVER, DOOR, TREASURE, WALL = ".", "b", "L", "D", "T", "#"
BELL_GLOW, BELL_DARK = "G", "Q"
TREE, KEY = "F", "K"

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
RING_STORM, RING_CALM = 0.40, 0.01
STORM_DWELL = (40, 70)
CALM_DWELL = (120, 180)
TREE_SPAWN_MAX_DIST = 2          # storm trees spawn near the bell (the trap)
TREE_LIFE = 60
KEY_LIFE = 80
KEY_SPAWN_P = 0.02
DOOR_OPEN_WINDOW = 300
KEY_IN_HAND_WINDOW = 12
AMB_WARM, AMB_COLD, METAB = 0.3, 0.0, 0.4
BERRY_ENERGY, TREE_ENERGY = 10.0, 25.0
COLD_ZONE = [(r, c) for r in (5, 6, 7) for c in range(1, W - 1)
             if MAP[r][c] == EMPTY]


class TerrariumV3:
    def __init__(self, seed, regime_flip_at=3000):
        self.rng = random.Random(seed)
        self.seed = seed
        self.t = 0
        self.regime_flip_at = regime_flip_at
        self.energy = 60.0
        # slow hidden process: season (warm/cold) -- key spawn, ambient
        self.season = "warm"
        self.season_dwell = self.rng.randint(80, 200)
        # fast hidden process: weather (calm/storm) -- THE TRAP
        self.weather = "calm"
        self.weather_dwell = self.rng.randint(*CALM_DWELL)
        self.door_open = False
        self.has_key = False
        self.key_after_door = False      # key picked while door already open
        self.door_opened_at = None       # step at which the door last opened
        self.key_taken_at = None         # step at which the key was taken
        self.treasure_taken = 0
        self.berries_eaten = 0
        self.tree_fruits = 0
        self.keys_seen = 0
        self.lever_presses = 0
        self.storm_steps = 0
        self.pos = [3, 3]
        self.alive = True
        self.berries = set()
        self.tree = None
        self.tree_fuel = 0
        self.key = None
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
        if self.weather == "calm":
            if self.season == "warm":
                zone = [(r, c) for r in range(1, 3) for c in range(2, 5)
                        if MAP[r][c] == EMPTY and (r, c) != BELL_POS]
                target = 3
            else:
                zone = list(COLD_ZONE)
                target = 2
            if len(self.berries) < target and zone:
                free = [c for c in zone if c not in self.berries]
                if free:
                    self.berries.add(self.rng.choice(free))
        else:
            self.berries = set()      # storm: no berries anywhere

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
                    ch = BELL_GLOW if self.weather == "storm" else BELL_DARK
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
        scent = self._scent(r, c)
        return {"view": "".join(view), "energy": int(self.energy),
                "afford": tuple(sorted(afford)), "t": self.t, "scent": scent}

    def _scent(self, r, c):
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
        if self.key and tuple(self.pos) == self.key:
            self.has_key = True
            self.key = None
            self.key_fuel = 0
            self.key_after_door = self.door_open
            self.key_taken_at = self.t if self.t > 0 else 1

    def step(self, action):
        assert action in ACTIONS, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        self.t += 1
        # slow process: season
        self.season_dwell -= 1
        if self.season_dwell <= 0:
            self.season = "cold" if self.season == "warm" else "warm"
            self.season_dwell = self.rng.randint(80, 200)
        # fast process: weather (the trap's hidden common cause)
        self.weather_dwell -= 1
        if self.weather_dwell <= 0:
            if self.weather == "calm":
                self.weather = "storm"
                self.weather_dwell = self.rng.randint(*STORM_DWELL)
                # storm tree spawns NEAR the bell -- the trap geometry
                cands = [(r2, c2) for r2 in range(1, H - 1)
                         for c2 in range(1, W - 1)
                         if MAP[r2][c2] == EMPTY and (r2, c2) != BELL_POS
                         and abs(r2 - BELL_POS[0]) + abs(c2 - BELL_POS[1])
                         <= TREE_SPAWN_MAX_DIST]
                self.tree = self.rng.choice(cands)
                self.tree_fuel = max(TREE_LIFE, self.weather_dwell)
            else:
                self.weather = "calm"
                self.weather_dwell = self.rng.randint(*CALM_DWELL)
                self.tree = None
            self._maintain_berries()
        info = {}
        if self.weather == "storm":
            self.storm_steps += 1
        # the bell rings by itself: weather-driven world event, never
        # affected by any action or position (oracle-checked)
        if self.rng.random() < (RING_STORM if self.weather == "storm"
                                else RING_CALM):
            info["bell_rang"] = True
        self.energy += (AMB_WARM if self.season == "warm" else AMB_COLD) - METAB
        r, c = self.pos
        reward = 0.0
        # regime flip: mid-life the season flips to cold, world resets
        if self.t == self.regime_flip_at:
            self.season = "cold"
            self.season_dwell = self.rng.randint(80, 200)
            self.door_open = False
            self.has_key = False
            self.key_after_door = False
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
                self.energy = min(100.0, self.energy + BERRY_ENERGY)
                self.berries_eaten += 1
                reward += 1.0
                info["ate"] = True
            elif self.tree and (r, c) == self.tree:
                self.energy = min(100.0, self.energy + TREE_ENERGY)
                self.tree_fruits += 1
                reward += 8.0
                info["tree_ate"] = True
        elif action == "press":
            if MAP[r][c] == LEVER:
                if not self.door_open:
                    self.door_opened_at = self.t
                self.door_open = True
                self.lever_presses += 1
                info["lever"] = True
        elif action == "grasp":
            info["grasp"] = True      # never any world effect
        # rare events: wandering fruit tree in CALM weather (far cells) --
        # the storm tree is the trap; calm trees are ordinary rare events
        self._next_tree -= 1
        if self.tree:
            self.tree_fuel -= 1
            if self.tree_fuel <= 0:
                self.tree = None
        if self._next_tree <= 0 and self.tree is None \
                and self.weather == "calm":
            cell = self.rng.choice(self._free_cells())
            self.tree = cell
            self.tree_fuel = TREE_LIFE
            self._next_tree = self.rng.randint(200, 400)
            info["tree_appeared"] = True
        # key materialises only in the cold season
        if self.key:
            self.key_fuel -= 1
            if self.key_fuel <= 0:
                self.key = None
        if self.key is None and self.season == "cold" \
                and self.rng.random() < KEY_SPAWN_P:
            # keys never spawn near the treasure: the final leg must be a
            # real walk, not a stumble (measured: keys within 4 of the
            # treasure let a random walk finish the chain in <15 steps)
            far = [c for c in self._free_cells()
                   if abs(c[0] - 6) + abs(c[1] - 5) > 5]
            cell = self.rng.choice(far if far else self._free_cells())
            self.key = cell
            self.key_fuel = KEY_LIFE
            self.keys_seen += 1
            info["key_appeared"] = True
        # v3 gate hardening 3: the door CLOSES 300 steps after the lever
        # (a door held open forever lets a random walk luck into the whole
        # chain; measured 6/20 random lives before this). A planner that
        # wants the treasure must open the door and fetch the key within
        # the window -- a genuine two-step plan under time pressure.
        if self.door_open and self.door_opened_at is not None \
                and self.t - self.door_opened_at > DOOR_OPEN_WINDOW:
            self.door_open = False
        # v3 gate hardening 4: the key in hand CRUMBLES 120 steps after
        # pickup. Measured leak: a random walk presses the lever (t=17),
        # lucks onto a key (t=247) and stumbles to the treasure (t=274) --
        # all inside one door window, 5-6/20 random lives. With the key
        # crumbling, the agent must pick up the key and WALK STRAIGHT to
        # the treasure: a 27-step detour still fits, but the 200+ step
        # random wander does not. A planner routes directly.
        if self.has_key and self.key_taken_at is not None \
                and self.t - self.key_taken_at > KEY_IN_HAND_WINDOW:
            self.has_key = False
            self.key_after_door = False
        if not self.door_open and self.has_key:
            self.has_key = False
        # treasure: needs door open AND key in hand AND the door OPENED
        # BEFORE the key was picked up (v3 gate hardening: the v2 gate let
        # a random walk collect key+lever in any order and then stumble
        # through the open door -- measured 1 treasure / 5x6000 random
        # steps in verify_env_v3; the chain must require planning order)
        rr, cc = self.pos
        if MAP[rr][cc] == TREASURE and self.door_open and self.has_key \
                and self.treasure_taken == 0 and self.key_after_door:
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
            ("eat", "ate"): 1.0,
            ("eat", "tree_ate"): 1.0,
            ("eat", "energy"): 1.0,
            ("energy", "alive"): 1.0,
            ("grasp", "bell_rang"): 0.0,     # decoy: NOT causal
            ("eat", "bell_rang"): 0.0,        # linger decoy: NOT causal
        }

    def true_confounders(self):
        return {
            "weather->bell_rang": "storm rings 0.40, calm 0.01",
            "weather->storm_tree_near_bell": "storm tree within 2 of bell",
            "linger": "forager must eat at the storm tree -> eat ~ ring",
            "season->ambient/berries/key": "slow hidden common cause",
        }
