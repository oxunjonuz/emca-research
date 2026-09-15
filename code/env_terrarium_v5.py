"""Terrarium v5 -- the TRUE-EDGE-VALUE world (turn 106 directive,
op_30a1023467a9 + op_849188424224): the first world of the campaign
where knowledge of a TRUE causal edge gives the agent a resource
channel the ASSOCIATIVE model does not have -- and, through the
permissive-assoc control, measures that the value is SELECTIVITY, not
possession.

The owner's framing: across the whole campaign no world existed where
knowing a TRUE causal link gave the agent something the associative
model lacks. The causal module so far either changed nothing or merely
refused to be fooled. This world closes that gap.

THE MASKED TRUE EDGE -- (wait, spring_flow).
  The SPRING at (7,7) (tile 'W'), in the cold berry zone (the agent has
  unrelated reasons to be there -- cold foraging -- so the aura gets
  crossed and its actions tried). Inside the aura (the 3x3 view of the
  spring) the water flows: P(spring_flow) = 0.25 per step for EVERY
  action except wait; P(spring_flow | wait) = 0.65. The edge is TRUE,
  and it is MASKED, each layer in its own way:
    * assoc (min_p=0.5): the marginal rate(wait->flow) = 0.65 * w,
      w = the agent's in-aura share of waits. Nothing in any arm's
      machinery concentrates waits in the aura above w ~ 0.4, and the
      blindness holds for every w < 0.77 -- STRUCTURAL.
    * pooled v2.1 / spec v2.2: their contrast is diluted by the agent's
      own exploration (waits everywhere vs waits in the aura);
      pooled_others is diluted too (zeros outside the aura). The
      verdicts are trajectory-dependent -- measured columns, predicted
      borderline (the prereg states this; they are NOT gates).
    * stratified v2.5c: the contrast is WITHIN the aura context (wait
      0.65 vs the others' 0.25, RR = 2.6 >= 2) -- the exposure
      weighting cancels the dilution. The only layer that knows the
      edge RELIABLY.
  The structural duality with the campaign's decoys: a linger decoy is
  a FALSE edge that looks exclusive in the pooled contrast but is
  shared within the action's contexts; the spring is a TRUE edge that
  looks shared in the pooled contrast but is exclusive within the
  action's contexts. The stratified rule is the only one that gets both
  right -- this world tests that, behaviourally.

THE PAYOFF -- the pool and the lotus.
  Flows fill the pool (+1 per flow). The pool LEAKS: every in-aura
  no-flow step drains 1 (DECAY_TICKS=1); AWAY from the aura the pool is
  FROZEN (the vessel holds). The fill threshold is p > 0.5:
    background 0.25      -> net -0.50/step  (drains, always)
    1/3-wait blend 0.38  -> net -0.23/step  (blind patience NEVER fills)
    waiting 0.65         -> net +0.30/step  (15 flows in ~50 waits)
  12 flows -> the LOTUS blooms on the spring cell (+30 energy, +8
  reward, eatable, lives 80 steps). Brute force and blind patience are
  structurally excluded (verify NV2-NV4). The lotus goal is in every
  arm's menu (5th -- before the goals that would monopolise the slot);
  its ONLY route in the plan is an edge in the agent's own model,
  place-checked at the spring tile in view. Navigation to the spring
  (the scent channel + the episodic tile) is world-knowledge of WHERE
  the spring is -- shared by every arm; WHAT causes the flow is exactly
  what the identifiers disagree on. Blind arms pay an exploration tax
  (up to 3 x 1200 steps of goal pursuit in the aura, then demotion).

Everything else is TerrariumV4 whole: scarcity, the lever->key->door
chain, the altar gray edge, the bell linger trap, the brazier decoy,
the treasury.
"""
import random

from env_terrarium_v4 import TerrariumV4
from env_terrarium_v3 import W, H, MAP, EMPTY, BERRY, ACTIONS

SPRING_POS = (7, 7)
SPRING_TILE = "W"
LOTUS_TILE = "O"             # the bloomed lotus (a distinct sensory tile:
                             # sight is shared by every arm -- knowing
                             # WHAT blooms it is the identifiers' dispute)
FLOW_BACKGROUND = 0.10     # P(flow | any action but wait, in the aura)
FLOW_WAIT = 0.48            # P(flow | wait, in the aura) -- the TRUE cause
FLOW_GAIN = 2               # a flow raises the pool by 2
DECAY_TICKS = 1             # every in-aura no-flow step drains 1
LOTUS_NEED = 15             # pool level that blooms the lotus
LOTUS_ENERGY = 30.0
LOTUS_REWARD = 8.0
LOTUS_LIFE = 80


class TerrariumV5(TerrariumV4):
    def __init__(self, seed, regime_flip_at=3000):
        super().__init__(seed, regime_flip_at=regime_flip_at)
        self.pool = 0
        self.no_flow_run = 0
        self.lotus = False
        self.lotus_fuel = 0
        self.spring_flows = 0
        self.lotus_eaten = 0
        self.pool_fills = 0
        self.waits_in_aura = 0
        self.aura_steps = 0

    # ---------- the aura ----------
    def _in_aura(self):
        r, c = self.pos
        return abs(r - SPRING_POS[0]) <= 1 and abs(c - SPRING_POS[1]) <= 1

    # ---------- view: spring tile + lotus overlay ----------
    def obs(self):
        o = super().obs()
        r, c = self.pos
        view = list(o["view"])
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                if (rr, cc) == SPRING_POS:
                    i = (dr + 1) * 3 + (dc + 1)
                    if self.lotus:
                        view[i] = LOTUS_TILE    # the lotus is visible food
                    elif view[i] == EMPTY:
                        view[i] = SPRING_TILE
        o["view"] = "".join(view)
        if self.lotus and (r, c) == SPRING_POS \
                and "eat" not in o["afford"]:
            o["afford"] = tuple(sorted(o["afford"] + ("eat",)))
        return o

    # ---------- scent: the spring joins the navigable objects ----------
    def _scent(self, r, c):
        out = super()._scent(r, c)
        orow, ocol = SPRING_POS
        d_here = abs(r - orow) + abs(c - ocol)
        out["spring"] = {
            "up": (abs(r - 1 - orow) + abs(c - ocol)) - d_here,
            "down": (abs(r + 1 - orow) + abs(c - ocol)) - d_here,
            "left": (abs(r - orow) + abs(c - 1 - ocol)) - d_here,
            "right": (abs(r - orow) + abs(c + 1 - ocol)) - d_here,
        }
        return out

    # ---------- the spring cell never hosts a bloom berry ----------
    def _maintain_berries(self):
        super()._maintain_berries()
        self.berries.discard(SPRING_POS)

    # ---------- step ----------
    def step(self, action):
        assert action in ACTIONS, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        o, r, done, info = super().step(action)
        rr, cc = self.pos
        # ---- the spring (position final; weather-free by design) ----
        if self._in_aura():
            self.aura_steps += 1
            if action == "wait":
                self.waits_in_aura += 1
            p = FLOW_WAIT if action == "wait" else FLOW_BACKGROUND
            if self.rng.random() < p:
                self.spring_flows += 1
                self.pool = min(LOTUS_NEED, self.pool + FLOW_GAIN)
                self.no_flow_run = 0
                info["spring_flow"] = True
                if self.pool >= LOTUS_NEED and not self.lotus:
                    self.lotus = True
                    self.lotus_fuel = LOTUS_LIFE
                    self.pool = 0
                    self.pool_fills += 1
                    info["lotus_bloom"] = True
            else:
                self.no_flow_run += 1
                if self.no_flow_run >= DECAY_TICKS:
                    self.pool = max(0, self.pool - 1)
                    self.no_flow_run = 0
        # away from the aura: the vessel is frozen (holds its water)
        # ---- the lotus eat ----
        if action == "eat" and self.lotus and (rr, cc) == SPRING_POS:
            self.lotus = False
            self.lotus_fuel = 0
            self.energy = min(100.0, self.energy + LOTUS_ENERGY)
            r += LOTUS_REWARD
            self.lotus_eaten += 1
            info["lotus"] = True
        # ---- lotus expiry ----
        if self.lotus:
            self.lotus_fuel -= 1
            if self.lotus_fuel <= 0:
                self.lotus = False
                self.lotus_fuel = 0
        return self.obs(), r, done or not self.alive, info

    # ---------- ground truth ----------
    def true_causal_edges(self):
        out = super().true_causal_edges()
        out[("wait", "spring_flow")] = 1.0      # TRUE (the masked cause)
        out[("wait", "lotus")] = 1.0            # the chain's end
        return out

    def true_confounders(self):
        out = super().true_confounders()
        out["spring_mask"] = ("the spring flows at 0.25 for every action "
                              "in its aura; only wait raises it to 0.65 "
                              "-- the pooled contrast is diluted by the "
                              "agent's own exploration and the assoc "
                              "layer's 0.5 threshold is structurally "
                              "blind (the marginal is 0.65*w < 0.5); "
                              "the stratified within-aura contrast sees "
                              "RR=2.6 and accepts")
        out["pool_leak"] = ("every in-aura no-flow step drains 1; away "
                            "the pool is frozen; the fill threshold is "
                            "p>0.5 -- the background (0.25) and any "
                            "patience blend below pure waiting never "
                            "fill it")
        return out
