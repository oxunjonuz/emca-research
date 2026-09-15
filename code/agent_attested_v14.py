"""agent_attested_v14.py -- turn 145, the v14 "ATTESTED" arms (owner directive
msg_00145).

Owner: *"вариант А Продолжить исследование -- добавить учёт «кто кому платил»."*

THE ONE DECLARED SUBSTITUTION PER ARM, and nothing else. Every arm is
`agent_safety_v10.AgentSafetyBase` -- the FROZEN `agent_emca_v7.AgentV7Base.act`
with a declared guard on its output. NO LINE OF THE FROZEN POLICY IS COPIED. The
v13 instrumentation (`agent_ledger_v13.LedgerBase`, itself a subclass of the frozen
safety base) is INHERITED, not copied; v14 adds one accumulator pair, one change-log
and one property override that CALLS v13's getter instead of re-implementing it.

  a_none       -- no guard at all: v10's B0. Saturation control / identity anchor.
  a_scalar     -- the TOTAL receipt. The frozen B4 arm, blind to provenance.
                  Behaviourally identical to v13's `l_scalar`.
  a_believe    -- the world-attributed receipt AS REPORTED. This is v13's `l_ledger`
                  verbatim: it does not look at `attested` at all. It is the licence
                  for the whole substitution -- with the auditor absent it must
                  reproduce the frozen v13 `l_ledger` cells field for field (HA5).
  a_failclosed -- the world-attributed receipt ONLY on ATTESTED steps; an unattested
                  step contributes NOTHING to the statistic. The declared cautious
                  reading of a receipt whose provenance has not been attested.

WHAT THE AGENT IS NOT ALLOWED TO DO (the owner's v12 constraint, msg_00141,
inherited through v13): it does not falsify the signal and does not invent its own
provenance. The receipt -- split AND attestation -- arrives in the OBSERVATION
(`o["receipt"]`), issued by the world. The agent only decides WHICH PART OF ITS OWN
RECEIPT TO BELIEVE. AST-audited in the independent pass (HA8): 0 `def act`, no writes
into the observation or `info` it was handed, no `random`.

Instrumentation (declared, prereg §4 + §9): v13's counters, plus
`attested_world_rich_receipt`, `attested_rich_steps`, `unattested_rich_steps` and a
compact `stat_history` -- the arm's own statistic recorded on every CHANGE, with the
step at which it changed. The change-log is what makes "the vulnerability relocates"
a measurement: it shows whether a late attestation ever moves the number the guard
reads, and at which step.
"""
from agent_safety_v10 import AgentSafetyBase, SOCIAL_COST, MIN_OBS
from agent_ledger_v13 import LedgerBase


class AttestedBase(LedgerBase):
    """v13's ledger base + the attestation counters + the change-logged statistic."""

    IDENTIFIER_VERSION = "attested v14 base"

    def __init__(self, seed=0):
        LedgerBase.__init__(self, seed)
        # ---- the attestation counters (declared, prereg §4)
        self.attested_world_rich_receipt = 0.0   # world part, attested steps only
        self.attested_rich_steps = 0             # attested rich reward steps
        self.unattested_rich_steps = 0           # the same steps, unattested
        self.attested_steps_seen = 0
        self.unattested_steps_seen = 0
        # ---- the change-log of the number the guard actually reads
        self._last_logged_stat = None
        self.stat_history = []                   # [(agent_t, stat)] on change

    @property
    def rich_rate_obs(self):
        # CALL v13's getter (it assigns `rate_at_first_decision`, `_stat_cache`
        # and keeps the frozen semantics); do not re-implement it.
        stat = LedgerBase.rich_rate_obs.fget(self)
        if stat != self._last_logged_stat:
            self._last_logged_stat = stat
            self.stat_history.append((self.t, stat))
        return stat

    @rich_rate_obs.setter
    def rich_rate_obs(self, value):
        LedgerBase.rich_rate_obs.fset(self, value)

    def observe(self, o, a, r, o2, done, info):
        # the whole frozen + v13 observation path, untouched
        LedgerBase.observe(self, o, a, r, o2, done, info)
        rec = (o2 or {}).get("receipt")
        if rec is None:
            return
        if rec.get("attested"):
            self.attested_steps_seen += 1
        else:
            self.unattested_steps_seen += 1
        f1 = self._feat(o)
        on_rich_nonmove = (a in ("wait", "press", "grasp") and f1["on_rich"])
        if not on_rich_nonmove or r <= 0:
            return
        if rec.get("attested"):
            self.attested_world_rich_receipt += rec.get("world", 0.0)
            self.attested_rich_steps += 1
        else:
            self.unattested_rich_steps += 1


class ANone(AgentSafetyBase):
    """No guard: v10's B0. Identity anchor."""
    IDENTIFIER_VERSION = "v14 identity: v10 s0_nobrake"


class AScalar(AttestedBase):
    """The frozen B4 arm: the total receipt, blind to provenance."""
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "v14 scalar: the total receipt (frozen B4 statistic)"

    def _stat_from_raw(self, raw):
        return raw


class ABelieve(AttestedBase):
    """The world-attributed receipt as reported -- v13's `l_ledger` verbatim."""
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "v14 believe: world-attributed receipt as reported"

    def _stat_from_raw(self, raw):
        if getattr(self, "rich_steps", 0) <= 0:
            return 0.0
        return self.world_rich_receipt / self.rich_steps


class AFailClosed(AttestedBase):
    """Only ATTESTED receipts count; an unattested receipt is worth nothing."""
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "v14 fail-closed: attested world receipt only"

    def _stat_from_raw(self, raw):
        if getattr(self, "rich_steps", 0) <= 0:
            return 0.0
        return self.attested_world_rich_receipt / self.rich_steps


ARMS = {
    "a_none": ANone,
    "a_scalar": AScalar,
    "a_believe": ABelieve,
    "a_failclosed": AFailClosed,
}


def make_agent(arm, seed):
    return ARMS[arm](seed)
