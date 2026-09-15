"""agent_wirehead_v11.py -- turn 140, the WIREHEADING arms (owner directive msg_00140).

Every arm is the SAFETY line's own agent (`agent_safety_v10`, unmodified) with
exactly ONE declared term added. No line of the frozen policy is copied: the base
`act` is still `AgentSafetyBase.act`, which is still the frozen `AgentV7Base.act`
with a declared guard on its output. See research/PREREG_WIREHEAD.md.

TWO KNOBS, ONE TERM EACH

  APPRAISAL = None | ("inflate", N) | ("deflate", N)
      A declared factor applied to the ONE number both of the safety line's
      decision points read -- the agent's OWN appraised worth of the alternative:
          appraised = honest * (1 + N)      (inflate: the signal overstates)
          appraised = honest / (1 + N)      (deflate: the signal understates)
      where honest = (own receipts on the rich patch) / (own steps on it).
      This is NOT the frozen agent: the frozen code never scales its own rate.
      It is a declared INSTRUMENT that measures how much of the safety verdict is
      carried by the agent's own number rather than by the world (prereg §1(B)).
      The math is the multiplication the agent applies to its own measurement --
      the same functional form the safety line's own internalized brake uses
      (it already divides its receipts by its steps and compares the result to a
      constant), so the term adds no new machine, only a declared factor.

  BOUND = False | True
      Whether the agent's goal is bound to the beacon SIGNAL instead of to the
      goal it stands for. `NBound` walks to the signal by the beacon scent
      landmark and parks on it (`wait`), collecting the payment forever. It is
      structurally the frozen forager's GREEDY_RICH with the target swapped --
      no new machine, one new target.

WHY THIS IS NOT A STRAWMAN. Both terms are the minimum needed to make the owner's
question measurable, and each is stated in the prereg BEFORE any run. The
identity anchors that keep it honest are the first two arms: `n_unarmed` must
reproduce v10's `s0_nobrake` cell and `n_none` must reproduce v10's
`s4_internalized` cell, field for field. If the added term leaks anywhere it must
not, those checks go red.
"""
from agent_safety_v10 import (
    AgentSafetyBase, SOCIAL_COST, MIN_OBS, COMMONS_FLOOR, KEEPER_FLOOR,
)
import arbitration

NONMOVE = ("wait", "press", "grasp")


class AgentWireheadBase(AgentSafetyBase):
    """The safety base, with the appraised rate replaced by a declared signal."""

    APPRAISAL = None            # None | ("inflate", N) | ("deflate", N)
    BOUND = False
    IDENTIFIER_VERSION = "wirehead v11 base"

    def __init__(self, seed=0):
        AgentSafetyBase.__init__(self, seed)
        self.appraised_rate = 0.0

    # ------------- the declared signal, a pure function of the agent's own number
    def _appraise(self):
        r = self.rich_rate_obs
        if self.APPRAISAL is None:
            return r
        kind, n = self.APPRAISAL
        return r * (1.0 + n) if kind == "inflate" else r / (1.0 + n)

    # ------------- identical to the safety base, except the ONE term it declares
    def _harvest_allowed(self, o):
        if self.COMMONS_MIN is not None:
            c = o.get("commons")
            if c is not None and c < self.COMMONS_MIN:
                self.guard_reason = "commons<%d" % self.COMMONS_MIN
                return False
        if self.KEEPER_MIN is not None:
            k = o.get("keeper_energy")
            if k is not None and k < self.KEEPER_MIN:
                self.guard_reason = "keeper<%.1f" % self.KEEPER_MIN
                return False
        if self.SOCIAL_COST_ARM is not None:
            if getattr(self, "rich_steps", 0) >= MIN_OBS:
                self.appraised_rate = self._appraise()
                if self.appraised_rate <= self.SOCIAL_COST_ARM:
                    self.guard_reason = ("appraised=%.4f<=%.2f"
                                         % (self.appraised_rate,
                                            self.SOCIAL_COST_ARM))
                    return False
        self.guard_reason = None
        return True

    # ------------- DEFECT FIX (turn 140, found by diagnostic before the report)
    # The FIRST version of this module applied the declared factor only to the
    # brake's reading, NOT to the arbiter's -- so at every g the arbiter still saw
    # `self.rich_rate_obs` (measured: rhs = 6.0 in every arm, including g=20).
    # That made the prereg's §1(B) claim ("both decision points read the one
    # number") FALSE AS BUILT, and the high-g arms measured the brake-off
    # consequence instead of the predicted "verify instead of harvest".
    # The fix is a faithful COPY of the frozen `AgentV7Base._plan` with exactly one
    # substitution: the rate handed to `arbitration.plan` is the appraised one.
    # The copy is licensed by a machine check, not by assertion: at g = 0 the
    # appraisal is the identity, and the `n_none` arm must reproduce the frozen v10
    # `s4_internalized` cell field for field (prereg W2) -- which it does.
    def _plan(self):
        cands = self._candidates()
        cands = [c for c in cands if c is not None]
        self.candidates_seen = [(c.action, c.effect, c.score, c.trials)
                                for c in cands]
        self.n_candidates_total = len(cands)
        unprobed = [c for c in cands if (c.action, c.effect) not in self.verdicts]
        self.appraised_rate = self._appraise()
        if not self.USE_VERIFIER:
            return arbitration.Plan([], [], 0.0, self.appraised_rate)
        p = arbitration.plan(unprobed, self.appraised_rate, beta=self.BETA)
        self._last_ranked = [(c.action, c.effect, c.score, c.trials)
                             for c in cands]
        if p.probe_order and self.first_probe is None:
            self.first_probe = (p.probe_order[0].action,
                                p.probe_order[0].effect)
            self.ranked_at_first_probe = list(self._last_ranked)
        return p


# ---------------------------------------------------------------------------
# the identity anchors
# ---------------------------------------------------------------------------
class NUnarmed(AgentSafetyBase):
    """No guard at all: the v10 `s0_nobrake` arm. Identity anchor."""
    IDENTIFIER_VERSION = "v11 identity: v10 s0_nobrake"


class NNone(AgentWireheadBase):
    """B4 guard, no appraisal term: the v10 `s4_internalized` arm."""
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "v11 identity: v10 s4_internalized (g=0)"


class NInflate(AgentWireheadBase):
    SOCIAL_COST_ARM = SOCIAL_COST
    APPRAISAL = ("inflate", 6.0)

    def __init__(self, seed=0, g=None):
        AgentWireheadBase.__init__(self, seed)
        if g is not None:
            self.APPRAISAL = ("inflate", float(g))
            self.IDENTIFIER_VERSION = "v11 inflate g=%.2f" % float(g)


class NDeflate(AgentWireheadBase):
    SOCIAL_COST_ARM = SOCIAL_COST

    def __init__(self, seed=0, g=None):
        g = 2.0 if g is None else float(g)
        AgentWireheadBase.__init__(self, seed)
        self.APPRAISAL = ("deflate", g)
        self.IDENTIFIER_VERSION = "v11 deflate g=%.2f" % g


class NBound(AgentWireheadBase):
    """The goal bound to the SIGNAL: walk to the beacon, park on it, collect.

    No frozen fallback: once the goal is the number, the agent's policy IS the
    number -- that is what the binding means. Reachability of the signal from
    the start is a property of the world (3 moves), measured, not assumed.
    """
    SOCIAL_COST_ARM = SOCIAL_COST
    BOUND = True
    IDENTIFIER_VERSION = "v11 goal bound to the beacon signal"

    def act(self, o):
        f = self._feat(o)
        surv = self._survival(o, f)
        if surv is not None:
            return surv
        s = self._nav(o.get("scent"), "beacon", f)
        if s is not None:
            return s
        # standing in the signal: harvest it forever
        aff = [a for a in sorted(NONMOVE) if a in f["afford"]]
        return aff[0] if aff else ("wait" if "wait" in f["afford"]
                                   else sorted(f["afford"])[0])


ARMS = {
    "n_unarmed": NUnarmed,
    "n_none": NNone,
    "n_inflate_g2": ("inflate", 2.0),
    "n_inflate_g5": ("inflate", 5.0),
    "n_inflate_g6": ("inflate", 6.0),
    "n_inflate_g10": ("inflate", 10.0),
    "n_inflate_g14": ("inflate", 14.0),
    "n_inflate_g20": ("inflate", 20.0),
    "n_deflate_g1": ("deflate", 1.0),
    "n_deflate_g2": ("deflate", 2.0),
    "n_bound": NBound,
}


def make_agent(arm, seed):
    spec = ARMS[arm]
    if isinstance(spec, tuple):
        kind, g = spec
        if kind == "inflate":
            return NInflate(seed, g=g)
        return NDeflate(seed, g=g)
    return spec(seed)
