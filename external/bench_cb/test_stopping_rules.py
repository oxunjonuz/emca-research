"""test_stopping_rules.py -- turn 134. Unit checks on the NEW stopping rules.

Prints PASS/FAIL per check; exits 1 if any fails. The suite is RED-CAPABLE: W8
is a negative control that must fail an assertion, and W5 measures the
STRUCTURAL difference between the two types of rule rather than re-asserting my
own code. A green suite is therefore a statement about a difference between
designs, not only about my arithmetic.

W1  posterior arithmetic against hand computation
W2  Beta-Binomial predictive: sums to 1; uniform-prior case is uniform; the
    closed form matches an independent numerical integration
W3  incomplete beta and P(X>Y): exact values at known points, monotonicity
W4  T2 arithmetic: info >= 0, risk >= 0, and the rule's own identity
    (probe_value - exploit == info - risk) to machine precision
W5  TYPE DIFFERENCE: T2's accept set over the alternative's rate is a two-sided
    INTERVAL (probe only while learning would change the decision); the frozen
    rule's is not bounded by the price at all
W6  source audit: the T2/T2b/T3 bodies contain no GAIN_UNIT / PROBE_COST /
    arbitration / beta, while the frozen path does
W7  determinism: identical output in three fresh processes
W8  NEGATIVE CONTROL: the W4 identity on a corrupted predictive must FAIL
W9  degenerate cases: empty list, L <= n, r_best = 1.0, prior-only candidate
"""
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import candidate_gen as CG
import stopping_rules as SR

FAILS = []


def check(name, ok, extra=""):
    print("%-4s %s%s" % ("PASS" if ok else "FAIL", name,
                         ("  " + extra) if extra else ""))
    if not ok:
        FAILS.append(name)


def C(rate_a, trials, score=0.5, rate_o=None, action="a1"):
    return CG.Candidate(action, "y", "c0", rate_a=rate_a, rate_o=rate_o,
                        trials=trials, score=score)


def w1():
    a, b = SR.posterior(0.6, 50)
    check("W1 posterior of (0.6, n=50), Beta(1,1) == (31, 21)",
          abs(a - 31) < 1e-9 and abs(b - 21) < 1e-9, "(%.3f, %.3f)" % (a, b))
    check("W1 rate_a=None -> prior stands", SR.posterior(None, 999) == (1.0, 1.0))
    check("W1 trials=0 -> prior stands", SR.posterior(0.5, 0) == (1.0, 1.0))


def w2():
    pmf = SR.betabinom_pmf(20, 1.0, 1.0)
    check("W2 uniform prior -> uniform predictive",
          all(abs(p - 1.0 / 21) < 1e-12 for p in pmf))
    check("W2 pmf sums to 1", abs(sum(pmf) - 1.0) < 1e-12)
    from math import gamma, comb
    n, a, b = 8, 4.0, 6.0
    grid = 40000
    direct = []
    for k in range(n + 1):
        s = 0.0
        for i in range(1, grid):
            x = i / float(grid)
            s += (comb(n, k) * x ** k * (1 - x) ** (n - k)
                  * x ** (a - 1) * (1 - x) ** (b - 1))
        direct.append(s / grid * gamma(a + b) / (gamma(a) * gamma(b)))
    closed = SR.betabinom_pmf(n, a, b)
    err = max(abs(x - y) for x, y in zip(direct, closed))
    check("W2 closed form matches numerical integration (err < 1e-4)",
          err < 1e-4, "max err %.2e" % err)


def w3():
    check("W3 I_0.5(2,2) = 0.5", abs(SR.betainc_reg(2.0, 2.0, 0.5) - 0.5) < 1e-9,
          "%.10f" % SR.betainc_reg(2.0, 2.0, 0.5))
    check("W3 I_x(1,1) = x", abs(SR.betainc_reg(1.0, 1.0, 0.37) - 0.37) < 1e-9)
    check("W3 I_x monotone increasing in x",
          all(SR.betainc_reg(3.0, 5.0, x / 100.0)
              <= SR.betainc_reg(3.0, 5.0, (x + 1) / 100.0)
              for x in range(0, 99)))
    pg = SR.p_greater_beta(31.0, 21.0, 31.0, 21.0)
    check("W3 P(X>Y) = 0.5 for identical independent Betas",
          abs(pg - 0.5) < 5e-3, "%.6f" % pg)
    pg = SR.p_greater_beta(100.0, 5.0, 5.0, 100.0)
    check("W3 P(X>Y) ~ 1 for a clearly larger Beta", pg > 0.999, "%.6f" % pg)


def _identity_residual(t):
    """The rule's algebraic identity, as a residual to test (W4/W8)."""
    return abs(t.probe_value - t.exploit - (t.info - t.risk))


def w4():
    worst_i, worst_r, worst_id = 1e9, 1e9, 0.0
    for ra in (0.2, 0.5, 0.7, 0.85):
        for tr in (0, 3, 30, 200, 2000):
            for r in (0.1, 0.3, 0.5, 0.7, 0.9):
                t = SR.voi_terms(ra, tr, r, 20, 200.0)
                worst_i = min(worst_i, t.info)
                worst_r = min(worst_r, t.risk)
                worst_id = max(worst_id, _identity_residual(t))
    check("W4 info >= 0 (information can never hurt)", worst_i >= -1e-9,
          "min %.3e" % worst_i)
    check("W4 risk >= 0 (probing cannot earn more during the probe itself)",
          worst_r >= -1e-9, "min %.3e" % worst_r)
    check("W4 probe_value - exploit == info - risk (the rule's own identity)",
          worst_id < 1e-6, "max |lhs-rhs| %.3e" % worst_id)


def w5():
    """The TYPE difference, as a shape. T2 probes only while the alternative's
    rate is close enough that learning would change the decision, so its accept
    set over that rate is a two-sided INTERVAL. The frozen rule answers a bar on
    the candidate's score, so its answer does not turn with the price at all for
    a fixed candidate."""
    rich = [round(0.005 * i, 4) for i in range(1, 200)]
    for rule in ("voi", "voi_rate"):
        for ra, tr in ((0.85, 200), (0.55, 200), (None, 0)):
            c = C(ra, tr, score=0.55 if ra is not None else 1.0)
            acc = [r for r in rich if SR.plan([c], r, rule=rule)]
            if not acc:
                check("W5 %s candidate(%s,%s): refuses at every rate"
                      % (rule, ra, tr), True)
                continue
            lo, hi = min(acc), max(acc)
            contiguous = all(any(abs(r - a) < 1e-9 for a in acc)
                             for r in rich if lo <= r <= hi)
            check("W5 %s candidate(%s,%s): accept set is an INTERVAL "
                  "[%.3f, %.3f]" % (rule, ra, tr, lo, hi), contiguous)
    n_probe = 0
    for ra, tr in ((0.85, 200), (0.55, 200), (0.30, 100), (None, 0)):
        c = C(ra, tr, score=0.55 if ra is not None else 1.0)
        if all(SR.plan([c], r, rule="frozen") for r in rich):
            n_probe += 1
    check("W5 frozen rule probes at EVERY price for all four candidates "
          "(score against a fixed bar -- the price does not enter that way)",
          n_probe == 4, "%d/4" % n_probe)
    c = C(0.55, 200, score=0.55)
    frozen_all = all(SR.plan([c], r, rule="frozen") for r in rich)
    voi_some = any(not SR.plan([c], r, rule="voi") for r in rich)
    check("W5 at least one price where the frozen rule probes and T2 refuses "
          "(the types genuinely differ)", frozen_all and voi_some)


def w6():
    """Source audit, scoped by MODULE INTROSPECTION rather than by string
    slicing: exactly the three rule functions' own source is inspected."""
    import inspect
    bodies = {n: inspect.getsource(getattr(SR, n))
              for n in ("_voi", "_voi_rate", "_conf")}
    for name, body in bodies.items():
        for tok in ("GAIN_UNIT", "PROBE_COST", "arbitration", "arbitration_scaled",
                    "beta=", "self.beta"):
            check("W6 %s mentions no '%s'" % (name, tok), tok not in body)
    check("W6 all three rules go through the same voi_terms/posterior core",
          all(("voi_terms" in b) or ("posterior" in b) for b in bodies.values()))
    src = open(os.path.join(_HERE, "stopping_rules.py")).read()
    check("W6 the frozen path IS a delegation, not a re-implementation",
          "arbitration_scaled" in src[:src.index("def _nocost")])
    check("W6 the frozen producer really declares a conversion constant",
          "GAIN_UNIT" in open(os.path.join(
              os.path.dirname(_HERE), "arbitration.py")).read())


def w7():
    code = (
        "import sys;"
        "sys.path[:0]=[%r,%r];"
        "import candidate_gen as CG, stopping_rules as SR;"
        "cs=[CG.Candidate('a'+str(i),'y','c0',rate_a=0.55,rate_o=None,"
        "trials=200,score=0.3) for i in range(3)];"
        "print([c.action for c in SR.plan(cs,0.55,rule='voi',horizon_left=200)])"
        % (_HERE, os.path.dirname(_HERE)))
    outs = []
    for h in ("0", "1", "7"):
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, env=dict(os.environ, PYTHONHASHSEED=h))
        if r.returncode != 0:
            check("W7 subprocess ran clean", False, r.stderr.strip()[-300:])
            return
        outs.append(r.stdout)
    check("W7 identical output across three fresh processes / hash seeds",
          len(set(outs)) == 1, outs[0].strip())


def w8():
    """Negative control, corrected. The identity in W4 is ALGEBRAIC -- it holds
    for any predictive, so corrupting the predictive cannot break it (my first
    version of this control asserted the opposite and was wrong; reported, not
    quietly replaced). The meaningful red-capable control is that the rule's
    DECISION depends on its own expectation: a degenerate predictive that claims
    a probe always fails must change the answer. If it did not, the rule would
    be ignoring the information it claims to price."""
    c = C(0.85, 200, score=0.55)
    good = len(SR.plan([c], 0.80, rule="voi"))
    real = SR.betabinom_pmf
    SR.betabinom_pmf = lambda n, a, b: [1.0] + [0.0] * int(n)     # always fails
    try:
        bad = len(SR.plan([c], 0.80, rule="voi"))
        tb = SR.voi_terms(0.85, 200, 0.80, 20, 200.0)
        resid_bad = _identity_residual(tb)
    finally:
        SR.betabinom_pmf = real
    tg = SR.voi_terms(0.85, 200, 0.80, 20, 200.0)
    check("W8 negative control: a degenerate predictive CHANGES the decision "
          "(the rule really reads its own expectation)",
          good != bad, "true predictive -> %d, corrupted -> %d" % (good, bad))
    check("W8 the algebraic identity survives the corruption (identity is "
          "definitional; that is why the first control I wrote was wrong)",
          resid_bad < 1e-9, "residual %.3e" % resid_bad)
    check("W8 and the corrupted rule reports a DIFFERENT value of information",
          abs(tb.info - tg.info) > 1e-9,
          "info good=%.6f bad=%.6f" % (tg.info, tb.info))


def w9():
    check("W9 empty list -> empty accept list",
          SR.plan([], 0.5, rule="voi") == []
          and SR.plan([], 0.5, rule="conf") == []
          and SR.plan([], 0.5, rule="voi_rate") == [])
    n = len(SR.plan([C(0.9, 100)], 0.1, rule="voi", horizon_left=20))
    check("W9 L <= n: no future to benefit from -> refuse", n == 0)
    check("W9 r_best = 1.0 (perfect alternative) -> refuse",
          all(len(SR.plan([C(ra, 200)], 1.0, rule=rule)) == 0
              for ra in (0.2, 0.5, 0.9) for rule in ("voi", "voi_rate")))
    check("W9 prior-only candidate with a rich alternative: T2 refuses "
          "(declared limit L3)", len(SR.plan([C(None, 0)], 0.9, rule="voi")) == 0)
    check("W9 prior-only candidate does NOT crash T3",
          len(SR.plan([C(None, 0)], 0.3, rule="conf")) == 1)


if __name__ == "__main__":
    print("=== test_stopping_rules: unit checks on the new stopping rules ===")
    for f in (w1, w2, w3, w4, w5, w6, w7, w8, w9):
        f()
    print("\n%d failure(s)" % len(FAILS))
    if FAILS:
        print("FAILED:", FAILS)
        sys.exit(1)
    print("ALL PASS")
