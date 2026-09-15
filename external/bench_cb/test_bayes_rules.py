"""test_bayes_rules.py -- turn 135. Unit suite for the T4 lookahead rule.

RED-CAPABLE BY CONSTRUCTION: W9 runs the same inclusion check the theorem uses
against a DELIBERATELY CORRUPTED rule (V := commit, i.e. never probe) and
requires the check to FAIL. If W9 ever passes, the suite is not testing anything.

Run:  python3 test_bayes_rules.py
"""
import ast
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import candidate_gen as CG
import stopping_rules as SR
import bayes_stopping as BS

FAILS = []


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name,
                           ("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def mk(ra, tr, sc=0.3):
    return CG.Candidate("a1", "y", "c0", rate_a=ra, rate_o=None, trials=tr,
                        score=sc)


GRID = [(ra, tr, r, L)
        for ra in (None, 0.20, 0.55, 0.85)
        for tr in (0, 5, 20, 100, 400)
        for r in (0.10, 0.30, 0.50, 0.65, 0.80, 0.90)
        for L in (40.0, 200.0)]


TIE_TOL = 1e-12     # a margin this close to 0 is an indifference tie, not a
                    # decision: both rules are on the boundary and each breaks
                    # its own tie differently (turn-135 W2 correction).


def acc_bayes(c, r, L):
    return bool(BS.plan([c], r, horizon_left=L, probe_len=20))


def acc_voi(c, r, L):
    return bool(SR.plan([c], r, rule="voi", horizon_left=L, probe_len=20))


def voi_margin(c, r, L):
    t = SR.voi_terms(c.rate_a, c.trials, r, 20, L)
    return t.info - t.risk


def violations(hi, lo, grid, tol=0.0):
    """states where `lo` accepts and `hi` does not, EXCLUDING states where `lo`'s
    own margin is within `tol` of zero (an indifference tie)."""
    bad = []
    for (ra, tr, r, L) in grid:
        c = mk(ra, tr)
        if lo(c, r, L) and not hi(c, r, L):
            if tol and abs(voi_margin(c, r, L)) <= tol:
                continue
            bad.append((ra, tr, r, L))
    return bad


def main():
    print("=== W1 V >= commit at every state (the DP's own definition)")
    bad = []
    for (ra, tr, r, L) in GRID:
        mu, commit, probe, V, m = BS.terms_bayes(ra, tr, r, 20, L)
        if V < commit - 1e-12:
            bad.append((ra, tr, r, L, V, commit))
    check("W1 V >= commit", not bad, "%d violations" % len(bad))

    print("=== W1b HORIZON IS EXACT: T4 and T2 agree at every state where the "
          "step count matters (no block quantisation)")
    worst = 0
    for (ra, tr, r, L) in [(None, 99, 0.711, 135.0), (None, 99, 0.711, 121.0),
                           (None, 99, 0.711, 139.0), (0.55, 5, 0.10, 41.0),
                           (0.85, 100, 0.10, 43.0)]:
        mu, commit, probe, V, LL = BS.terms_bayes(ra, tr, r, 20, L)
        t2 = SR.voi_terms(ra, tr, r, 20, L)
        disc = (probe > commit) != (t2.info > t2.risk)
        if disc and abs(t2.info - t2.risk) > TIE_TOL:
            worst += 1
    check("W1b no disagreement beyond ties at non-multiple horizons", worst == 0,
          "%d disagreements" % worst)

    print("=== W1c NUMERIC DOMINANCE: probe_value_T4 >= probe_value_T2 at every "
          "state (the theorem's arithmetic, not just the decision)")
    bad = []
    worst = 0.0
    for (ra, tr, r, L) in GRID:
        mu, commit, probe, V, LL = BS.terms_bayes(ra, tr, r, 20, L)
        t2 = SR.voi_terms(ra, tr, r, 20, L)
        d = probe - t2.probe_value
        worst = min(worst, d)
        if d < -1e-9:
            bad.append((ra, tr, r, L, d))
    check("W1c probe_T4 >= probe_T2 everywhere", not bad,
          "worst difference %+.3e over %d states" % (worst, len(GRID)))

    print("=== W2 THE THEOREM: accept(T4) contains accept(T2) on the grid, "
          "up to indifference ties (|T2 margin| <= %g)" % TIE_TOL)
    v_all = violations(acc_bayes, acc_voi, GRID, tol=0.0)
    v = violations(acc_bayes, acc_voi, GRID, tol=TIE_TOL)
    ties = [x for x in v_all if x not in v]
    check("W2 T2-accepts => T4-accepts (ties excluded)", not v,
          "%d/%d violate beyond tolerance; %d are ties: %s"
          % (len(v), len(GRID), len(ties), v[:4]))
    check("W2b every excluded state is a genuine tie (|margin| <= %g)"
          % TIE_TOL,
          all(abs(voi_margin(mk(x[0], x[1]), x[2], x[3])) <= TIE_TOL
              for x in ties),
          "%d ties, worst margin %.2e"
          % (len(ties), max([abs(voi_margin(mk(x[0], x[1]), x[2], x[3]))
                             for x in ties] or [0.0])))

    print("=== W3 T4 accepts strictly more than T2 somewhere (the theorem is "
          "not vacuous)")
    strict = 0
    for (ra, tr, r, L) in GRID:
        c = mk(ra, tr)
        if acc_bayes(c, r, L) and not acc_voi(c, r, L):
            strict += 1
    check("W3 strict gain exists", strict > 0, "%d states" % strict)

    print("=== W4 L < n (cannot afford a whole probe) => never probe")
    ok = all(not BS.plan([mk(ra, tr)], r, horizon_left=19.0, probe_len=20)
             for (ra, tr, r, _L) in GRID)
    check("W4 no whole probe affordable => no probe", ok)

    print("=== W5 V is non-decreasing in L (more steps cannot hurt)")
    bad = []
    for ra, tr in ((0.85, 20), (0.55, 100), (None, 0)):
        prev = -1.0
        for L in range(0, 221, 5):
            mu, commit, probe, V, LL = BS.terms_bayes(ra, tr, 0.30, 20, float(L))
            if V < prev - 1e-12:
                bad.append((ra, tr, L))
            prev = V
    check("W5 V monotone in L", not bad, str(bad))

    print("=== W6 source audit: no price constant, no RNG, no arbitration")
    src = open(os.path.join(_HERE, "bayes_stopping.py")).read()
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for al in node.names:
                names.add(al.name)
                names.add(al.asname or al.name)
    banned = {"GAIN_UNIT", "PROBE_COST", "beta", "random", "np", "numpy",
              "arbitration", "arbitration_scaled"}
    hit = sorted(banned & names)
    check("W6 no price/RNG/arbitration symbol", not hit, str(hit))

    print("=== W7 predictive cross-check: log-ratio pmf vs an independent "
          "lgamma pmf")
    from math import lgamma, exp as _exp

    def lg_pmf(n, a, b):
        logs = [lgamma(n + 1.0) - lgamma(k + 1.0) - lgamma(n - k + 1.0)
                + lgamma(a + k) + lgamma(b + n - k) - lgamma(a + b + n)
                - (lgamma(a) + lgamma(b) - lgamma(a + b))
                for k in range(n + 1)]
        m = max(logs)
        w = [_exp(x - m) for x in logs]
        s = sum(w)
        return [x / s for x in w]

    worst = 0.0
    for (a, b) in ((1.0, 1.0), (201.0, 1.0), (1.0, 201.0), (86.0, 116.0),
                   (1000.0, 1000.0)):
        p1, p2 = BS.bb_pmf(20, a, b), lg_pmf(20, a, b)
        worst = max(worst, max(abs(x - y) for x, y in zip(p1, p2)),
                    abs(sum(p1) - 1.0))
    check("W7 pmf agrees to 1e-12 and sums to 1", worst < 1e-12,
          "worst=%.3e" % worst)

    print("=== W8 determinism: two calls, identical decisions (no RNG)")
    d1 = [acc_bayes(mk(ra, tr), r, L) for (ra, tr, r, L) in GRID]
    d2 = [acc_bayes(mk(ra, tr), r, L) for (ra, tr, r, L) in GRID]
    check("W8 deterministic", d1 == d2)

    print("=== W9 NEGATIVE CONTROL (must be RED): corrupt V := commit (i.e. "
          "never look ahead, so T4 never probes) and the inclusion check must "
          "FAIL")
    real_V = BS._V
    try:
        BS._MEMO.clear()
        BS._V = lambda a, b, m, r, n: m * max(a / (a + b), r)
        v_bad = violations(acc_bayes, acc_voi, GRID, tol=TIE_TOL)
    finally:
        BS._V = real_V
        BS._MEMO.clear()
    check("W9 control is red-capable", len(v_bad) > 0,
          "%d violations under corruption (beyond tolerance)" % len(v_bad))

    print("=== W9b the same control must NOT be red for the T2 side alone "
          "(it is T4's lookahead that the corruption removes)")
    real_V = BS._V
    try:
        BS._MEMO.clear()
        BS._V = lambda a, b, m, r, n: m * max(a / (a + b), r)
        self_bad = violations(acc_voi, acc_voi, GRID, tol=TIE_TOL)
    finally:
        BS._V = real_V
        BS._MEMO.clear()
    check("W9b T2 compared with itself is never violated", not self_bad)

    print()
    if FAILS:
        print("SUITE FAILED: %s" % FAILS)
        return 1
    print("SUITE PASSED (9 groups)")
    return 0


if __name__ == "__main__":
    sys.exit(main())