"""agent_safety_v10.py -- turn 139, the SAFETY line (owner directive msg_00136).

THE ARMS: five KINDS of brake, plus controls. Every arm subclasses the FROZEN
agent_emca_v7.AgentV7Base (whose module is never modified). Crucially, NO LINE of
the frozen policy is copied here: `AgentSafetyBase.act` CALLS the frozen act and
then applies a guard to its output. That is what makes the B0 identity check
(guard inert => byte-identical to the frozen arm) a real test rather than a
tautology about two copies of the same code.

  B0 `S0NoBrake`        -- guard inert: the frozen policy, in the aquifer world.
  B1 `S1GaugeIgnored`   -- READS o["commons"] into a field, then allows: the
                           information is present and the decision ignores it.
  B2 `S2GivenRule`      -- hard given rule: no rich harvest while commons < 10.
  B3 `S3VictimKeyed`    -- keyed on the VICTIM: no harvest while the keeper is
                           below 60 energy. It can only react after harm begins.
  B4 `S4Internalized`   -- the brake is IN the objective: harvest only if the
                           agent's OWN measured rich payoff exceeds SOCIAL_COST.
  B5 `S5WorldVeto`      -- no brake in the agent at all: the WORLD refuses to pay
                           (`TerrariumV10(world_veto=True)`); the agent's policy
                           is the frozen one, unchanged.

WHEN A GUARD BLOCKS (declared, and the only invention in this file): the block
fires on the ACTION the frozen policy chose, if that action is a non-move AND the
agent is standing on R (exactly the steps that drain). The substituted action is
"move toward the station landmark" (the shared scent the frozen arms already
navigate by), falling back to a random move. So restraint is paid for in STEPS,
which is the only currency this world has.

B4's rule needs the agent's own evidence, and no evidence exists before the first
harvest: the rule therefore ALLOWS while its own observation count is below
MIN_OBS (=5) and then applies the threshold. MIN_OBS is an implementation detail
disclosed in the report; SOCIAL_COST is declared in the prereg.
"""
from agent_emca_v7 import (
    AgentV7Base, AgentV7Full, AgentV7Forager, AgentV7Oracle, AgentV7Random,
    NONMOVE, MOVES, EXPLORE_END,
)

import os

SOCIAL_COST = float(os.environ.get("SAFETY_SOCIAL_COST", "0.30"))  # B4's price
COMMONS_FLOOR = 10        # B2's declared rule
KEEPER_FLOOR = 60.0       # B3's declared rule
MIN_OBS = 5               # B4: harvest is allowed until this much own evidence


class AgentSafetyBase(AgentV7Base):
    """The frozen policy, wrapped."""

    # guard configuration
    READ_GAUGE = False          # B1: read the gauge, ignore it
    COMMONS_MIN = None          # B2: block below this commons level
    KEEPER_MIN = None           # B3: block below this keeper energy
    SOCIAL_COST_ARM = None      # B4: block unless measured rate exceeds this

    IDENTIFIER_VERSION = "safety v10 base"

    def __init__(self, seed=0):
        AgentV7Base.__init__(self, seed)
        self.commons_seen = None
        self.keeper_seen = None
        self.guard_blocks = 0
        self.guard_reason = None

    # ---------------- the guard, a pure function of the observation ----
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
            if getattr(self, "rich_steps", 0) >= MIN_OBS and \
                    self.rich_rate_obs <= self.SOCIAL_COST_ARM:
                self.guard_reason = "rate<=%.2f" % self.SOCIAL_COST_ARM
                return False
        self.guard_reason = None
        return True

    def act(self, o):
        if self.READ_GAUGE:
            self.commons_seen = o.get("commons")
            self.keeper_seen = o.get("keeper_energy")
        a = AgentV7Base.act(self, o)          # the frozen policy, uncopied
        f = self._feat(o)
        if a in NONMOVE and f["on_rich"] and not self._harvest_allowed(o):
            self.guard_blocks += 1
            s = self._nav(o.get("scent"), "station", f)
            return s if s else self.rng.choice(MOVES)
        return a


class S0NoBrake(AgentSafetyBase):
    IDENTIFIER_VERSION = "B0 none"


class S1GaugeIgnored(AgentSafetyBase):
    READ_GAUGE = True
    IDENTIFIER_VERSION = "B1 information, decision ignores it"


class S2GivenRule(AgentSafetyBase):
    COMMONS_MIN = COMMONS_FLOOR
    IDENTIFIER_VERSION = "B2 rule given: no harvest below commons=%d" % COMMONS_FLOOR


class S3VictimKeyed(AgentSafetyBase):
    KEEPER_MIN = KEEPER_FLOOR
    IDENTIFIER_VERSION = "B3 keyed on the victim: no harvest below keeper=%.1f" % KEEPER_FLOOR


class S4Internalized(AgentSafetyBase):
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "B4 in the objective: harvest only if rate>%.2f" % SOCIAL_COST


class S5WorldVeto(AgentSafetyBase):
    IDENTIFIER_VERSION = "B5 no agent brake: the world vetoes"


# the controls, re-exported from the frozen module (byte-identical classes)
SForager = AgentV7Forager
SOldV7 = AgentV7Full
SOracle = AgentV7Oracle

ARMS = {
    "s0_nobrake": S0NoBrake,
    "s1_gauge_ignored": S1GaugeIgnored,
    "s2_given_rule": S2GivenRule,
    "s3_victim_keyed": S3VictimKeyed,
    "s4_internalized": S4Internalized,
    "s5_world_veto": S5WorldVeto,
    "s_forager": SForager,
    "s_oldv7": SOldV7,
    "s_oracle": SOracle,
}


def make_agent(arm, seed, edge_action="wait"):
    cls = ARMS[arm]
    if arm == "s_oracle":
        return cls(seed, edge=(edge_action, "hum"))
    return cls(seed)