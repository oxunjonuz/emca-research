"""diag_t4_inclusion.py -- turn 135. WHY did the inclusion claim fail on 7/240
states in test_bayes_rules.py W2?

HYPOTHESIS: they are not dominance failures but INDIFFERENCE TIES -- states where
T2's own criterion (info - risk) is within floating-point noise of zero, so T2
accepts on noise while T4 (whose probe-commit is exactly 0 there) refuses. If so,
|info - risk| <= 1e-12 in every violating state and the two actions are exactly
equally optimal. This script tests that, and also scans a much wider grid for any
violation with a LARGE margin (which would be a real failure).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import candidate_gen as CG
import stopping_rules as SR
import bayes_stopping as BS

TOL = 1e-12


def mk(ra, tr):
    return CG.Candidate("a1", "y", "c0", rate_a=ra, rate_o=None, trials=tr,
                        score=0.3)


def margins(ra, tr, r, L):
    c = mk(ra, tr)
    t2 = SR.voi_terms(ra, tr, r, 20, L)
    mu, commit, probe, V, m = BS.terms_bayes(ra, tr, r, 20, L)
    return (t2.info - t2.risk), (probe - commit)


print("(1) the 7 reported states, with both margins")
for (ra, tr, r, L) in ((0.2, 400, 0.1, 40.0), (0.55, 5, 0.1, 40.0),
                       (0.85, 5, 0.1, 40.0), (0.85, 100, 0.1, 40.0)):
    m2, m4 = margins(ra, tr, r, L)
    print("  rate=%-5s tr=%-4s r=%.2f L=%.0f  T2 margin=%+.3e  T4 margin=%+.3e"
          "  T2acc=%s T4acc=%s" % (ra, tr, r, L, m2, m4, m2 > 0, m4 > 0))

print("\n(2) WIDE SCAN for a violation with a LARGE T2 margin (> TOL).")
print("    A violation here would be a genuine dominance failure.")
bad_big = []
bad_tie = []
n = 0
for ra in (None, 0.05, 0.20, 0.35, 0.55, 0.70, 0.85, 0.95):
    for tr in (0, 1, 5, 20, 100, 400, 2000):
        for r in (0.05, 0.10, 0.30, 0.50, 0.65, 0.80, 0.90, 0.95):
            for L in (20.0, 40.0, 60.0, 200.0, 400.0):
                n += 1
                m2, m4 = margins(ra, tr, r, L)
                t2a, t4a = m2 > 0, m4 > 0
                if t2a and not t4a:
                    if m2 > TOL:
                        bad_big.append((ra, tr, r, L, m2, m4))
                    else:
                        bad_tie.append((ra, tr, r, L, m2))
print("    states scanned: %d" % n)
print("    T2-accepts/T4-refuses with T2 margin > %g : %d" % (TOL, len(bad_big)))
print("    T2-accepts/T4-refuses with T2 margin <= %g: %d (ties)"
      % (TOL, len(bad_tie)))
if bad_big:
    print("    REAL FAILURES: %s" % bad_big[:6])
if bad_tie:
    worst = max(abs(x[4]) for x in bad_tie)
    print("    worst tie margin: %.3e" % worst)

print("\n(3) the converse direction: does T4 ever accept where T2 strictly "
      "refuses? (that is the strict gain the theorem predicts)")
gain = 0
for ra in (None, 0.05, 0.20, 0.35, 0.55, 0.70, 0.85, 0.95):
    for tr in (0, 1, 5, 20, 100, 400, 2000):
        for r in (0.05, 0.10, 0.30, 0.50, 0.65, 0.80, 0.90, 0.95):
            for L in (20.0, 40.0, 60.0, 200.0, 400.0):
                m2, m4 = margins(ra, tr, r, L)
                if m4 > 0 and m2 <= 0:
                    gain += 1
print("    states where T4 strictly accepts and T2 does not: %d" % gain)