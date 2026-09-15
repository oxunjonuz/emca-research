"""factcheck_union_report.py -- turn 129. Re-derive every number quoted in
RESULTS_UNION.md from the FROZEN matrix (results_union/) and the Lean output.
Prints PASS/FAIL per statement. Any FAIL means the report must be corrected.
"""
import json, os, sys, re

_HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(_HERE, "results_union", "SUMMARY.json")))
FAILS = []
N = [0]


def stmt(text, cond, got=""):
    N[0] += 1
    if cond:
        print("  ok   %s" % text)
    else:
        FAILS.append(text)
        print("  FAIL %s   (%s)" % (text, got))


def g(inst, param, arm):
    return S["%s|%s|%s" % (inst, param, arm)]["mean_regret"]


print("=== MASK instance (base=0.5) ===")
for eps in [0.15, 0.25, 0.35]:
    pu = g("mask", eps, "pure")
    u = g("mask", eps, "union")
    nc = g("mask", eps, "union_noctx")
    ne = g("mask", eps, "union_noexp")
    stmt("mask eps=%s pure in [0.07,0.19]" % eps, 0.07 <= pu <= 0.19, "%.4f" % pu)
    stmt("mask eps=%s union < 0.05" % eps, u < 0.05, "%.4f" % u)
    stmt("mask eps=%s union << noctx" % eps, u < nc - 0.03, "%.4f vs %.4f" % (u, nc))
    stmt("mask eps=%s union << noexp" % eps, u < ne - 0.03, "%.4f vs %.4f" % (u, ne))
    stmt("mask eps=%s noexp ~ pure" % eps, abs(ne - pu) < 0.005, "%.4f vs %.4f" % (ne, pu))

print("=== exact quoted mask numbers ===")
stmt("mask 0.15 union=0.0315", abs(g("mask", 0.15, "union") - 0.0315) < 5e-4, g("mask", 0.15, "union"))
stmt("mask 0.25 union=0.0136", abs(g("mask", 0.25, "union") - 0.0136) < 5e-4, g("mask", 0.25, "union"))
stmt("mask 0.35 union=0.0051", abs(g("mask", 0.35, "union") - 0.0051) < 5e-4, g("mask", 0.35, "union"))
stmt("mask 0.15 pure=0.0804", abs(g("mask", 0.15, "pure") - 0.0804) < 5e-4, g("mask", 0.15, "pure"))
stmt("mask 0.25 pure=0.1304", abs(g("mask", 0.25, "pure") - 0.1304) < 5e-4, g("mask", 0.25, "pure"))
stmt("mask 0.35 pure=0.1804", abs(g("mask", 0.35, "pure") - 0.1804) < 5e-4, g("mask", 0.35, "pure"))
stmt("mask 0.35 noctx=0.1794", abs(g("mask", 0.35, "union_noctx") - 0.1794) < 5e-4, g("mask", 0.35, "union_noctx"))
stmt("mask 0.35 noexp=0.1776", abs(g("mask", 0.35, "union_noexp") - 0.1776) < 5e-4, g("mask", 0.35, "union_noexp"))

print("=== improvement factors ===")
f15 = g("mask", 0.15, "pure") / g("mask", 0.15, "union")
f25 = g("mask", 0.25, "pure") / g("mask", 0.25, "union")
f35 = g("mask", 0.35, "pure") / g("mask", 0.35, "union")
stmt("factor eps=0.35 > 20x", f35 > 20, "%.1f" % f35)
stmt("factor eps=0.25 > 5x", f25 > 5, "%.1f" % f25)

print("=== PUBLISHED instance ===")
for m in [2, 8, 16, 25, 40, 49]:
    stmt("pub m=%d pure=0.3000" % m, abs(g("pub", m, "pure") - 0.3000) < 1e-9, "%.4f" % g("pub", m, "pure"))
# HONEST: at m=2 the union does NOT beat alg1 (0.0069 vs 0.0000); it beats it
# for every m >= 8. The claim is stated exactly that way, not overreached.
stmt("pub m=2 union <= 0.01 (but NOT below alg1=0.0)",
     abs(g("pub", 2, "union") - 0.0069) < 5e-4 and g("pub", 2, "alg1_pub") < 1e-9,
     "union=%.4f alg1=%.4f" % (g("pub", 2, "union"), g("pub", 2, "alg1_pub")))
for m in [8, 16, 25, 40, 49]:
    stmt("pub m=%d union < alg1" % m, g("pub", m, "union") < g("pub", m, "alg1_pub") - 1e-4,
         "union=%.4f alg1=%.4f" % (g("pub", m, "union"), g("pub", m, "alg1_pub")))
stmt("pub m=2 union=0.0069", abs(g("pub", 2, "union") - 0.0069) < 5e-4, g("pub", 2, "union"))
stmt("pub m=49 union=0.0264", abs(g("pub", 49, "union") - 0.0264) < 5e-4, g("pub", 49, "union"))
stmt("pub m=49 alg1=0.2574", abs(g("pub", 49, "alg1_pub") - 0.2574) < 5e-4, g("pub", 49, "alg1_pub"))

print("=== RICH regime (honest boundaries) ===")
for eps in [0.25, 0.35]:
    u = g("maskr", eps, "union")
    ne = g("maskr", eps, "union_noexp")
    nc = g("maskr", eps, "union_nocost")
    # union does NOT strictly beat noexp in the rich regime (exploration is inert
    # there: the alternative is rich, so the tree is already visited)
    stmt("maskr eps=%s union == noexp (exploration inert in rich regime)" % eps,
         abs(u - ne) < 0.005, "%.4f vs %.4f" % (u, ne))
    # and the cost-aware arbiter HURTS here (nocost beats union)
    stmt("maskr eps=%s union_nocost < union (arbiter counterproductive)" % eps,
         nc < u - 0.001, "nocost=%.4f union=%.4f" % (nc, u))

print("=== Lean ===")
lean_out = open(os.path.join(_HERE, "lean", "out.txt")).read()
stmt("Lean file compiles with no output (no sorry, no error)", lean_out.strip() == "", repr(lean_out[:120]))
lean_src = open(os.path.join(_HERE, "lean", "UNION_BOUND.lean")).read()
stmt("Lean file has no 'sorry'/'admit'/'axiom'", not re.search(r"\b(sorry|admit|axiom)\b", lean_src))

print("\n=== FACTCHECK: %d statements, %d failures ===" % (N[0], len(FAILS)))
for f in FAILS:
    print("  " + f)
print("ALL PASS" if not FAILS else "FAILURES PRESENT")
sys.exit(1 if FAILS else 0)
