r"""bayes_stopping.py -- turn 135. T4: the LOOKAHEAD stopping rule.

Owner directive msg_00135: option (C) -- spend one more cycle building a more
complex rule that computes the whole future ahead.

WHAT T2 WAS, AND WHAT IT MISSED
  T2 (`voi` in stopping_rules.py, turn 134) compares two complete strategies over
  the remaining horizon L: ACT NOW (L*max(mu, r)) against PROBE n steps THEN ACT
  (n*mu + (L-n)*E_k[max(post, r)]). It is a ONE-STEP lookahead: after the probe it
  assumes the agent commits to the better arm and never probes again.

  T4 solves the actual optimal stopping problem. After a probe the agent may probe
  AGAIN, or commit. V(a,b,L) is the value of the optimal policy from a Beta(a,b)
  posterior on the candidate's rate, an observed alternative rate r, and L STEPS
  left:

      V(a,b,L) = L*max(mu, r)                                  if L < n
      V(a,b,L) = max( L*max(mu, r) ,  n*mu + sum_k P(k;n,a,b)*V(a+k,b+n-k,L-n) )
        mu = a/(a+b)

  with P(k;n,a,b) the exact Beta-Binomial predictive of the next n pulls (closed
  form, no sampling, no RNG). The rule ACCEPTS a candidate iff the optimal policy
  PROBES at (a,b,L,r).

HORIZON IS EXACT IN STEPS -- AND THAT CORRECTION WAS FORCED BY A MEASUREMENT
  My first version quantised the horizon to whole probe blocks (m = floor(L/n))
  and treated the < n remainder as commit-only. I declared it as approximation A1
  "worth at most n-1 steps of horizon". THAT DECLARATION WAS WRONG, and the
  instrumented diagnostic caught it with a large margin, not a tie: at the state
  (rate_a=None, trials=99, r=0.711, L=135) T2 accepts (margin +4.8e-2) while the
  quantised T4 refused (margin -3.4e-1), because the quantised rule valued the same
  state as if only 120 steps were left -- it discarded 15 steps, and those 15 steps
  were worth more than the entire lookahead gain. A1 was therefore not an
  approximation of the rule; it was a DIFFERENT rule with a large error term.
  The DP now carries L exactly (a step count), so there is no block quantisation
  and no tail approximation at all. A1 is withdrawn.

CONSEQUENCE -- A THEOREM, NOT A HOPE (and the one place it needed correcting)
  Since V >= commit at every state,
      probe_value_T4 >= probe_value_T2   at every state,
  so T4's accept set CONTAINS T2's: T4 never probes less than T2 anywhere.

  HONEST CORRECTION (turn 135, caught by my own unit suite W2 before any matrix
  ran). The first statement of the theorem was "accept(T4) contains accept(T2)"
  as a set inclusion, and W2 FAILED on 7/240 grid states. The cause is NOT
  dominance. In those states the probe is exactly worthless (E_k[max(post,r)] ==
  max(mu,r) in exact arithmetic), so BOTH rules sit on the indifference point:
  T2's margin `info - risk` is +2.2e-15 (floating-point noise) while T4's margin
  `probe - commit` is exactly 0.0, and each breaks its own tie differently. A wide
  scan (diag_t4_inclusion.py, 2240 states) finds **0** violations with a T2 margin
  above 1e-12 and 111 ties (worst tie margin 8.4e-14), plus 138 states where T4
  strictly accepts and T2 does not. So the corrected claim is:

      accept(T4) contains accept(T2) UP TO INDIFFERENCE TIES,
      and is STRICTLY LARGER wherever the probe has positive expected value.

  The suite tests the corrected claim (tolerance declared in the test) and the
  negative control (W9) still breaks it.

DECLARED QUANTITIES: n (steps in one probe -- asserted by the caller to be the
campaign's own PROBE_BLOCK), L = STEPS REMAINING (observed by the agent), prior
Beta(1,1) (a COUNT), r (observed). NO GAIN_UNIT, NO beta, NO PROBE_COST.

DECLARED APPROXIMATIONS (written before the run)
  A2 THE ALTERNATIVE IS A POINT. r enters as the observed best rate, not as a
     posterior (inherited from T2 / turn-134 prereg L4).
  A3 ONE CANDIDATE AT A TIME. The DP values this candidate against the observed
     alternative only; it does not model the other candidates competing for the
     same steps. Same scope as T2, so the comparison is like-for-like.
  A4 THE OBJECTIVE IS THE CANDIDATE'S OWN REWARD, not the episode's policy
     regret. The DP is optimal for "should I spend steps learning this
     candidate's rate"; the agent's regret is over contexts. The gap between the
     two is what the matrix measures, not something this module assumes away.
  A5 MEMO CAP. The DP memo is shared across the whole matrix and cleared when it
     exceeds MEMO_CAP entries; clearing costs time, never correctness.

WHAT THIS MODULE DOES NOT DO
  Reads no world constant, contains no world token, touches no model, and edits
  nothing: candidate_gen.py, arbitration.py, arbitration_scaled.py,
  stopping_rules.py, union_agent_v2.py and union_agent_v3.py stay byte-identical
  (hashes re-verified in the report).
"""
from math import exp, log

from stopping_rules import (posterior, PRIOR_A, PRIOR_B, PROBE_LEN_DEFAULT)

HORIZON_DEFAULT = 200.0      # fallback only when the caller cannot supply L
MEMO_CAP = 800000

_MEMO = {}
_PMF_CACHE = {}


# --------------------------------------------------------------- predictive --
def bb_pmf(n, a, b):
    """Exact Beta-Binomial predictive pmf over k = 0..n, by a log-ratio
    recursion (no overflow, deterministic, no RNG)."""
    key = (n, round(a, 6), round(b, 6))
    v = _PMF_CACHE.get(key)
    if v is not None:
        return v
    lw = [0.0] * (n + 1)
    for k in range(n):
        lw[k + 1] = (lw[k] + log(a + k) + log(n - k)
                     - log(b + n - k - 1) - log(k + 1))
    mx = max(lw)
    w = [exp(x - mx) for x in lw]
    s = sum(w)
    out = [x / s for x in w]
    _PMF_CACHE[key] = out
    return out


# ------------------------------------------------------------ the DP itself --
def _V(a, b, m, r, n):
    """Value of the optimal policy with `m` STEPS left (exact step count)."""
    if m <= 0:
        return 0.0
    key = (round(a, 6), round(b, 6), m, r, n)
    v = _MEMO.get(key)
    if v is not None:
        return v
    mu = a / (a + b)
    commit = m * (mu if mu > r else r)
    if m < n:
        v = commit                      # cannot afford a whole probe
    else:
        pmf = bb_pmf(n, a, b)
        s = 0.0
        for k in range(n + 1):
            pk = pmf[k]
            if pk:
                s += pk * _V(a + k, b + n - k, m - n, r, n)
        probe = n * mu + s
        v = probe if probe > commit else commit
    if len(_MEMO) >= MEMO_CAP:
        _MEMO.clear()
    _MEMO[key] = v
    return v


def terms_bayes(rate_a, trials, r_best, probe_len=PROBE_LEN_DEFAULT,
                horizon_left=HORIZON_DEFAULT, prior=(PRIOR_A, PRIOR_B)):
    """The arithmetic of T4 for one candidate, in reward units over the SAME
    exact remaining-steps horizon T2 uses: (mu, commit, probe_value, V, L)."""
    n = int(probe_len)
    L = int(float(horizon_left))
    r = float(r_best)
    a, b = posterior(rate_a, trials, prior)
    mu = a / (a + b)
    commit = L * (mu if mu > r else r)
    if L < n:
        return mu, commit, commit, commit, L
    pmf = bb_pmf(n, a, b)
    s = 0.0
    for k in range(n + 1):
        pk = pmf[k]
        if pk:
            s += pk * _V(a + k, b + n - k, L - n, r, n)
    probe = n * mu + s
    return mu, commit, probe, (probe if probe > commit else commit), L


# --------------------------------------------------------------- the rule ----
def plan(cands, r_best, horizon_left=None, probe_len=PROBE_LEN_DEFAULT,
         prior=(PRIOR_A, PRIOR_B), **kw):
    """Same call shape as stopping_rules.plan / arbitration.plan: the candidates
    the rule ACCEPTS, in the incoming ranked order. The rule swaps only the
    accept/reject decision, never the ranking."""
    n = int(probe_len)
    L = int(float(horizon_left if horizon_left is not None else HORIZON_DEFAULT))
    out = []
    if L < n:
        return out
    r = float(r_best)
    for c in cands:
        a, b = posterior(c.rate_a, c.trials, prior)
        mu = a / (a + b)
        commit = L * (mu if mu > r else r)
        if _V(a, b, L, r, n) > commit:
            out.append(c)
    return out


def explain(cands, r_best, horizon_left=None, probe_len=PROBE_LEN_DEFAULT,
            prior=(PRIOR_A, PRIOR_B)):
    """Per-candidate arithmetic, for the report and the verifier: a refusal comes
    with the numbers that produced it."""
    n = int(probe_len)
    L = int(float(horizon_left if horizon_left is not None else HORIZON_DEFAULT))
    r = float(r_best)
    out = []
    for c in cands:
        mu, commit, probe, V, LL = terms_bayes(c.rate_a, c.trials, r, n, L,
                                               prior)
        a, b = posterior(c.rate_a, c.trials, prior)
        out.append({"action": c.action, "score": c.score, "rate_a": c.rate_a,
                    "trials": c.trials, "a": round(a, 4), "b": round(b, 4),
                    "mu": round(mu, 6), "r": round(r, 6), "L": LL,
                    "commit": round(commit, 6), "probe_value": round(probe, 6),
                    "V": round(V, 6), "probe": bool(probe > commit)})
    return out


def cutoff_bayes(rate_a, trials, probe_len=PROBE_LEN_DEFAULT,
                 horizon_left=HORIZON_DEFAULT, prior=(PRIOR_A, PRIOR_B),
                 lo=0.0, hi=1.0, iters=60):
    """The alternative rate at which T4 goes silent for this record, by bisection
    on (probe_value - commit). The single-candidate analogue of the frozen rule's
    silence level, derived from the DP's own arithmetic."""
    def f(r):
        mu, commit, probe, _V_, _L = terms_bayes(rate_a, trials, r, probe_len,
                                                 horizon_left, prior)
        return probe - commit
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


def stats():
    return {"memo": len(_MEMO), "pmf_cache": len(_PMF_CACHE)}


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import candidate_gen as CG
    import stopping_rules as SR

    def C(ra, tr, sc=0.3):
        return CG.Candidate("a1", "y", "c0", rate_a=ra, rate_o=None, trials=tr,
                            score=sc)

    print("declared: n=%d prior=(%.0f,%.0f) horizon_default=%.0f  (horizon is "
          "EXACT steps: no block quantisation)"
          % (PROBE_LEN_DEFAULT, PRIOR_A, PRIOR_B, HORIZON_DEFAULT))

    print("\n(1) ONE CANDIDATE vs AN ALTERNATIVE, L=200, n=20")
    print("    rate  trials  mu      commit   probe_T4  probe_T2  T4  T2")
    for ra, tr in ((0.85, 200), (0.85, 20), (0.55, 200), (0.55, 5), (None, 0)):
        c = C(ra, tr)
        mu, commit, probe, V, L = terms_bayes(ra, tr, 0.30, 20, 200.0)
        t2 = SR.voi_terms(ra, tr, 0.30, 20, 200.0)
        print("    %-5s %6d  %.3f  %7.3f  %8.3f  %8.3f  %-3s %-3s"
              % (ra, tr, mu, commit, probe, t2.probe_value,
                 "yes" if probe > commit else "no",
                 "yes" if t2.info > t2.risk else "no"))

    print("\n(2) THE CORRECTED STATE (the one the quantised version got wrong):")
    print("    rate=None tr=99 r=0.711  -- T4 must now agree with T2 at L=135")
    for L in (120.0, 135.0, 140.0):
        mu, commit, probe, V, LL = terms_bayes(None, 99, 0.711, 20, L)
        t2 = SR.voi_terms(None, 99, 0.711, 20, L)
        print("      L=%-5.0f  T2 margin=%+.4f (%s)   T4 margin=%+.4f (%s)"
              % (L, t2.info - t2.risk, t2.info > t2.risk, probe - commit,
                 probe > commit))

    print("\n(3) SILENCE LEVELS as the alternative gets richer (rate 0.85,"
          " trials 200, L=400):")
    cs = [C(0.85, 200)]
    for name, fn in (("frozen", lambda r: bool(SR.plan(cs, r, rule="frozen",
                                                       horizon_left=400.0,
                                                       probe_len=20))),
                     ("voi   ", lambda r: bool(SR.plan(cs, r, rule="voi",
                                                       horizon_left=400.0,
                                                       probe_len=20))),
                     ("conf  ", lambda r: bool(SR.plan(cs, r, rule="conf",
                                                       horizon_left=400.0,
                                                       probe_len=20))),
                     ("bayes ", lambda r: bool(plan(cs, r, horizon_left=400.0,
                                                    probe_len=20)))):
        row = ["yes" if fn(r) else "no " for r in
               (0.10, 0.30, 0.50, 0.65, 0.80, 0.90)]
        print("    %s  %s" % (name, "   ".join(row)))

    print("\n(4) THEOREM CHECK: T4 accepts wherever T2 accepts (grid, ties "
          "excluded at 1e-12):")
    bad, ties, n_acc = [], 0, 0
    for ra in (None, 0.20, 0.55, 0.85):
        for tr in (0, 5, 20, 100, 400):
            for r in (0.10, 0.30, 0.50, 0.65, 0.80, 0.90):
                for L in (40.0, 200.0):
                    c = C(ra, tr)
                    t2m = SR.voi_terms(ra, tr, r, 20, L)
                    t2 = t2m.info > t2m.risk
                    mu, commit, probe, V, LL = terms_bayes(ra, tr, r, 20, L)
                    t4 = probe > commit
                    n_acc += t4
                    if t2 and not t4:
                        if abs(t2m.info - t2m.risk) <= 1e-12:
                            ties += 1
                        else:
                            bad.append((ra, tr, r, L))
    print("    states=240  T4 accepts %d  REAL violations: %d  ties: %d  -> %s"
          % (n_acc, len(bad), ties, "PASS" if not bad else "FAIL %s" % bad[:4]))

    print("\nself-check: bb_pmf(20,1,1) sums to %.12f; bb_pmf(20,201,1)[0..3]="
          % sum(bb_pmf(20, 1.0, 1.0)))
    print("    %s" % [round(x, 6) for x in bb_pmf(20, 201.0, 1.0)[:4]])
    print("memo stats: %s" % stats())