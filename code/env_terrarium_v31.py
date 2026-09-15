"""Terrarium v3.1 -- the ACTIONABLE-DECOY environment (turn 100 directive,
op_39d83261dc8e): "create a world where the decoy becomes an attractor or
carries a cost, so that agents with different identifiers start to differ
BEHAVIOURALLY" + "unlock the full chain (Treasures > 0)".

Everything in TerrariumV3 (turn 99) is kept: weather linger trap, chain
(lever->door, key in cold, treasure), rare calm trees, survival, regime
flip. Three deltas, each tied to a measured defect of the turn-99 matrix:

DELTA 1 -- the decoy moves from `eat` to `grasp` (the actionable form).
  In v3 the storm tree is eaten with `eat` -- a UNIVERSAL action that
  every identifier-armed agent performs identically, so the false edge
  never fed a goal and all arms were behaviourally identical (RESULTS_
  LINGER_V3.md honest negative #2). In v3.1 the storm tree's fruit hangs
  HIGH: it is gathered with `grasp` at the tree cell. `grasp` is NOT
  universal (it is a chosen action), so the false edge (grasp, bell_rang)
  is exactly the kind of edge the planner can act on: an agent that
  BELIEVES grasp->bell_rang has a reason to grasp at the bell; an agent
  that knows better has none. The linger structure is identical to v3
  (storm tree near the bell, ring 0.40 vs 0.01, oracle-checked).
  The tree still yields +25 energy / reward 8 per fruit (survival is
  load-bearing in storms -- unchanged).

DELTA 2 -- the ring is COLLECTABLE and the bell is an attractor with a
  cost. When the bell rings, a chime lands on a cell within dist<=2 of
  the bell; walking onto the chime collects it (+0.5 reward). The chime
  is a pure weather artifact: it appears ONLY because the bell rang, and
  the bell rings by itself. So an agent whose goal machinery treats
  bell_rang as a valuable effect (the ring goal) will spend its storms
  by the bell collecting chimes -- while the storm rages: during a storm
  the ambient temperature drops (STORM_FURY = -2.0/step instead of the
  season ambient). Lingering at the bell in a storm is therefore
  SURVIVABLE but EXPENSIVE: the storm tree (+25/fruit) is the only food
  that pays for the fury. This makes the decoy an attractor (chimes) AND
  a cost (fury) at once -- the two forms the owner named.

DELTA 3 -- the chain is completable again (measured defects of turn 99):
  (a) the env now reports info["key"]=True when the key is picked up
      (v3 never emitted it: the key goal was unsatisfiable, expired 3x
      and was demoted forever -- self_model['key']=[0,3] in every seed);
  (b) the scent channel carries 'treasure' whenever the agent holds the
      key and the door is open (the final leg needs navigation; in v3
      the agent wandered off with the key and the 12-step window died);
  (c) the scent channel carries 'bell' while a chime is on the ground.
  The gate parameters (order gate, 12-step in-hand window, spawn dist>5,
  300-step door window) are UNCHANGED from v3 -- the brute-force gates
  measured 0/80 leaks stay in force. If the planner still cannot finish
  the chain, the window is re-measured (not guessed) before any change.

Identifier question this env answers: do agents that REJECT the decoy
(v2.5c) and agents that ACCEPT it (v2.1, v2.2, assoc-only) now BEHAVE
differently -- and does knowing the truth pay (reward, survival, or
chain completion) where believing the decoy costs?

Ground truth: (grasp, bell_rang) is NOT causal (oracle-checked); the
chime is a weather artifact; press->lever, eat->ate, grasp->tree_gather
are causal.
"""
import random

from env_terrarium_v3 import (
    TerrariumV3, ACTIONS, BELL_POS, EMPTY, TREE, KEY, BERRY, WALL, MAP,
    W, H, LEVER, DOOR, TREASURE, BELL_GLOW, BELL_DARK,
    RING_STORM, RING_CALM, STORM_DWELL, CALM_DWELL, TREE_SPAWN_MAX_DIST,
    TREE_LIFE, KEY_LIFE, KEY_SPAWN_P, DOOR_OPEN_WINDOW, KEY_IN_HAND_WINDOW,
    AMB_WARM, AMB_COLD, METAB, BERRY_ENERGY, TREE_ENERGY, COLD_ZONE,
)

STORM_FURY = -2.0          # ambient during a storm (replaces season ambient)
CHIME_REWARD = 0.5
CHIME_MAX_DIST = 2         # chimes land within 2 of the bell
CHIME_LIFE = 40


class TerrariumV31(TerrariumV3):
    def __init__(self, seed, regime_flip_at=3000):
        super().__init__(seed, regime_flip_at=regime_flip_at)
        self.chime = None          # (r, c) or None
        self.chime_fuel = 0
        self.chimes_collected = 0
        self.tree_fruits = 0       # grasp-gathered fruits (was eat-gathered)
        self.grasp_attempts = 0

    # ---------- overrides ----------
    def _scent(self, r, c):
        """v3.1: scent carries tree/key (as in v3) PLUS 'treasure' when the
        agent holds the key with the door open (chain completion needs a
        navigation channel) and 'bell' while a chime is on the ground."""
        out = super()._scent(r, c)
        for name, obj in (("treasure", (6, 5) if (self.has_key and
                                                  self.door_open) else None),
                          ("bell", self.chime)):
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

    def obs(self):
        o = super().obs()
        # chime tile overlays an EMPTY cell in the view
        if self.chime:
            r, c = self.pos
            view = list(o["view"])
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if (rr, cc) == self.chime:
                        i = (dr + 1) * 3 + (dc + 1)
                        if view[i] in (EMPTY, BERRY):
                            view[i] = "C"
            o["view"] = "".join(view)
        return o

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
        # the bell rings by itself; in v3.1 a ring DROPS A CHIME near the
        # bell (the collectable artifact: it exists only because the bell
        # rang, and the bell rings by weather alone)
        if self.rng.random() < (RING_STORM if self.weather == "storm"
                                else RING_CALM):
            info["bell_rang"] = True
            if self.chime is None:
                cands = [(r2, c2) for r2 in range(1, H - 1)
                         for c2 in range(1, W - 1)
                         if MAP[r2][c2] == EMPTY and (r2, c2) != BELL_POS
                         and (r2, c2) != self.tree
                         and abs(r2 - BELL_POS[0]) + abs(c2 - BELL_POS[1])
                         <= CHIME_MAX_DIST]
                if cands:
                    self.chime = self.rng.choice(cands)
                    self.chime_fuel = CHIME_LIFE
        # ambient: storms are FURIOUS (the cost of lingering by the bell);
        # calm keeps the season ambient as in v3
        if self.weather == "storm":
            self.energy += STORM_FURY - METAB
        else:
            self.energy += (AMB_WARM if self.season == "warm"
                            else AMB_COLD) - METAB
        r, c = self.pos
        reward = 0.0
        # regime flip (unchanged from v3)
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
            # v3.1 DELTA 1: the storm tree's fruit hangs high -- gathered
            # with grasp from ADJACENT (dist<=1), not eat. Same +25 energy
            # / reward 8 as v3's fruit. (First draft required standing ON
            # the cell; the toy trace measured the agent starving next to
            # a visible tree -- the competence fix is standing NEAR it.)
            if self.tree and (r, c) != self.tree:
                d = abs(r - self.tree[0]) + abs(c - self.tree[1])
                if d <= 1:
                    self.energy = min(100.0, self.energy + TREE_ENERGY)
                    self.tree_fruits += 1
                    reward += 8.0
                    info["tree_gather"] = True
        # chime collection: walking onto the chime cell (a move, not an
        # action -- the chime is picked up in passing, like the key)
        if self.chime and tuple(self.pos) == self.chime:
            self.chime = None
            self.chime_fuel = 0
            self.chimes_collected += 1
            reward += CHIME_REWARD
            info["chime"] = True
        # rare calm trees (unchanged: ordinary rare events, eaten with eat)
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
        # key (unchanged from v3) -- but now REPORTED on pickup (delta 3a)
        if self.key:
            self.key_fuel -= 1
            if self.key_fuel <= 0:
                self.key = None
        if self.key is None and self.season == "cold" \
                and self.rng.random() < KEY_SPAWN_P:
            far = [c for c in self._free_cells()
                   if abs(c[0] - 6) + abs(c[1] - 5) > 5]
            cell = self.rng.choice(far if far else self._free_cells())
            self.key = cell
            self.key_fuel = KEY_LIFE
            self.keys_seen += 1
            info["key_appeared"] = True
        if self.key is None and self.has_key and not info.get("key"):
            info["key"] = True          # v3.1: key pickup is an observable
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
        # chime expiry
        if self.chime:
            self.chime_fuel -= 1
            if self.chime_fuel <= 0:
                self.chime = None
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
            ("grasp", "tree_gather"): 1.0,      # v3.1: fruit is grasped
            ("eat", "energy"): 1.0,
            ("energy", "alive"): 1.0,
            ("grasp", "bell_rang"): 0.0,         # decoy: NOT causal
            ("eat", "bell_rang"): 0.0,           # linger decoy: NOT causal
        }

    def true_confounders(self):
        return {
            "weather->bell_rang": "storm rings 0.40, calm 0.01",
            "weather->storm_tree_near_bell": "storm tree within 2 of bell",
            "weather->chime": "a ring drops a collectable chime near the bell",
            "linger": "forager must grasp at the storm tree -> grasp ~ ring",
            "fury": "storms drain 2.4/step: lingering by the bell costs energy",
        }
