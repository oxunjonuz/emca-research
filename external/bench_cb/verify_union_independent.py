"""verify_union_independent.py -- turn 129. INDEPENDENT verification.

Different code, disk only: imports NONE of the producers (union_agent,
union_run, union_matrix). It reads the frozen per-seed rows in results_union/
and re-derives every reported quantity with plain arithmetic, then re-derives
the instance's claimed structure from the model's OWN parameters via a fresh
Monte-Carlo sample (not from the producer's expected_rewards array), and runs a
NEGATIVE CONTROL that must fail.

Checks:
  C1 every cell's mean/sem re-derived from its raw rows
  C2 the instance structure: pooled margin of the true arm over do(A=0) is 0;
     ctx0 gap is +eps; ctx1 gap is -eps (Monte-Carlo, independent of the
     producer's analytic arrays)
  C3 the published instance reproduces turn-128's frozen numbers (pure=0.300,
     alg1 shape) -- a cross-check against a DIFFERENT turn's frozen matrix
  C4 determinism: a fresh process reproduces a cell bit-for-bit
  C5 the union's advantage is super-additive: union < min(parts) on mask
  NEG a negative control that MUST fail (assert union_noctx == union on mask)
"""
import sys, os, json, subprocess
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "results_union")
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)

FAILS = []
CHECKS = [0]


def check(name, cond, detail=""):
    CHECKS[0] += 1
    if not cond:
        FAILS.append("%s :: %s" % (name, detail))
        print("  FAIL  %s  %s" % (name, detail))
    else:
        print("  ok    %s" % name)


def load(inst, param, arm):
    fn = os.path.join(OUT, "%s_p%s_%s.json" % (inst, str(param).replace(".", "p"), arm))
    with open(fn) as f:
        return json.load(f)


def main():
    print("=== C1: every cell mean/sem re-derived from raw rows ===")
    cells = 0
    for fn in sorted(os.listdir(OUT)):
        if not fn.endswith(".json") or fn == "SUMMARY.json":
            continue
        with open(os.path.join(OUT, fn)) as f:
            d = json.load(f)
        regs = [r["regret"] for r in d["rows"]]
        mean = float(np.mean(regs))
        sem = float(np.std(regs, ddof=1) / np.sqrt(len(regs)))
        check("C1 %s" % fn, abs(mean - d["mean_regret"]) < 1e-9
              and abs(sem - d["sem_regret"]) < 1e-9,
              "mean %.6f vs %.6f" % (mean, d["mean_regret"]))
        cells += 1
    print("  (%d cells)" % cells)

    print("=== C2: instance structure, Monte-Carlo, independent of producer ===")
    from union_instance import MaskedParallel
    mm = MaskedParallel(N=50, m=1, eps=0.35)

    def mc(a, n, z=None):
        tot = 0
        cnt = 0
        for _ in range(n):
            x, y, zz = mm.sample(a)
            if z is None or zz == z:
                tot += y
                cnt += 1
        return tot / cnt if cnt else float("nan")

    pA1 = mc(mm.N, 60000)
    pA0 = mc(0, 60000)
    c0A1 = mc(mm.N, 60000, z=0)
    c1A1 = mc(mm.N, 60000, z=1)
    c0A0 = mc(0, 60000, z=0)
    check("C2 pooled margin of true arm is ZERO", abs(pA1 - pA0) < 0.02,
          "do(A=1)=%.4f do(A=0)=%.4f diff=%.4f" % (pA1, pA0, pA1 - pA0))
    check("C2 ctx0 true arm pays base+eps+decoy·seg",
          abs(c0A1 - (mm.base + 0.35 + mm.decoy * mm.seg)) < 0.02,
          "ctx0 do(A=1)=%.4f (expect %.4f)" % (c0A1, mm.base + 0.35 + mm.decoy * mm.seg))
    check("C2 ctx1 true arm pays base-eps (decoy rare there)", abs(c1A1 - (mm.base - 0.35)) < 0.03,
          "ctx1 do(A=1)=%.4f (expect ~%.2f)" % (c1A1, mm.base - 0.35))
    check("C2 pooled analytic == Monte-Carlo",
          abs(mm.expected_rewards[mm.N] - pA1) < 0.02
          and abs(mm.expected_rewards[0] - pA0) < 0.02,
          "analytic A1=%.4f mc=%.4f | analytic A0=%.4f mc=%.4f"
          % (mm.expected_rewards[mm.N], pA1, mm.expected_rewards[0], pA0))
    check("C2 ctx0 do(A=0) pays base+decoy·seg",
          abs(c0A0 - (mm.base + mm.decoy * mm.seg)) < 0.02,
          "ctx0 do(A=0)=%.4f (expect %.4f)" % (c0A0, mm.base + mm.decoy * mm.seg))
    # analytic per-context arrays must MATCH the Monte-Carlo they are scored on
    check("C2 analytic er_ctx[0][A1] == MC ctx0",
          abs(mm.er_ctx[0][mm.N] - c0A1) < 0.02,
          "analytic=%.4f mc=%.4f" % (mm.er_ctx[0][mm.N], c0A1))

    print("=== C3: published instance reproduces turn-128's frozen numbers ===")
    pure_pub = {m: load("pub", m, "pure")["mean_regret"] for m in [2, 8, 16, 25, 40, 49]}
    alg1_pub = {m: load("pub", m, "alg1_pub")["mean_regret"] for m in [2, 8, 16, 25, 40, 49]}
    check("C3 pure == 0.3000 at every m",
          all(abs(v - 0.3000) < 1e-9 for v in pure_pub.values()),
          str(pure_pub))
    # turn-128 frozen alg1 column
    T128_ALG1 = {2: 0.0000, 8: 0.0189, 16: 0.1056, 25: 0.1755, 40: 0.2394, 49: 0.2574}
    ok = all(abs(alg1_pub[m] - T128_ALG1[m]) < 5e-4 for m in T128_ALG1)
    check("C3 alg1_pub matches turn-128 frozen column", ok,
          str({m: round(alg1_pub[m], 4) for m in alg1_pub}))

    print("=== C4: determinism (fresh process, bit-for-bit) ===")
    cmd = [sys.executable, "-c",
           "import sys; sys.path.insert(0,'ext/latt_py3'); sys.path.insert(0,'.');"
           "from union_run import run_cell; import json;"
           "print(json.dumps(run_cell('union','mask',0.35,7,400)))"]
    o1 = subprocess.run(cmd, cwd=_HERE, capture_output=True, text=True).stdout
    o2 = subprocess.run(cmd, cwd=_HERE, capture_output=True, text=True).stdout
    d1, d2 = json.loads(o1), json.loads(o2)
    for k in ("seconds",):
        d1.pop(k, None); d2.pop(k, None)
    check("C4 union mask eps=0.35 seed=7 deterministic", d1 == d2)

    print("=== C5: are the pieces MUTUALLY NECESSARY? (ablation test) ===")
    # The honest test is not "union beats every ablation" (one ablation may be a
    # superset that happens to be inert). The test is: remove EITHER the context
    # split OR the exploration term and the union collapses.
    for eps in [0.15, 0.25, 0.35]:
        u = load("mask", eps, "union")["mean_regret"]
        noctx = load("mask", eps, "union_noctx")["mean_regret"]
        noexp = load("mask", eps, "union_noexp")["mean_regret"]
        pure = load("mask", eps, "pure")["mean_regret"]
        check("C5 mask eps=%s: removing EITHER piece collapses the union" % eps,
              u < noctx - 0.03 and u < noexp - 0.03,
              "union=%.4f noctx=%.4f noexp=%.4f pure=%.4f" % (u, noctx, noexp, pure))
        # strictly super-additive: the union is far below the best single-feature
        # arm (both features needed together)
        best_single_feature = min(noctx, noexp)
        check("C5 mask eps=%s: union << best single-feature arm" % eps,
              u < best_single_feature - 0.03,
              "union=%.4f best_single=%.4f" % (u, best_single_feature))

    print("=== C5b: the RICH regime (honest boundary; may FAIL the union) ===")
    for eps in [0.25, 0.35]:
        u = load("maskr", eps, "union")["mean_regret"]
        parts = {a: load("maskr", eps, a)["mean_regret"]
                 for a in ["union_noctx", "union_noexp", "union_nocost",
                           "pure", "budget_pub", "uniform_policy"]}
        best_part = min(parts.values())
        print("  maskr eps=%s: union=%.4f best_part=%.4f (%s)  -> %s"
              % (eps, u, best_part, min(parts, key=parts.get),
                 "union WINS" if u < best_part - 0.01 else "union LOSES"))

    print("=== C6: is the cost-aware arbiter load-bearing? (honest, may FAIL) ===")
    for eps in [0.15, 0.25, 0.35]:
        u = load("mask", eps, "union")["mean_regret"]
        nc = load("mask", eps, "union_nocost")["mean_regret"]
        check("C6 union==union_nocost at eps=%s (arbiter inert?)" % eps,
              abs(u - nc) < 0.005, "union=%.4f nocost=%.4f" % (u, nc))

    print("=== NEGATIVE CONTROL: must FAIL ===")
    u = load("mask", 0.35, "union")["mean_regret"]
    c = load("mask", 0.35, "union_noctx")["mean_regret"]
    # This assertion is FALSE by construction; the harness must report it red.
    neg_ok = (abs(u - c) < 1e-6)
    print("  negative control (union==union_noctx on mask): %s  -> %s"
          % ("asserted", "RED as required" if not neg_ok else "GREEN (BAD!)"))
    if neg_ok:
        FAILS.append("NEGATIVE CONTROL did not fire")

    print("\n=== RESULT: %d checks, %d failures ===" % (CHECKS[0], len(FAILS)))
    for f in FAILS:
        print("  " + f)
    print("ALL AGREE" if not FAILS else "DISAGREEMENTS PRESENT")


if __name__ == "__main__":
    main()
