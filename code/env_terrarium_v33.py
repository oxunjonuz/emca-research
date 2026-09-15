"""Terrarium v3.3 -- the SCARCITY + DYNAMIC-COST world (turn 102,
op_6181258f9eae). Directive task 1: "make the price of empty grasps
and the cost of experiments (Prober) more DYNAMIC, to test the
agents' stability under a HARD ENERGY DEFICIT."

TerrariumV32 kept whole (separated geometry, altar gray edge, chain,
linger trap). Three deltas, each tied to a measured number of the
turn-101 matrix:

DELTA 1 -- DYNAMIC GRASP COST (the empty grasp's price is state-dependent).
  v3.2: GRASP_COST = 0.6 flat. Measured: curious_surv paid 85.8 energy
  in grasp costs and still won by +82% -- the flat tax did not bind.
  v3.3: the empty grasp costs 0.6 in calm, but 1.8 in a STORM
  (GRASP_COST_STORM = 3x): the fury already drains 2.4/step, and a
  wasted grasp in a storm is a triple mistake (wrong place, wrong time,
  no food). The competent grasp (tree at dist<=1) still pays +18.
  The believer's false edge (grasp, bell_rang) routes grasps to the
  bell zone -- where the storm tree lives by trap design -- so the
  DYNAMIC cost discriminates: grasping at the bell WITH the tree in
  reach is competence; grasping at the bell with NO tree in reach is
  the exact behaviour the false edge motivates, and it now costs 1.8.

DELTA 2 -- PROBE COSTS (the experiment's price is state-dependent).
  v3.2: probe trials were free (wait at the altar costs only time).
  Measured: the prober paid ~33% reward for its experiments -- but all
  of that was opportunity cost (storm-foraging time), not a direct fee.
  v3.3: the altar DEMANDS an offering: each `wait` AT the altar costs
  WAIT_ALTAR_COST = 1.0 energy (the offering burns). The gray-zone true
  edge (wait -> patch_berry) still pays: berry +10 energy / reward 1,
  sprout P=0.28 per wait. Expected energy value per wait: 0.28*10 - 1.0
  = +1.8; reward-wise 0.28*1 = 0.28 per wait vs 0 before.
  The experiment is no longer free: a prober that runs 180+180 trials
  pays 360*1.0 = 360 energy in offerings -- it must EARN its data.
  The passive arms that never wait at the altar pay nothing (and never
  see the edge). The offering also prices the decoy probe's control
  arm -- both arms of a probe pay, so the alternation stays fair.

DELTA 3 -- HARD DEFICIT (the world's food budget shrinks).
  v3.2: berries bloom to 3 (warm) / 2 (cold) per maintain; storm tree
  +25 per fruit, unlimited; BERRY_ENERGY 10; fury -2.4.
  v3.3: the budget is cut hard, on three axes at once:
    * BERRY_TARGET_WARM 3 -> 2, BERRY_TARGET_COLD 2 -> 1
      (the far-zone rows that paid the rejector's chime walks shrink)
    * TREE_ENERGY 25 -> 18, and the storm tree's fruit is capped:
      MAX_STORM_FRUITS = 60 per storm (then the tree is bare -- the
      curious arm's 4683 fruits came from camping the tree; scarcity
      must not be survivable by camping ONE resource)
    * STORM_FURY -2.4 -> -3.0 (the fury deepens)
  Energy math (deficit check, preregistered): calm warm net 0.3-0.4 =
  -0.1/step; a warm phase of 150 steps drains ~15 energy -- 2 berries
  on the map (+10 each) do not cover it without the rare trees; storms
  drain 3.0+0.4 = 3.4/step bare, +18 per fruit, capped 60 fruits.
  The competent forager survives by WORK; nobody survives by luck.

Identifier question unchanged (the trap is untouched); the NEW
questions this env answers:
  Q1 (task 1): under the dynamic grasp cost + hard deficit, does the
      believer (v2.1) now LOSE to the rejector (v2.5c) -- and does the
      curious_surv dominance survive scarcity?
  Q2 (task 2): does the prober still reach verdicts when every trial
      costs an offering -- and does the verdict still pay (patch
      berries) against the deficit?
  Q3 (task 3): can the curious agent solve the CHAIN (lever->key->
      door->treasure) without a goal planner? (agent-side; see
      agent_emca_v33.py: object-directed novelty + chain affordances)

Ground truth: (grasp, bell_rang) NOT causal; (eat, bell_rang) NOT
causal; (wait, patch_berry) TRUE weak cause (RR~1.9); press->lever,
eat->ate, grasp->tree_gather true. The altar's offering does NOT
change the edge's causality (the sprout channel is untouched).
"""
import random

from env_terrarium_v32 import (
    TerrariumV32, ALTAR_POS, PATCH_POS, PATCH_BERRY_P, BASE_BERRY_P,
    PATCH_LIFE, CHIME_FAR_CELLS,
)
from env_terrarium_v3 import (
    ACTIONS, BELL_POS, EMPTY, BERRY, LEVER, TREASURE, MAP, W, H, TREE,
    KEY, STORM_DWELL, CALM_DWELL, TREE_SPAWN_MAX_DIST, TREE_LIFE,
    KEY_LIFE, KEY_SPAWN_P, DOOR_OPEN_WINDOW, KEY_IN_HAND_WINDOW,
    AMB_WARM, AMB_COLD, METAB, BERRY_ENERGY, COLD_ZONE,
)

# ---- delta 1: dynamic grasp cost ----
GRASP_COST_CALM = 0.6            # unchanged from v3.2
GRASP_COST_STORM = 1.8           # 3x in a storm (the dynamic price)
# ---- delta 2: probe cost ----
WAIT_ALTAR_COST = 1.0            # each wait at the altar burns an offering
# ---- delta 3: hard deficit ----
STORM_FURY_V33 = -3.0            # was -2.4
TREE_ENERGY_V33 = 18.0           # was 25
BERRY_TARGET_WARM = 2            # was 3
BERRY_TARGET_COLD = 1            # was 2
MAX_STORM_FRUITS = 60            # the storm tree goes bare


class TerrariumV33(TerrariumV32):
    def __init__(self, seed, regime_flip_at=3000):
        super().__init__(seed, regime_flip_at=regime_flip_at)
        self.storm_fruits_this_storm = 0
        self.offerings_paid = 0
        self.waits_at_altar = 0
        self.bare_tree_events = 0

    # ---------- delta 3: the shrunken berry budget ----------
    def _maintain_berries(self):
        if self.weather == "calm":
            if self.season == "warm":
                zone = [(r, c) for r in range(1, 3) for c in range(2, 5)
                        if MAP[r][c] == EMPTY and (r, c) != BELL_POS]
                target = BERRY_TARGET_WARM
            else:
                zone = list(COLD_ZONE)
                target = BERRY_TARGET_COLD
            if len(self.berries) < target and zone:
                free = [c for c in zone if c not in self.berries]
                if free:
                    self.berries.add(self.rng.choice(free))
        else:
            self.berries = set()      # storm: no berries anywhere

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
                self.storm_fruits_this_storm = 0        # delta 3: cap reset
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
                self.chime_fuel = 40
        # ambient: the DEEPENED fury (delta 3)
        if self.weather == "storm":
            self.energy += STORM_FURY_V33 - METAB
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
                self.patch_berry = False
                self.patch_fuel = 0
                self.energy = min(100.0, self.energy + BERRY_ENERGY)
                self.berries_eaten += 1
                reward += 1.0
                info["ate"] = True
                info["patch_ate"] = True
            elif self.tree and (r, c) == self.tree:
                # delta 3: the tree's fruit is leaner (18, was 25)
                self.energy = min(100.0, self.energy + TREE_ENERGY_V33)
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
                if d <= 1 and self.storm_fruits_this_storm < MAX_STORM_FRUITS:
                    self.energy = min(100.0, self.energy + TREE_ENERGY_V33)
                    self.tree_fruits += 1
                    self.storm_fruits_this_storm += 1
                    reward += 8.0
                    info["tree_gather"] = True
                elif d <= 1 and self.storm_fruits_this_storm >= MAX_STORM_FRUITS:
                    # delta 3: the tree is BARE -- the grasp is empty
                    info["tree_bare"] = True
            if not info.get("tree_gather"):
                # delta 1: DYNAMIC empty-grasp cost (storm costs 3x)
                cost = (GRASP_COST_STORM if self.weather == "storm"
                        else GRASP_COST_CALM)
                self.energy -= cost
                self.grasp_costs_paid += cost
        elif action == "wait":
            # delta 2: the altar demands an offering for each wait
            if (r, c) == ALTAR_POS:
                self.energy -= WAIT_ALTAR_COST
                self.offerings_paid += 1
                self.waits_at_altar += 1
                info["offering"] = True
        # chime collection (in passing, unchanged)
        if self.chime and tuple(self.pos) == self.chime:
            self.chime = None
            self.chime_fuel = 0
            self.chimes_collected += 1
            reward += 0.5
            info["chime"] = True
        # ---- the altar: the gray-zone TRUE edge (rates unchanged) ----
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
        # patch berry rot (unchanged)
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
            "fury": "storms drain 3.0/step: lingering by the bell costs energy",
            "altar_gray_zone": "wait@altar sprouts 0.28 vs base 0.15: RR~1.87",
            "dynamic_grasp_cost": "empty grasp: 0.6 calm / 1.8 storm",
            "altar_offering": "each wait@altar burns 1.0 energy",
            "scarcity": "berries 2/1, tree 18 capped 60/storm, fury -3.0",
        }
