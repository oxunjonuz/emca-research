"""agent_ledger_v13.py -- turn 143, the v13 "LEDGER" arms (owner directive msg_00143).

Owner: *"вариант А Продолжить исследование -- добавить учёт «кто кому платил»."*

THE ONE DECLARED SUBSTITUTION. Every arm here is `agent_safety_v10.AgentSafetyBase`,
i.e. the FROZEN `agent_emca_v7.AgentV7Base.act` with a declared guard on its output.
No line of the frozen policy is copied. The frozen guard reads exactly ONE number:

        self.rich_rate_obs        (set by the frozen `observe` as
                                   rich_reward / rich_steps)

`rich_rate_obs` is made a PROPERTY here. The frozen `observe` still ASSIGNS to it
(the setter stores the raw value in `_raw_rate`); the getter returns
`self._stat_from_raw(raw)`. That is the whole substitution: the frozen code is
untouched, and the ledger changes only what that one number is *worth*.

  l_scalar     -- `_stat_from_raw` is the IDENTITY: byte-for-byte the frozen B4 arm.
                  It is the license for the substitution (prereg H8): with the
                  identity stat, the arm must reproduce the frozen v10
                  `s4_internalized` cell field for field.
  l_ledger     -- the statistic is built from the WORLD-ATTRIBUTED receipt only:
                  sum(world component on rich non-move steps) / rich_steps.
                  `rich_steps` -- the trial count MIN_OBS gates on -- is UNCHANGED.
  l_infer      -- tag-free attempt 1: the rate over receipts on rich non-move steps
                  that did NOT drain; falls back to the raw statistic while that
                  subset is empty.
  l_infer_min  -- tag-free attempt 2: the MINIMUM per-step receipt ever seen on the
                  rich patch (a bribe can only add, so the minimum is the
                  conservative reading); falls back to raw until one is seen.

WHAT THE AGENT IS NOT ALLOWED TO DO (owner's v12 constraint, msg_00141, inherited):
it does not falsify the signal and does not invent its own provenance. The payer tag
arrives in the OBSERVATION (`o["receipt"]`), issued by the world. The agent only
decides which part of its own receipt to believe.

Instrumentation (declared, prereg §4): `rate_at_first_decision` is recorded the
first time the frozen guard READS the statistic (which happens only once
`rich_steps >= MIN_OBS`), together with `first_decision_t`; `first_nodrain_t` is the
agent's own step counter at the first rich non-move receipt that did not drain.
"""
from agent_safety_v10 import AgentSafetyBase, SOCIAL_COST, MIN_OBS


class LedgerBase(AgentSafetyBase):
    """The frozen safety base with `rich_rate_obs` made a readable statistic."""

    IDENTIFIER_VERSION = "ledger v13 base"

    def __init__(self, seed=0):
        AgentSafetyBase.__init__(self, seed)
        self._raw_rate = 0.0
        self._stat_cache = 0.0
        # ---- ledger instrumentation (prereg §4)
        self.world_rich_receipt = 0.0     # world component on rich non-move steps
        self.foreign_rich_receipt = 0.0   # foreign component on the same steps
        self.foreign_steps_seen = 0
        self.nodrain_reward = 0.0
        self.nodrain_steps = 0
        self.min_rich_receipt = None
        self.first_nodrain_t = None
        self.rate_at_first_decision = None
        self.first_decision_t = None
        self.receipt_world_total = 0.0
        self.receipt_foreign_total = 0.0
        # DRAIN ATTRIBUTION (turn 143, declared; CORRECTED turn 144 against
        # measurement). v10 returns the observation it computed BEFORE its aquifer
        # hook drains, so the `commons` carried by the step's own returned
        # observation is the PRE-drain value. A step's own drain is therefore
        # visible only two calls later, as `commons[kk+2] < commons[kk+1]`.
        #
        # The first version compared the step's own o/o2 and was LAGGED BY ONE
        # STEP. My turn-143 comment here said it "classified 6 of 36 rich steps as
        # non-draining, exactly the wrong six". RE-MEASURED turn 144
        # (diag_ledger_lag_v13.py, 3 seeds x 2 arms, evidence in
        # results/diag_ledger_lag_v13.txt): the naive rule CALLS 6 of 36 steps
        # non-draining, but it DISAGREES with the correct rule on exactly ONE step
        # -- the step that drained the last unit (kk=38, commons 1 -> 0 -> 0).
        # So "the wrong six" was wrong: one step was misclassified, and it was the
        # one that decided whether the aquifer was counted dry. Corrected here
        # rather than left standing in a comment, which is where I found it.
        self._call = 0
        self._commons_hist = []
        self._pending = []                # (call_index, reward, receipt)

    # ------------- the ONE substitution: what the frozen number is worth
    def _stat_from_raw(self, raw):
        return raw

    @property
    def rich_rate_obs(self):
        stat = self._stat_from_raw(self._raw_rate)
        self._stat_cache = stat
        # the frozen guard reads this attribute only once `rich_steps >= MIN_OBS`
        # (short-circuit `and`), so this is the first harvest decision at which
        # the guard applies -- the declared instrumentation point.
        if self.rate_at_first_decision is None and \
                getattr(self, "rich_steps", 0) >= MIN_OBS:
            self.rate_at_first_decision = stat
            self.first_decision_t = self.t
        return stat

    @rich_rate_obs.setter
    def rich_rate_obs(self, value):
        self._raw_rate = value

    # ------------- the split, read from the observation (world-issued) -----
    def observe(self, o, a, r, o2, done, info):
        # the frozen observe runs FIRST and untouched (it assigns the raw rate)
        AgentSafetyBase.observe(self, o, a, r, o2, done, info)
        k = self._call
        self._call += 1
        self._commons_hist.append(o.get("commons"))
        # resolve the pending rich steps whose own drain is now observable
        still = []
        for (kk, rew, rec, at) in self._pending:
            if kk + 2 <= k:
                drained = (self._commons_hist[kk + 2] < self._commons_hist[kk + 1])
                self._classify(rew, rec, drained, at)
            else:
                still.append((kk, rew, rec, at))
        self._pending = still
        # the world's own tag for the step just taken
        rec = (o2 or {}).get("receipt")
        if rec is not None:
            self.receipt_world_total += rec.get("world", 0.0)
            self.receipt_foreign_total += rec.get("foreign", 0.0)
        f1 = self._feat(o)
        on_rich_nonmove = (a in ("wait", "press", "grasp") and f1["on_rich"])
        if rec is None or not on_rich_nonmove or r <= 0:
            return
        w = rec.get("world", 0.0)
        f = rec.get("foreign", 0.0)
        self.world_rich_receipt += w
        self.foreign_rich_receipt += f
        if f > 0:
            self.foreign_steps_seen += 1
        if self.min_rich_receipt is None or r < self.min_rich_receipt:
            self.min_rich_receipt = r
        # `self.t` is now k+1 (the frozen observe incremented it), so this step's
        # own agent-clock value is k+1.
        self._pending.append((k, r, dict(rec), k + 1))

    def _classify(self, reward, receipt, drained, agent_t):
        if not drained:
            self.nodrain_reward += reward
            self.nodrain_steps += 1
            if self.first_nodrain_t is None:
                self.first_nodrain_t = agent_t


class LNone(AgentSafetyBase):
    """No guard at all: v10's B0. Identity anchor."""
    IDENTIFIER_VERSION = "v13 identity: v10 s0_nobrake"


class LScalar(LedgerBase):
    """The frozen B4 arm, verbatim in behaviour (identity stat)."""
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "v13 scalar: the frozen B4 statistic (identity)"

    def _stat_from_raw(self, raw):
        return raw


class LLedger(LedgerBase):
    """The accounting layer: only the WORLD-attributed receipt is believed."""
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "v13 ledger: world-attributed receipt only"

    def _stat_from_raw(self, raw):
        if getattr(self, "rich_steps", 0) <= 0:
            return 0.0
        return self.world_rich_receipt / self.rich_steps


class LInfer(LedgerBase):
    """Tag-free attempt 1: calibrate on receipts from steps that did NOT drain."""
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "v13 tag-free: non-draining-step rate"

    def _stat_from_raw(self, raw):
        if self.nodrain_steps > 0:
            return self.nodrain_reward / self.nodrain_steps
        return raw


class LInferMin(LedgerBase):
    """Tag-free attempt 2: the minimum receipt ever seen on the rich patch."""
    SOCIAL_COST_ARM = SOCIAL_COST
    IDENTIFIER_VERSION = "v13 tag-free: minimum rich receipt"

    def _stat_from_raw(self, raw):
        if self.min_rich_receipt is not None:
            return self.min_rich_receipt
        return raw


ARMS = {
    "l_none": LNone,
    "l_scalar": LScalar,
    "l_ledger": LLedger,
    "l_infer": LInfer,
    "l_infer_min": LInferMin,
}


def make_agent(arm, seed):
    return ARMS[arm](seed)
