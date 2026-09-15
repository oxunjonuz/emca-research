"""Terrarium v6 -- the GREY-TRUTH world (turn 115, msg_00115,
self-directed after V5). The question this world answers, chosen from
the campaign's own open cells: does ACTIVE causal experimentation PAY
when it is the ONLY epistemic route to an expensive resource?

Why this cell: v4 priced the LIE (false edge corrupts planning, -3159);
v5 measured the CAPABILITY of passive truth (exclusive resource 10/10
vs 3) and found its reward microscopic against the fruit weather noise
(+8 prize vs ~466 opportunity cost, corr(D, fruit_gap)=0.999); the
v3.2/v3.3 prober line resolved grey edges (11/15, 3/3 verdicts) but
never had a payday. The combination never measured: an edge in the
GREY zone (1<=RR<2, where every passive layer stops) guarding an
EXPENSIVE prize. The fourth side of the tetrahedron: the price of
DISCOVERY itself.

TerrariumV5 kept WHOLE (v4 gates/scorch/treasury, v3.3 deficit economy,
spring+lotus). Deltas frozen in research/PREREG_V6.md before any agent
run; the AMENDMENT section there records the two calibration
corrections made while building this file (both BEFORE any agent ran,
as the prereg authorizes for world constants):

D1 -- THE GREY SPRING. FLOW_WAIT 0.30, FLOW_BACKGROUND 0.20. Within-
  aura RR = 1.5: the stratified gate (RR>=2) cannot accept; pooled is
  diluted; assoc(0.5) blind (marginal 0.30*w < 0.5). No passive path.

D2 -- THE EXPENSIVE PRIZE. LOTUS_REWARD 800, LOTUS_ENERGY 60 (the
  golden lotus). Calibration target (the prereg's own): a knowledgeable
  farmer at 3-6 blooms/life -> +2400..+4800 direct reward, clearing the
  fruit weather noise (+-2471 sd/seed, turn 104) at the top end and the
  +300 practical bar at the low end.

D3 -- ANTI-ILLUSION (AMENDED twice during calibration, pre-agent; see
  the prereg's amendment section). Final form: NO momentum window.
  Only WAIT-flows fill the vessel (+3 each); a flow while acting
  sprays past it (the event flag still fires for every flow -- the
  visible event stays grey and action-shared; the FILL is the
  patient's privilege, and the pool level is not observable). The
  arithmetic: streak-waiting nets 0.30*3 - 0.70*1 = +0.20/wait (a
  bloom in ~120 waits); the blind 1/4 cadence nets ~-2.1 per 4-step
  cycle (peaks <= 6 of 24, never fills). The first draft's momentum
  window (a post-flow lift) was REMOVED: measured on the toy, it
  coupled epistemology back into the statistics -- the streak-farmer's
  own wait-rate rose to ~0.35 and the passive stratified RR climbed
  above the 2.0 gate (self-reinforcing belief: acting on the edge
  produced the data that justified it, and the 'grey' edge was never
  grey for anyone who already believed it). Without the window the
  wait-rate is 0.30 for everyone, always: the grey zone is stable.

D4 -- THE DECOY STAYS (brazier, grasp~torch_lit, real scorch).

D5 -- RECHARGE. AMENDED (calibration, pre-agent): LOTUS_NEED 15->24,
  LOTUS_COOLDOWN 600->2000. The draft constants left the scripted
  streak-waiter cooldown-bound at ~10+ blooms/life, above the declared
  3-6 target; the tuned cycle (~330 productive waits + 2000 dry)
  lands the continuous-farming ceiling at ~6-7, the realistic farmer
  at 4-6. While the spring sleeps it renders DRY ('w') -- a
  WORLD-VISIBLE public signal (like the bell glow): every arm knows
  the channel is closed; no wasted pursuit, no infinite rent.

Implementation note (the honest harness detail): TerrariumV5.step
applies the v5 spring block with the v5 module constants -- v6 MUST
NOT call it. TerrariumV6.step calls the v4 grandparent directly (the
whole inherited world minus v5's spring/lotus block) and applies the
v6 spring/lotus mechanics itself.
"""
import random

from env_terrarium_v4 import TerrariumV4
from env_terrarium_v5 import TerrariumV5, SPRING_POS
from env_terrarium_v3 import W, H, MAP, EMPTY, ACTIONS

FLOW_BACKGROUND = 0.20     # P(flow event | any action but wait, in the aura)
FLOW_WAIT = 0.30            # P(flow | wait, in the aura) -- the GREY cause
MOMENTUM_SPAN = 0           # NO momentum window (removed: it coupled the
                            # agent's own policy back into the statistics
                            # and un-greyed the edge for believers -- see
                            # the module docstring and the prereg amendment)
FLOW_MOMENTUM = FLOW_WAIT   # unused (kept for interface compatibility)
FLOW_GAIN = 3               # a WAIT-flow raises the pool by 3 (the fill
                            # is the patient's privilege; non-wait flows
                            # spray past -- the event fires, the pool
                            # does not fill)
DECAY_TICKS = 1             # every in-aura no-flow step drains 1
LOTUS_NEED = 24             # pool level that blooms the golden lotus
LOTUS_ENERGY = 60.0
LOTUS_REWARD = 800.0
LOTUS_LIFE = 80
LOTUS_COOLDOWN = 2500       # the spring sleeps after a bloom (renders DRY)

SPRING_TILE = "W"           # wet (flows possible)
DRY_TILE = "w"              # dry (cooldown: no flows, world-visible)
LOTUS_TILE = "O"


class TerrariumV6(TerrariumV5):
    def __init__(self, seed, regime_flip_at=3000):
        super().__init__(seed, regime_flip_at=regime_flip_at)
        self.cooldown = 0            # steps of spring sleep after a bloom
        self.windows_opened = 0      # kept at 0 (no window; interface)

    # ---------- the flow probability (v6 rules; no window) ----------
    def _flow_p(self, action):
        if self.cooldown > 0:
            return 0.0
        if action == "wait":
            return FLOW_WAIT
        return FLOW_BACKGROUND

    # ---------- view: the dry spring is a public signal ----------
    def obs(self):
        o = super().obs()
        if self.cooldown > 0:
            o["view"] = o["view"].replace(SPRING_TILE, DRY_TILE)
        return o

    # ---------- step: the v4 world + the v6 spring ----------
    def step(self, action):
        assert action in ACTIONS, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        # the inherited world WITHOUT v5's spring/lotus block
        o, r, done, info = TerrariumV4.step(self, action)
        rr, cc = self.pos
        if self._in_aura():
            self.aura_steps += 1
            if action == "wait":
                self.waits_in_aura += 1
            flowed = self.cooldown <= 0 \
                and self.rng.random() < self._flow_p(action)
            if flowed:
                self.spring_flows += 1
                self.no_flow_run = 0
                info["spring_flow"] = True
                if action == "wait":
                    # only the patient pour fills the vessel
                    self.pool = min(LOTUS_NEED, self.pool + FLOW_GAIN)
                if self.pool >= LOTUS_NEED and not self.lotus:
                    self.lotus = True
                    self.lotus_fuel = LOTUS_LIFE
                    self.pool = 0
                    self.pool_fills += 1
                    self.cooldown = LOTUS_COOLDOWN
                    info["lotus_bloom"] = True
            else:
                self.no_flow_run += 1
                if self.no_flow_run >= DECAY_TICKS:
                    self.pool = max(0, self.pool - 1)
                    self.no_flow_run = 0
        else:
            pass
        # the golden lotus eat (v6 values)
        if action == "eat" and self.lotus and (rr, cc) == SPRING_POS:
            self.lotus = False
            self.lotus_fuel = 0
            self.energy = min(100.0, self.energy + LOTUS_ENERGY)
            r += LOTUS_REWARD
            self.lotus_eaten += 1
            info["lotus"] = True
        # the spring sleeps anywhere on the map
        if self.cooldown > 0:
            self.cooldown -= 1
        # lotus expiry
        if self.lotus:
            self.lotus_fuel -= 1
            if self.lotus_fuel <= 0:
                self.lotus = False
                self.lotus_fuel = 0
        return self.obs(), r, done or not self.alive, info

    # ---------- ground truth ----------
    def true_causal_edges(self):
        out = super().true_causal_edges()
        out[("wait", "spring_flow")] = 1.0      # TRUE GREY cause (RR=1.5)
        out[("wait", "lotus")] = 1.0
        return out

    def true_confounders(self):
        out = super().true_confounders()
        out["grey_spring"] = ("wait flows at 0.30 in the aura vs 0.20 "
                              "background: RR=1.5 -- GREY. The stratified "
                              "gate (RR>=2) cannot accept it; pooled is "
                              "diluted; assoc(0.5) blind (0.30*w<0.5). "
                              "Only an intervention resolves it.")
        out["momentum_window"] = ("REMOVED during calibration (pre-agent): "
                                  "the post-flow lift coupled the agent's "
                                  "own policy back into the statistics -- "
                                  "the streak-farmer's wait-rate rose to "
                                  "~0.35 and the passive stratified RR "
                                  "climbed above the 2.0 gate (a "
                                  "self-reinforcing belief). Without the "
                                  "window the wait-rate is 0.30 for "
                                  "everyone, always: the grey zone is "
                                  "stable. Only wait-flows fill the pool "
                                  "(+3); streak-waiting nets +0.20/wait "
                                  "(a bloom in ~120 waits); the blind 1/4 "
                                  "cadence nets ~-2.1/cycle and never "
                                  "fills.")
        out["golden_lotus"] = ("+800 reward / +60 energy; after a bloom "
                               "the spring sleeps 2000 steps and renders "
                               "DRY ('w') -- a public signal")
        return out
