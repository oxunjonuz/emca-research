"""Terrarium v4 -- the EPISTEMIC-VALUE world (turn 105, op_097e99fae22e
+ op_6d6b5f5a1105): a world where a FALSE causal edge corrupts
PLANNING at the price of life, and where reaching food itself requires
chain understanding.

Design directive (owner): (1) food is hard to reach and must be
earned through chains of actions, not wandering; (2) false beliefs are
expensive -- the agent that believes a false link walks away from food
into a dangerous zone and loses energy or dies; (3) raw curiosity is
itself costly or insufficient -- without a filter of what actually
matters, the agent spends its life in vain. In such a world causal
understanding may START to pay.

TerrariumV33 is kept WHOLE (scarcity, chain, altar gray edge, linger
trap, storm tree competence). Three deltas:

DELTA 1 -- THE SECOND-ORDER DECOY: (grasp, torch_lit).
  A brazier stands at TRAP_CELL (3,6) -- in the upper-right pocket,
  away from every food source (storm trees spawn near the bell (1,3);
  berries are upper-left / far zone). In a STORM the brazier pulses a
  flame: lit 60 steps / dark 40 steps, purely by the wind -- the agent
  cannot light it. The flame is a WORLD EVENT (info['torch_lit']=True
  on every lit step): by the linger mechanism (the storm tree is the
  only food, and grasping it is the competent foraging action), grasp
  correlates with torch_lit (P(lit|grasp) ~ 0.35 vs ~0.15 pooled) --
  but the oracle P(lit|do(a)) is equal for every action. The pooled
  v2.1 identifier ACCEPTS the false edge; the stratified v2.5c
  REJECTS it (the flame is shared by every action at the tree).
  The false edge is ACTIVE in planning: the v4 goal menu has a
  "torch" goal (bank torches for the treasury); for a BELIEVER the
  decoy edge routes empty grasps at the brazier -- the flame's tile
  is in view, so its plan fires 'grasp' next to a fire it cannot
  influence, paying the storm price 1.8 per grasp, inside the
  scorch pocket (dist<=1 of a lit brazier costs 2.2/step).

DELTA 2 -- THE TREASURY: food behind a competence CHAIN.
  The treasury tile 'Q' at (2,1) pays +10 energy / +1 reward per eat,
  but ONLY if the agent has BANKED torches: standing on the brazier
  cell while a torch is lit and the stack is not full collects one
  (max 3 banked). Brute force cannot bank torches (random agents
  scorch and die; verify gate V2). The chain is: know where food is
  -> know that torches are collected by STANDING (not grasping) ->
  pay the scorch ONCE per pulse -> eat at the treasury when calm+warm.

DELTA 3 -- BITTER CURIOSITY.
  The torch pulse is a rich NOVELTY source (new view tile 'X', new
  transition rhythms) in the most dangerous pocket of the map. A
  novelty-driven agent is pulled there by its own generator -- into
  the scorch -- during storms, when every step costs fury -3.0.
  Curiosity is no longer free: the filter "what actually influences
  my survival" is exactly what the causal model provides.

Ground truth (v4):
  (grasp, torch_lit)  0.0   -- NEW decoy, NOT causal (oracle-checked)
  (eat, treasury_ate) 1.0   -- TRUE chain edge (the competence)
  all v3.3 ground truth unchanged.
"""
import random

from env_terrarium_v33 import TerrariumV33, BERRY_TARGET_WARM
from env_terrarium_v32 import ALTAR_POS, PATCH_POS
from env_terrarium_v3 import W, H, MAP, ACTIONS, BELL_POS, EMPTY

TRAP_CELL = (3, 6)             # the brazier pocket
TREASURY_POS = (2, 1)          # the treasury cell (overlay tile '$')
BLOCKED_CELLS = ((2, 3), (2, 4))   # the warm-zone gate walls
# The gates are REAL walls: MAP (shared list of strings from
# env_terrarium_v3) is row-replaced at v4 import so every inherited
# mechanic (berry spawn, view, reachability) sees the blocked cells as
# walls. Every v4 run lives in its own process/subprocess and never
# imports the v3.3 runner, so no v3.3 numbers are touched.
_old_row = MAP[2]                       # "#.......#"
MAP[2] = (_old_row[:3] + "##" + _old_row[5:])
SCORCH_COST = 2.2              # per step within dist<=1 of a LIT brazier
TORCH_LIT_ON = 60              # flame burns 60 steps
TORCH_LIT_OFF = 40             # then dark 40 steps
TORCH_SPAWN_GAP = 90           # min steps between spawns
TORCH_STACK_MAX = 3            # brazier holds max 3 torches
TREASURY_ENERGY = 10.0
TREASURY_REWARD = 1.0
BRAZIER_TILE = "X"
TREASURY_TILE = "$"


class TerrariumV4(TerrariumV33):
    def __init__(self, seed, regime_flip_at=3000):
        super().__init__(seed, regime_flip_at=regime_flip_at)
        self.torches = 0             # torches standing in the brazier
        self.torch_bank = 0          # torches collected by the agent
        self.torch_lit = False
        self.torch_dwell = 0
        self.last_torch_spawn = -10**9
        self.torches_collected = 0
        self.treasury_eaten = 0
        self.scorch_paid = 0.0
        self.scorch_steps = 0
        self.grasps_near_torch = 0
        self.near_trap_steps = 0

    # ---------- helpers ----------
    def _dist_to_trap(self):
        r, c = self.pos
        return abs(r - TRAP_CELL[0]) + abs(c - TRAP_CELL[1])

    def _free_cells(self):
        out = []
        for r in range(1, H - 1):
            for c in range(1, W - 1):
                if MAP[r][c] == "." and (r, c) not in BLOCKED_CELLS \
                        and (r, c) != TRAP_CELL:
                    out.append((r, c))
        return out

    # ---------- the warm berry zone follows the gate walls ----------
    def _maintain_berries(self):
        if self.weather == "calm":
            if self.season == "warm":
                # v4: the old zone (rows 1-2, cols 2-5) is now half
                # walls (the treasury gate). The zone moves to the
                # whole upper corridor, treasury cell excluded.
                zone = [(r, c) for r in (1, 2) for c in range(1, 8)
                        if MAP[r][c] == EMPTY and (r, c) != BELL_POS
                        and (r, c) != TREASURY_POS]
                target = BERRY_TARGET_WARM
                if len(self.berries) < target and zone:
                    free = [c2 for c2 in zone if c2 not in self.berries]
                    if free:
                        self.berries.add(self.rng.choice(free))
            else:
                # cold: inherited behaviour (the far zone is untouched)
                from env_terrarium_v3 import COLD_ZONE
                from env_terrarium_v33 import BERRY_TARGET_COLD
                zone = [c2 for c2 in COLD_ZONE if MAP[c2[0]][c2[1]] == EMPTY]
                target = BERRY_TARGET_COLD
                if len(self.berries) < target and zone:
                    free = [c2 for c2 in zone if c2 not in self.berries]
                    if free:
                        self.berries.add(self.rng.choice(free))
        else:
            self.berries = set()      # storm: no berries anywhere

    # ---------- view: brazier tile + treasury afford ----------
    def obs(self):
        o = super().obs()
        r, c = self.pos
        view = list(o["view"])
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                if (rr, cc) == TRAP_CELL and view[(dr + 1) * 3 + dc + 1] == ".":
                    view[(dr + 1) * 3 + dc + 1] = BRAZIER_TILE
                if (rr, cc) == TREASURY_POS and view[(dr + 1) * 3 + dc + 1] == ".":
                    view[(dr + 1) * 3 + dc + 1] = TREASURY_TILE
        o["view"] = "".join(view)
        # treasury afford: eat only with a banked torch, calm+warm
        if (r, c) == TREASURY_POS and self.torch_bank >= 1 \
                and self.weather == "calm" and self.season == "warm" \
                and "eat" not in o["afford"]:
            o["afford"] = tuple(sorted(o["afford"] + ("eat",)))
        return o

    # ---------- scent: brazier + treasury channels ----------
    def _scent(self, r, c):
        out = super()._scent(r, c)
        for name, obj in (("torch", TRAP_CELL),
                          ("treasury", TREASURY_POS
                           if self.torch_bank >= 1 else None)):
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

    # ---------- movement: the gate walls ----------
    def _move(self, nr, nc):
        if (nr, nc) in BLOCKED_CELLS:
            return
        super()._move(nr, nc)

    # ---------- step ----------
    def step(self, action):
        assert action in ACTIONS, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        info = {}
        # torch pulse (the wind's flame -- a pure world event)
        if self.weather == "storm":
            self.torch_dwell -= 1
            if self.torch_dwell <= 0:
                self.torch_lit = not self.torch_lit
                self.torch_dwell = (TORCH_LIT_ON if self.torch_lit
                                    else TORCH_LIT_OFF)
            if self.torches < TORCH_STACK_MAX \
                    and self.t - self.last_torch_spawn >= TORCH_SPAWN_GAP:
                self.torches += 1
                self.last_torch_spawn = self.t
        else:
            self.torch_lit = False
            self.torch_dwell = 0
        if self.torch_lit:
            info["torch_lit"] = True
        # run the inherited world (moves, berries, tree, chain, death)
        o, r, done, info2 = super().step(action)
        info.update(info2)
        # v4 mechanics after the move (position is final)
        rr, cc = self.pos
        if self.torch_lit and self._dist_to_trap() <= 1:
            self.energy -= SCORCH_COST
            self.scorch_paid += SCORCH_COST
            self.scorch_steps += 1
            info["scorched"] = True
            if self.energy <= 0:
                self.alive = False
                r -= 5.0
                info["died"] = True
                done = True
        if self.torch_lit and (rr, cc) == TRAP_CELL and self.torches > 0:
            self.torches -= 1
            self.torch_bank += 1
            self.torches_collected += 1
            info["torch_collect"] = True
            info["torch_bank"] = True
        if action == "eat" and (rr, cc) == TREASURY_POS and self.torch_bank >= 1:
            self.torch_bank -= 1
            self.energy = min(100.0, self.energy + TREASURY_ENERGY)
            r += TREASURY_REWARD
            self.treasury_eaten += 1
            info["treasury_ate"] = True
        if action == "grasp" and self._dist_to_trap() <= 1:
            self.grasps_near_torch += 1
        if self._dist_to_trap() <= 1:
            self.near_trap_steps += 1
        return self.obs(), r, done or not self.alive, info

    # ---------- ground truth ----------
    def true_causal_edges(self):
        out = super().true_causal_edges()
        out[("grasp", "torch_lit")] = 0.0      # the v4 decoy: NOT causal
        out[("eat", "treasury_ate")] = 1.0      # the competence chain
        return out

    def true_confounders(self):
        out = super().true_confounders()
        out["storm->torch_lit"] = ("the brazier burns only in storms, "
                                   "60 on / 40 off, by the wind")
        out["linger->grasp~torch"] = ("the storm tree is the only food in a "
                                      "storm; competent grasping there "
                                      "correlates with the flame")
        out["scorch"] = ("dist<=1 of a lit brazier costs 2.2/step")
        out["treasury_gate"] = ("eat at 'Q' needs a banked torch: calm+warm, "
                                "collected by standing on the brazier")
        return out
