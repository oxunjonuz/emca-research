r"""stopping_rules.py -- turn 134. A DIFFERENT TYPE of stopping rule.

OWNER'S INSTRUCTION (msg_00134): do not tune the current price; design a
fundamentally different type of rule that does not directly compare quantities
incommensurable by nature (probability vs reward).

STEP 0 -- WHAT THE OLD RULE ACTUALLY COMPARES (read off the code, not the prose)
-------------------------------------------------------------------------------
Frozen rule (arbitration.py sha 2d3d825b..., corrected sibling
arbitration_scaled.py):

    probe  iff  beta * GAIN_UNIT * score  >  rich_rate * PROBE_LEN + PROBE_COST

In BOTH engines this campaign has run the fields fed to that rule are REWARD
rates (the union agent keys candidate_gen on the observed reward "y"), so the
two sides are (gap x GAIN_UNIT) vs (rate x PROBE_LEN + cost). The
incommensurability is real and sits one level down: GAIN_UNIT is a declared
VALUE per unit gap, PROBE_LEN a declared DURATION. The verdict is therefore
fixed by two declared constants of DIFFERENT KINDS, neither derivable from the
world. Turn 132 measured the consequence -- the maskr verdict flips between
GAIN_UNIT 200 and 400 with no world change.

THE REPLACEMENT. Three types, one idea each.

T3  DECISION-CONFIDENCE STOPPING  (`conf`) -- probability compared with
    probability, reward magnitude absent.
        probe iff q_lo < P(rate_cand > rate_alt) < q_hi.
    Both quantities are probabilities. Nothing is converted into anything.

T2  ONE-CURRENCY VALUE OF INFORMATION  (`voi`) -- reward compared with reward.
    The agent holds a Beta posterior on the candidate's rate and an observed
    best rate r_best for the alternative (its own reward stream). Two complete
    strategies over the SAME remaining horizon L:

      (a) ACT NOW  (take the better of the two, on current beliefs)
              exploit = L * max(mu_c, r_best)
      (b) PROBE n steps on the candidate, then act
              probe   = n * mu_c + (L - n) * E_k[ max(mu_c^post, r_best) ]

        probe iff probe > exploit
        <=>      (L - n) * ( E_k[max(mu_c^post, r_best)] - max(mu_c, r_best) )
                 >  n * ( max(mu_c, r_best) - mu_c )
        <=>              INFORMATION  >  PAYOFF FORGONE WHILE GATHERING IT

    Both sides are REWARD TOTALS over the same L steps. There is no value-per-
    gap constant and no price constant: the exchange between evidence and reward
    happens inside the expectation, in the world's own currency. mu_c and its
    update come from the agent's OWN counts (Beta(a1+h, b1+n-h)); E_k integrates
    the exact Beta-Binomial predictive of n further pulls, in closed form and
    without sampling, so the rule is deterministic and cannot leak an RNG stream.

T2b the horizon-free reading of the same inequality (info per step vs risk per
    step) is available as `voi_rate` for readers who dislike the horizon.

T1  the frozen threshold rule, imported unchanged, as the thing replaced, beside
    the controls `nocost` (probe every nomination), `never` (probe nothing) and
    `beta0` (the frozen rule's own C1 control).

DECLARED QUANTITIES IN T2/T3 (and why this is a different kind of declaration)
-----------------------------------------------------------------------------
  probe_len -- STEPS: how many pulls a probe costs. Asserted by the caller to be
               the campaign's own PROBE_BLOCK, so it is measured, not chosen.
  horizon   -- STEPS REMAINING in the episode, which the agent OBSERVES. Not a
               valuation device: it says how long the answer will be used.
  prior     -- Beta(1,1): a COUNT (one pseudo-success, one pseudo-failure).
  q_lo,q_hi -- a confidence level in [0,1].
None of these converts probability into reward. In particular there is NO
GAIN_UNIT, NO beta, NO PROBE_COST.

SO WHAT *DOES* MOVE THE VERDICT? -- measured, not hidden
--------------------------------------------------------
Both rules move with their declared numbers; the question is what those numbers
mean. `horizon` says how long the answer will be acted on: change it and the
answer really does change for any decision-maker, in the world. `GAIN_UNIT` says
how many reward units one success is worth: change it and the verdict moves with
NOTHING about the world changed, which is only defensible if the agent is handed
an arbitrary utility scale it can never check. diag_sensitivity.py measures the
two sensitivities side by side so the difference is a number, not a claim.

HONEST LIMITS, DECLARED BEFORE THE RUN
--------------------------------------
L1  ONE-STEP LOOKAHEAD. No probe is valued for enabling a LATER probe and no
    sequence is planned: myopic against the Bayes-optimal dynamic program over
    beliefs. `nocost` is kept as the opposite extreme so the size of that gap is
    visible rather than assumed away.
L2  PLUG-IN DECISION. After the probe the larger posterior mean is taken; the
    full posterior over decisions is not integrated.
L3  THIN CANDIDATES (rate_a is None: never resolved in that context) have no
    record, so their posterior is the prior. Consequence, and it is a REAL one:
    a prior-only candidate cannot promise enough to beat a rich alternative, so
    T2 refuses it. That refusal is derived arithmetic, not a declared bar -- and
    it is reported as a finding (the rule is silent in rich worlds for a
    different reason than the frozen rule was).
L4  THE COMPARATOR IS A POINT. r_best enters as the observed rate of the best
    resolved arm, treated as known. A Beta posterior on the alternative would
    widen the interval; the point version is the declared approximation.
L5  THE BRIDGE IS STILL A BRIDGE. "The candidate's rate could be higher than the
    best known rate" IS the assumption -- stated openly here, as a probability
    over rates, rather than buried in a currency constant. It can be wrong and it
    can be tested (the rule's own silence points are checked against the
    instance's true arithmetic in the report).

WHAT THIS MODULE DOES NOT DO
----------------------------
Reads no world constant, contains no world token, never touches
model.expected_rewards, and edits nothing: candidate_gen.py, arbitration.py,
arbitration_scaled.py, union_agent_v2.py and union_instance.py stay
byte-identical to turn 132 (hashes re-verified in the report).
"""
from collections import namedtuple
from math import lgamma, exp, log

PROBE_LEN_DEFAULT = 20       # = union_agent_v2.PROBE_BLOCK (caller asserts)
HORIZON_DEFAULT = 200.0      # fallback only when the caller cannot supply L
PRIOR_A = 1.0                # Beta(1,1) prior on a reward rate (a COUNT)
PRIOR_B = 1.0
Q_LO = 0.05                  # T3: probe only while the comparison is open
Q_HI = 0.95
N_GRID = 1500                # Simpson grid for T3 (deterministic)

Terms = namedtuple("Terms", "mu_c cur info risk exploit probe_value gap "
                            "evsi_per_step horizon")


# ------------------------------------------------------------- beta helpers --
def _lbeta(a, b):
    return lgamma(a) + lgamma(b) - lgamma(a + b)


def _betacf(a, b, x):
    """Continued fraction for the incomplete beta function (Lentz)."""
    tiny, eps = 1e-30, 3e-14
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def betainc_reg(a, b, x):
    """Regularised incomplete beta I_x(a,b). Deterministic, no scipy."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    if x < (a + 1.0) / (a + b + 2.0):
        return exp(a * log(x) + b * log(1.0 - x) - _lbeta(a, b)) \
            * _betacf(a, b, x) / a
    return 1.0 - exp(b * log(1.0 - x) + a * log(x) - _lbeta(b, a)) \
        * _betacf(b, a, 1.0 - x) / b


def p_greater_beta(a1, b1, a2, b2, n_grid=N_GRID):
    """P(X > Y) for independent X~Beta(a1,b1), Y~Beta(a2,b2): Simpson on the
    density of X times the CDF of Y. Deterministic."""
    h = 1.0 / n_grid
    tot = 0.0
    for i in range(1, n_grid):
        x = i * h
        dens = exp((a1 - 1.0) * log(x) + (b1 - 1.0) * log(1.0 - x)
                   - _lbeta(a1, b1))
        tot += (4.0 if i % 2 else 2.0) * dens * betainc_reg(a2, b2, x)
    return min(max(tot * h / 3.0, 0.0), 1.0)


def posterior(rate, trials, prior=(PRIOR_A, PRIOR_B)):
    """Beta posterior on a reward RATE from the agent's own counts.
    rate is None or trials is 0 -> the declared prior stands (L3)."""
    a0, b0 = prior
    if rate is None or not trials:
        return float(a0), float(b0)
    n = float(trials)
    return a0 + float(rate) * n, b0 + n - float(rate) * n


def _log_betabinom_pmf(k, n, a, b):
    return (lgamma(n + 1.0) - lgamma(k + 1.0) - lgamma(n - k + 1.0)
            + lgamma(a + k) + lgamma(b + n - k) - lgamma(a + b + n)
            - (lgamma(a) + lgamma(b) - lgamma(a + b)))


def betabinom_pmf(n, a, b):
    """Normalised Beta-Binomial predictive pmf over k = 0..n (whole n only)."""
    n = int(n)
    if n < 0:
        raise ValueError("probe_len must be a non-negative whole number")
    logs = [_log_betabinom_pmf(k, n, a, b) for k in range(n + 1)]
    m = max(logs)
    w = [exp(x - m) for x in logs]
    z = sum(w)
    return [x / z for x in w]


# --------------------------------------------------- T2: the one-currency rule
def voi_terms(rate_a, trials, r_best, probe_len=PROBE_LEN_DEFAULT,
              horizon=HORIZON_DEFAULT, prior=(PRIOR_A, PRIOR_B)):
    """The arithmetic of T2, in reward units over the same horizon L.

    returns Terms with
      mu_c        -- the candidate's posterior mean RATE on current evidence
      cur         -- max(mu_c, r_best): the rate the agent would act on NOW
      info        -- (L-n) * (E_k[max(post, r_best)] - cur)   >= 0
      risk        -- n * (cur - mu_c)                        >= 0
      exploit     -- L * cur                     (reward if it acts now)
      probe_value -- n*mu_c + (L-n)*E_k[max(post, r_best)]
      evsi_per_step - (E_k[max(...)] - cur)
    probe iff info > risk  (equivalently probe_value > exploit)."""
    L, n = float(horizon), int(probe_len)
    r = float(r_best)
    a1, b1 = posterior(rate_a, trials, prior)
    mu_c = a1 / (a1 + b1)
    cur = max(mu_c, r)
    if n <= 0 or L <= n:
        emax = cur
    else:
        pmf = betabinom_pmf(n, a1, b1)
        emax = 0.0
        for k in range(n + 1):
            post = (a1 + k) / (a1 + b1 + n)
            emax += pmf[k] * max(r, post)
    info = (L - n) * (emax - cur) if L > n else 0.0
    risk = n * (cur - mu_c)
    probe_value = n * mu_c + (L - n) * emax if L > n else n * mu_c
    gap = mu_c - r
    return Terms(mu_c=mu_c, cur=cur, info=info, risk=risk, exploit=L * cur,
                 probe_value=probe_value, gap=gap,
                 evsi_per_step=emax - cur, horizon=L)


def _voi(cands, r_best, horizon_left=None, probe_len=PROBE_LEN_DEFAULT,
         prior=(PRIOR_A, PRIOR_B), **kw):
    if horizon_left is None:
        horizon_left = HORIZON_DEFAULT
    out = []
    for c in cands:
        t = voi_terms(c.rate_a, c.trials, r_best, int(probe_len),
                      horizon_left, prior)
        if t.info > t.risk:
            out.append(c)
    return out


def _voi_rate(cands, r_best, probe_len=PROBE_LEN_DEFAULT,
              prior=(PRIOR_A, PRIOR_B), ratio_min=1.0, **kw):
    """T2b, horizon-free: information per step vs risk per step, with the same
    arithmetic (no horizon anywhere)."""
    out = []
    for c in cands:
        t = voi_terms(c.rate_a, c.trials, r_best, int(probe_len), 1e9, prior)
        if t.evsi_per_step * ratio_min > (t.cur - t.mu_c):
            out.append(c)
    return out


# ------------------------------------------------ T3: probability-only rule --
def _conf(cands, r_best, q_lo=Q_LO, q_hi=Q_HI, prior=(PRIOR_A, PRIOR_B),
          n_grid=N_GRID, **kw):
    """T3: probe while the candidate-vs-competitor RATE comparison is OPEN.
    Rate is compared with rate; the reward magnitude never enters."""
    out = []
    for c in cands:
        a1, b1 = posterior(c.rate_a, c.trials, prior)
        if c.rate_a is None or not c.trials:
            p = 0.5                                   # nothing decided (L3)
        else:
            p = 1.0 - betainc_reg(a1, b1, float(r_best))
        if q_lo < p < q_hi:
            out.append(c)
    return out


# --------------------------------------------------------- T1 and controls --
def _frozen(cands, r_best, beta=1.0, **kw):
    """The campaign's threshold rule, DELEGATED to the module actually used on
    turn 132 -- so `frozen` here IS that rule, not a lookalike. `beta` is passed
    THROUGH (turn-134 defect fix: the first version hardcoded beta=1.0, which
    made the `beta0` control silently identical to `frozen_rule`; the G5 control
    caught it -- beta0 probed 3.43 instead of 0)."""
    import arbitration_scaled as AS
    return list(AS.plan(cands, r_best, beta=beta).probe_order)


def _beta0(cands, r_best, **kw):
    import arbitration_scaled as AS
    return list(AS.plan(cands, r_best, beta=0.0).probe_order)


def _nocost(cands, r_best, **kw):
    return list(cands)


def _never(cands, r_best, **kw):
    return []


RULES = {"frozen": _frozen, "beta0": _beta0, "nocost": _nocost,
         "never": _never, "voi": _voi, "voi_rate": _voi_rate, "conf": _conf}

THRESHOLD_RULES = ("frozen", "beta0")        # a declared bar on a score
ONE_CURRENCY_RULES = ("voi", "voi_rate")     # reward vs reward
PROBABILITY_ONLY_RULES = ("conf",)           # probability vs probability


def plan(cands, r_best, horizon_left=None, probe_len=PROBE_LEN_DEFAULT,
         rule="voi", prior=(PRIOR_A, PRIOR_B), **kw):
    """Same call shape as arbitration(_scaled).plan: the candidates the rule
    ACCEPTS, in the incoming ranked order. The rule swaps only the accept/reject
    decision, never the ranking -- declared, so the measurement isolates the
    stopping rule from the nomination order."""
    return RULES[rule](list(cands), r_best, horizon_left=horizon_left,
                       probe_len=probe_len, prior=prior, **kw)


def explain(cands, r_best, horizon_left=None, probe_len=PROBE_LEN_DEFAULT,
            prior=(PRIOR_A, PRIOR_B)):
    """Per-candidate arithmetic, for the report and the verifier: a refusal comes
    with the numbers that produced it -- which the frozen rule's 'score below a
    declared bar' cannot do."""
    if horizon_left is None:
        horizon_left = HORIZON_DEFAULT
    out = []
    for c in cands:
        t = voi_terms(c.rate_a, c.trials, r_best, int(probe_len), horizon_left,
                      prior)
        out.append({"action": c.action, "score": c.score, "rate_a": c.rate_a,
                    "trials": c.trials, "mu_c": round(t.mu_c, 6),
                    "r_best": round(float(r_best), 6),
                    "cur": round(t.cur, 6), "info": round(t.info, 6),
                    "risk": round(t.risk, 6), "gap": round(t.gap, 6),
                    "probe": bool(t.info > t.risk),
                    "probe_value": round(t.probe_value, 6),
                    "exploit": round(t.exploit, 6),
                    "horizon": round(t.horizon, 3)})
    return out


def cutoff_voi(rate_a, trials, probe_len=PROBE_LEN_DEFAULT,
               horizon_left=HORIZON_DEFAULT, prior=(PRIOR_A, PRIOR_B),
               lo=0.0, hi=1.0, iters=60):
    """The r_best at which T2 goes silent for a candidate with this record, by
    bisection on (info - risk). The single-candidate analogue of the frozen
    rule's silence level, derived from the rule's own arithmetic."""
    def f(r):
        t = voi_terms(rate_a, trials, r, int(probe_len), horizon_left, prior)
        return t.info - t.risk
    if f(lo) <= 0.0:
        return lo
    if f(hi) > 0.0:
        return hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def cutoff_conf(rate_a, trials, q_lo=Q_LO, q_hi=Q_HI,
                prior=(PRIOR_A, PRIOR_B), iters=80):
    """The OPEN BAND of T3 for this record, as (r_hi, r_lo): p(r) is decreasing
    in the comparator rate r, so T3 probes exactly for r in (r_hi, r_lo) where
    p(r) = q_hi and p(r) = q_lo respectively. Bisection on a decreasing
    function -- the comparator rate is compared with rates, never with a price."""
    a1, b1 = posterior(rate_a, trials, prior)

    def p(r):
        return 1.0 - betainc_reg(a1, b1, min(max(r, 1e-12), 1.0 - 1e-12))

    def root(target):
        """the r with p(r) = target (p decreasing), or None if never crossed."""
        if not (p(0.0) >= target >= p(1.0)):
            return None
        lo, hi = 0.0, 1.0
        for _ in range(iters):
            mid = 0.5 * (lo + hi)
            if p(mid) > target:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    return root(q_hi), root(q_lo)


def cutoff_frozen(gain_unit=200.0, probe_len=20.0, probe_cost=4.0):
    """The frozen rule's silence level: GAIN_UNIT*(1-r) = r*PROBE_LEN + cost."""
    return (gain_unit - probe_cost) / (gain_unit + probe_len)


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import candidate_gen as CG
    import arbitration_scaled as AS

    def C(ra, ro, n, sc):
        return CG.Candidate("a1", "y", "c0", rate_a=ra, rate_o=ro, trials=n,
                            score=sc)

    print("declared: PROBE_LEN=%d HORIZON=%.0f prior=(%.0f,%.0f) q=(%.2f,%.2f)"
          % (PROBE_LEN_DEFAULT, HORIZON_DEFAULT, PRIOR_A, PRIOR_B, Q_LO, Q_HI))

    print("\n(1) THE SAME CANDIDATE, SEEN WITH DIFFERENT EVIDENCE "
          "(rate 0.55, alt 0.30, L=200, n=20):")
    print("    trials   mu_c    info     risk    frozen  voi   conf")
    for tr in (0, 5, 20, 100, 400, 2000):
        c = C(0.55, None, tr, 0.25) if tr else C(None, None, 0, 1.0)
        t = voi_terms(c.rate_a, c.trials, 0.30, 20, 200.0)
        old = AS.GAIN_UNIT
        try:
            f = bool(AS.plan([c], 0.30, beta=1.0).probe_order)
        finally:
            AS.GAIN_UNIT = old
        print("    %6d  %.3f  %7.3f  %6.3f   %-6s  %-5s %-5s"
              % (tr, t.mu_c, t.info, t.risk, f, bool(_voi([c], 0.30)),
                 bool(_conf([c], 0.30))))

    print("\n(2) SILENCE LEVELS as the alternative gets richer (alt rate):")
    print("    rule       0.10   0.30   0.50   0.65   0.80   0.90")
    cs = [C(0.85, None, 200, 0.55)]
    for name, fn in (("frozen  ", lambda r: _frozen(cs, r)),
                     ("voi     ", lambda r: _voi(cs, r)),
                     ("voi_rate", lambda r: _voi_rate(cs, r)),
                     ("conf    ", lambda r: _conf(cs, r))):
        row = ["yes" if fn(r) else "no " for r in
               (0.10, 0.30, 0.50, 0.65, 0.80, 0.90)]
        print("    %s  %s" % (name, "   ".join(row)))

    print("\n(3) which DECLARED number moves the verdict (same candidate, "
          "alt 0.30):")
    row = []
    for gu in (100.0, 200.0, 400.0, 800.0):
        old = AS.GAIN_UNIT
        AS.GAIN_UNIT = gu
        try:
            row.append("yes" if AS.plan(cs, 0.30, beta=1.0).probe_order else "no ")
        finally:
            AS.GAIN_UNIT = old
    print("    frozen: GAIN_UNIT 100/200/400/800 -> %s" % "  ".join(row))
    row = ["yes" if _voi(cs, 0.30, horizon_left=L) else "no "
           for L in (100.0, 200.0, 400.0, 800.0)]
    print("    voi   : horizon   100/200/400/800 -> %s  (= remaining STEPS)"
          % "  ".join(row))
    row = ["yes" if _voi(cs, 0.30, probe_len=n) else "no " for n in (5, 20, 40)]
    print("    voi   : probe_len     5/20/40      -> %s  (= PROBE_BLOCK)"
          % "  ".join(row))
    print("    conf  : none of the above         -> probability-only rule")

    print("\n(4) WHERE T2 GOES SILENT, by bisection (L=200, n=20):")
    for ra, tr in ((0.85, 200), (0.55, 200), (0.85, 20), (0.55, 5), (None, 0)):
        print("    rate=%-5s trials=%-5s -> silence at alt rate %.4f"
              % (ra, tr, cutoff_voi(ra, tr)))
    print("    frozen rule's silence level (GU=200, PL=20, c=4): %.4f"
          % cutoff_frozen())
    print("    T3 open band for rate 0.55, trials 200: alt in (%.4f, %.4f)"
          % cutoff_conf(0.55, 200))

    print("\nself-check: evsi arithmetic identity  info = (L-n)*(emax-cur), "
          "risk = n*(cur-mu)")
    t = voi_terms(0.85, 200, 0.30, 20, 200.0)
    print("    candidate 0.85/200 vs 0.30, L=200, n=20: mu=%.4f cur=%.4f "
          "info=%.4f risk=%.4f probe_value=%.4f exploit=%.4f -> probe=%s"
          % (t.mu_c, t.cur, t.info, t.risk, t.probe_value, t.exploit,
             t.info > t.risk))
    print("self-check: betainc_reg(2,2,0.5)=%.6f  p_greater_beta(31,21,31,21)"
          "=%.6f" % (betainc_reg(2.0, 2.0, 0.5),
                     p_greater_beta(31.0, 21.0, 31.0, 21.0)))
    print("self-check: betabinom_pmf(20,1,1) sums to %.12f"
          % sum(betabinom_pmf(20, 1.0, 1.0)))
