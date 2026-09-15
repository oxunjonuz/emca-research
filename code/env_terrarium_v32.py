"""Terrarium v3.2 -- the SEPARATED-GEOMETRY + ACTIVE-EXPERIMENT world
(turn 101 directive, op_51a5f449bf5e). Three parts in one world:

PART 1 -- geometry separation. The turn-100 paradox: the false belief
(grasp->bell_rang) PAID +8% reward because the decoy's attractor (the
chime zone) sat ON the foraging ground (the storm tree spawns within 2
of the bell -- the linger trap requires it). Owner's directive: move
the chime/attractor spawn AWAY from the fruit trees, so that
"epistemic correctness starts paying net reward" and believers "waste
energy on empty sounds far from the food".

  * The bell STAYS at (1,3) (the linger trap needs the storm tree near
    the BELL -- the tree is the foraging ground; moving the tree would
    break the trap itself).
  * A ring now drops the chime in the FAR ZONE: r >= 5 (the cold berry
    rows), >= 4 manhattan from the bell, away from the tree. The
    believer's ring goal still routes it to the bell (its false edge
    says grasping there rings the bell), but the COLLECTABLE artifact
    is now a long walk away -- and the believer's chime-scent pursuit
    drags it into the far zone during storms.
  * Empty grasps now COST energy: GRASP_COST = 0.6 per grasp with no
    effect (the directive's "waste energy on empty sounds"). Grasping
    the storm tree still pays +25 (the competence is unchanged).
  * The fury is unchanged (-2.4/step in storms). Lingering by the bell
    grasping at nothing is now pure loss: cost + fury, no food.

PART 2 -- a GRAY-ZONE TRUE EDGE (for the do-intervention task). The
owner's grey zone is 1 <= RR < 2: edges too ambiguous for the
stratified RR>=2 gate, needing an active experiment. The world now has
a genuine gray-zone CAUSE so that probing can PAY:

  * The ALTAR at (7,2). Action `wait` AT the altar cell causes a
    berry to sprout on the PATCH (7,3) with P=0.28 (vs the base
    patch-sprout rate 0.15 per step when the patch is empty). The
    patch berry is a normal berry (+10 energy, reward 1, `eat`).
    wait->patch_berry is a TRUE weak cause: RR ~ 1.87 -- in the gray
    zone by design.
  * The decoy (grasp, bell_rang) is the gray-zone FALSE edge: at the
    storm tree grasp rings at ~0.40 while others ring at ~0.37-0.40 --
    RR ~ 1.0-1.08. Both edges sit in the gray zone; only one is real.
    A prober that runs alternated trial blocks (target action vs an
    inert control) resolves both; a passive identifier cannot.
  * The altar is visible in the view (tile 'A') and has a scent
    channel ('altar'), so a planner can navigate to it.

PART 3 -- unchanged from v3.1: the chain (lever->door, key in cold,
12-step window, order gate, spawn dist>5, door window 300), rare calm
trees, survival, regime flip at 3000, wanting-refresh observables
(info['key'], treasure scent). All brute-force gates stay in force.

Ground truth:
  (grasp, bell_rang)  0.0   -- decoy, NOT causal (oracle-checked)
  (eat, bell_rang)    0.0   -- linger decoy, NOT causal
  (wait, patch_berry) 1.0   -- TRUE weak cause (RR~1.87, gray zone)
  (press, lever), (eat, ate), (grasp, tree_gather) 1.0 -- true
"""
import random

from env_terrarium_v31 import (
    TerrariumV31, STORM_FURY, CHIME_REWARD, CHIME_LIFE,
)
from env_terrarium_v3 import (
    ACTIONS, BELL_POS, EMPTY, BERRY, LEVER, TREASURE, MAP, W, H, TREE, KEY,
    STORM_DWELL, CALM_DWELL, TREE_SPAWN_MAX_DIST, TREE_LIFE,
    KEY_LIFE, KEY_SPAWN_P, DOOR_OPEN_WINDOW, KEY_IN_HAND_WINDOW,
    AMB_WARM, AMB_COLD, METAB, BERRY_ENERGY, TREE_ENERGY,
)

# ---- part 1: separated geometry ----
CHIME_FAR_MIN_ROW = 5          # chimes land only in the far zone (rows 5-7)
CHIME_FAR_MIN_DIST = 4         # and >= 4 manhattan from the bell
GRASP_COST = 0.6               # empty grasp energy cost (directive)
# ---- part 2: the altar (gray-zone true edge) ----
ALTAR_POS = (7, 2)
PATCH_POS = (7, 3)
ALTAR_TILE = "A"
PATCH_BERRY_P = 0.28           # P(berry sprouts | wait at altar, patch empty)
BASE_BERRY_P = 0.15            # P(berry sprouts | any step, patch empty)
PATCH_LIFE = 60                # a patch berry lives 60 steps then rots

# cells where chimes may land (far zone, computed once)
CHIME_FAR_CELLS = [
    (r, c) for r in range(CHIME_FAR_MIN_ROW, H - 1)
    for c in range(1, W - 1)
    if MAP[r][c] == EMPTY and (r, c) not in (ALTAR_POS, PATCH_POS)
    and abs(r - BELL_POS[0]) + abs(c - BELL_POS[1]) >= CHIME_FAR_MIN_DIST
]


class TerrariumV32(TerrariumV31):
    def __init__(self, seed, regime_flip_at=3000):
        super().__init__(seed, regime_flip_at=regime_flip_at)
        self.patch_berry = False
        self.patch_fuel = 0
        self.patch_sprouts = 0          # berries sprouted on the patch
        self.grasp_costs_paid = 0

    # ---------- view: altar tile + patch berry overlay ----------
    def obs(self):
        o = super().obs()
        r, c = self.pos
        # the patch berry is eatable: expose 'eat' in afford (v3.1's obs
        # only affords eat on bloom berries / the tree cell)
        if self.patch_berry and (r, c) == PATCH_POS \
                and "eat" not in o["afford"]:
            o["afford"] = tuple(sorted(o["afford"] + ("eat",)))
        view = list(o["view"])
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                if (rr, cc) == ALTAR_POS:
                    i = (dr + 1) * 3 + (dc + 1)
                    view[i] = ALTAR_TILE
                if (rr, cc) == PATCH_POS and self.patch_berry:
                    i = (dr + 1) * 3 + (dc + 1)
                    if view[i] in (EMPTY, BERRY):
                        view[i] = BERRY
        o["view"] = "".join(view)
        return o

    # ---------- scent: altar joins the navigable objects ----------
    def _scent(self, r, c):
        out = super()._scent(r, c)
        orow, ocol = ALTAR_POS
        d_here = abs(r - orow) + abs(c - ocol)
        out["altar"] = {
            "up": (abs(r - 1 - orow) + abs(c - ocol)) - d_here,
            "down": (abs(r + 1 - orow) + abs(c - ocol)) - d_here,
            "left": (abs(r - orow) + abs(c - 1 - ocol)) - d_here,
            "right": (abs(r - orow) + abs(c + 1 - ocol)) - d_here,
        }
        return out

    # ---------- free cells: keep altar/patch spawn-free ----------
    def _free_cells(self):
        return [cell for cell in super()._free_cells()
                if cell not in (ALTAR_POS, PATCH_POS)]

    def _maintain_berries(self):
        super()._maintain_berries()
        # the patch never hosts an ordinary bloom berry (separate channel)
        self.berries.discard(PATCH_POS)

    # ---------- step ----------
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
                cands = [(r2, c2) for r2 in range(1, H - 1)
                         for c2 in range(1, W - 1)
                         if MAP[r2][c2] == EMPTY and (r2, c2) != BELL_POS
                         and (r2, c2) not in (ALTAR_POS, PATCH_POS)
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
        # the bell rings by itself; a ring drops a chime in the FAR ZONE
        if self.rng.random() < (0.40 if self.weather == "storm"
                                else 0.01):
            info["bell_rang"] = True
            if self.chime is None and CHIME_FAR_CELLS:
                self.chime = self.rng.choice(CHIME_FAR_CELLS)
                self.chime_fuel = CHIME_LIFE
        # ambient (fury in storms, season ambient in calm)
        if self.weather == "storm":
            self.energy += STORM_FURY - METAB
        else:
            self.energy += (AMB_WARM if self.season == "warm"
                            else AMB_COLD) - METAB
        r, c = self.pos
        reward = 0.0
        # regime flip (unchanged)
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
            elif self.patch_berry and (r, c) == PATCH_POS:
                # the patch berry is a normal berry (the altar's payoff)
                self.patch_berry = False
                self.patch_fuel = 0
                self.energy = min(100.0, self.energy + BERRY_ENERGY)
                self.berries_eaten += 1
                reward += 1.0
                info["ate"] = True
                info["patch_ate"] = True
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
            self.grasp_attempts += 1
            info["grasp"] = True
            if self.tree and (r, c) != self.tree:
                d = abs(r - self.tree[0]) + abs(c - self.tree[1])
                if d <= 1:
                    self.energy = min(100.0, self.energy + TREE_ENERGY)
                    self.tree_fruits += 1
                    reward += 8.0
                    info["tree_gather"] = True
            if not info.get("tree_gather"):
                # empty grasp: costs energy (the directive's waste)
                self.energy -= GRASP_COST
                self.grasp_costs_paid += 1
        elif action == "wait":
            pass
        # chime collection (in passing, unchanged)
        if self.chime and tuple(self.pos) == self.chime:
            self.chime = None
            self.chime_fuel = 0
            self.chimes_collected += 1
            reward += CHIME_REWARD
            info["chime"] = True
        # ---- the altar: the gray-zone TRUE edge ----
        if not self.patch_berry:
            p = PATCH_BERRY_P if (action == "wait"
                                  and (r, c) == ALTAR_POS) else BASE_BERRY_P
            if self.rng.random() < p:
                self.patch_berry = True
                self.patch_fuel = PATCH_LIFE
                self.patch_sprouts += 1
                info["patch_berry"] = True
        # rare calm trees (unchanged)
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
        # key (unchanged)
        if self.key:
            self.key_fuel -= 1
            if self.key_fuel <= 0:
                self.key = None
        if self.key is None and self.season == "cold" \
                and self.rng.random() < KEY_SPAWN_P:
            far = [cell for cell in self._free_cells()
                   if abs(cell[0] - 6) + abs(cell[1] - 5) > 5]
            cell = self.rng.choice(far if far else self._free_cells())
            self.key = cell
            self.key_fuel = KEY_LIFE
            self.keys_seen += 1
            info["key_appeared"] = True
        if self.key is None and self.has_key and not info.get("key"):
            info["key"] = True
        # door window (unchanged)
        if self.door_open and self.door_opened_at is not None \
                and self.t - self.door_opened_at > DOOR_OPEN_WINDOW:
            self.door_open = False
        # key-in-hand window (unchanged: 12 steps)
        if self.has_key and self.key_taken_at is not None \
                and self.t - self.key_taken_at > KEY_IN_HAND_WINDOW:
            self.has_key = False
            self.key_after_door = False
        if not self.door_open and self.has_key:
            self.has_key = False
            self.key_after_door = False
        # treasure (unchanged gates)
        rr, cc = self.pos
        if MAP[rr][cc] == TREASURE and self.door_open and self.has_key \
                and self.treasure_taken == 0 and self.key_after_door:
            self.treasure_taken = 1
            self.has_key = False
            reward += 20.0
            info["treasure"] = True
        # chime expiry (unchanged)
        if self.chime:
            self.chime_fuel -= 1
            if self.chime_fuel <= 0:
                self.chime = None
        # patch berry rot
        if self.patch_berry:
            self.patch_fuel -= 1
            if self.patch_fuel <= 0:
                self.patch_berry = False
                self.patch_fuel = 0
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
            ("grasp", "tree_gather"): 1.0,
            ("eat", "energy"): 1.0,
            ("energy", "alive"): 1.0,
            ("wait", "patch_berry"): 1.0,      # TRUE weak cause (gray zone)
            ("grasp", "bell_rang"): 0.0,        # decoy: NOT causal
            ("eat", "bell_rang"): 0.0,          # linger decoy: NOT causal
        }

    def true_confounders(self):
        return {
            "weather->bell_rang": "storm rings 0.40, calm 0.01",
            "weather->storm_tree_near_bell": "storm tree within 2 of bell",
            "weather->chime": "a ring drops a collectable chime in the FAR zone",
            "linger": "forager must grasp at the storm tree -> grasp ~ ring",
            "fury": "storms drain 2.4/step: lingering by the bell costs energy",
            "altar_gray_zone": "wait@altar sprouts 0.28 vs base 0.15: RR~1.87",
        }
