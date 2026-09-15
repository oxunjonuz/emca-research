"""analyze_bayes.py -- turn 135. Verdicts for PREREG_BAYES.md §4.

Reads only the frozen JSON in results_bayes/ (never re-runs an agent) and prints
gates G0-G6 plus the headline tables. Numbers here are the ones the report quotes;
factcheck_bayes.py recomputes them independently.

  python3 analyze_bayes.py [nsim]
"""
import glob
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("BAYES_OUT") or os.path.join(_HERE, "results_bayes")


def load():
    cells = {}
    for fn in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        if fn.endswith("SUMMARY.json"):
            continue
        d = json.load(open(fn))
        key = (d["arm"], d["inst"], d["param"], d.get("base"), d["nsim"])
        cells[key] = d
    return cells


def pick(cells, arm, inst, param, base, nsim):
    return cells.get((arm, inst, param, base, nsim))


def boot_ci(a, b, n=5000, seed=12345):
    rng = np.random.RandomState(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    idx = rng.randint(0, len(d), size=(n, len(d)))
    means = d[idx].mean(axis=1)
    return float(np.mean(d)), float(np.percentile(means, 2.5)), \
        float(np.percentile(means, 97.5))


def sign_test(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    return int((d > 0).sum()), int((d < 0).sum())


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    den = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / den) if den else float("nan")


def main():
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    nsim_pub = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    cells = load()
    print("cells loaded: %d (nsim=%d for mask/maskr/rich, %d for pub)\n"
          % (len(cells), nsim, nsim_pub))

    bases = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

    # ---- G0 transplant control (checked in verify; restated here) ---------
    print("=== G0 transplant control: v4 driver with OLD rules == turn-134 v3 "
          "producer  (see verify_bayes_independent.py V2)")

    # ---- G1 the new rule must act ----------------------------------------
    print("\n=== G1 the new rule must act (bayes probes on >=80% of mask cells)")
    g1 = []
    for e in (0.15, 0.25, 0.35):
        c = pick(cells, "bayes", "mask", e, None, nsim)
        if c is None:
            continue
        frac = float(np.mean([1 if r["n_probes"] > 0 else 0 for r in c["rows"]]))
        g1.append(frac)
        print("  mask eps=%.2f  probes>0 on %.1f%% of seeds, mean probes %.2f"
              % (e, 100 * frac, c["mean_probes"]))
    print("  G1 PASS = %s" % (bool(g1) and min(g1) >= 0.80))

    # ---- G2 derived silence ----------------------------------------------
    print("\n=== G2 the stopping point must be DERIVED: probes vs world richness")
    print("  base   bayes_probes  voi_probes  frozen_probes  conf_probes  "
          "nocost_probes")
    vp, bp = [], []
    for b in bases:
        row = []
        for arm in ("bayes", "voi", "frozen_rule", "conf", "union_nocost"):
            c = pick(cells, arm, "mask", 0.35, b, nsim)
            row.append(c["mean_probes"] if c else float("nan"))
        bp.append(row[0]); vp.append(row[1])
        print("  %.2f   %-12.2f  %-11.2f  %-13.2f  %-11.2f  %.2f"
              % (b, row[0], row[1], row[2], row[3], row[4]))
    rho_b = spearman(bases, bp)
    rho_v = spearman(bases, vp)
    print("  Spearman rho(bayes probes, richness) = %.3f  (G2 wants <= 0)" % rho_b)
    print("  Spearman rho(voi   probes, richness) = %.3f  (turn-134 comparison)"
          % rho_v)
    print("  G2 PASS = %s" % (rho_b <= 0.0))

    # ---- G4 per-state inclusion, empirically ------------------------------
    print("\n=== G4 the theorem's empirical shadow: wherever voi still probes, "
          "does bayes probe at least as often?")
    print("  base   voi_probes  bayes_probes  bayes>=voi")
    ok = True
    for b, bpv, vpv in zip(bases, bp, vp):
        good = (bpv >= vpv - 1e-9)
        ok = ok and (good or vpv < 0.05)
        print("  %.2f   %10.2f  %12.2f  %s" % (b, vpv, bpv, good))
    print("  G4 (non-strict; declared P1) PASS = %s" % ok)

    # ---- G3 regret --------------------------------------------------------
    print("\n=== G3 regret: bayes vs voi and vs frozen_rule "
          "(bootstrap 95%% CI, sign test)")
    for inst, params, ns in (("mask", (0.15, 0.25, 0.35), nsim),
                             ("maskr", (0.25, 0.35), nsim),
                             ("pub", (2, 8, 16, 49), nsim_pub)):
        for p in params:
            a = pick(cells, "bayes", inst, p, None, ns)
            for other in ("voi", "frozen_rule", "conf"):
                b = pick(cells, other, inst, p, None, ns)
                if not a or not b:
                    continue
                ra = [r["regret"] for r in a["rows"]]
                rb = [r["regret"] for r in b["rows"]]
                m, lo, hi = boot_ci(ra, rb)
                pos, neg = sign_test(ra, rb)
                verdict = ("bayes BETTER" if hi < 0 else
                           "bayes WORSE" if lo > 0 else "NO DIFFERENCE")
                print("  %-5s p=%-4s bayes vs %-11s diff=%+.5f CI=[%+.5f,%+.5f] "
                      "sign %d+/%d-  %s" % (inst, p, other, m, lo, hi, pos, neg,
                                            verdict))
    print()

    # ---- G5 controls -------------------------------------------------------
    print("=== G5 controls")
    for arm in ("beta0", "pure"):
        c = pick(cells, arm, "mask", 0.35, None, nsim)
        if c:
            print("  %-6s mean probes %.2f  regret %.5f"
                  % (arm, c["mean_probes"], c["mean_regret"]))
    for b in bases:
        n = pick(cells, "union_nocost", "mask", 0.35, b, nsim)
        v = pick(cells, "voi", "mask", 0.35, b, nsim)
        bb = pick(cells, "bayes", "mask", 0.35, b, nsim)
        if n and v and bb:
            flag = "ok" if (n["mean_probes"] >= min(v["mean_probes"],
                                                    bb["mean_probes"]) - 1e-9) \
                else "VIOLATION"
            print("  base %.2f  nocost %.2f >= min(voi %.2f, bayes %.2f)  %s"
                  % (b, n["mean_probes"], v["mean_probes"], bb["mean_probes"],
                     flag))
    print()

    # ---- headline table ----------------------------------------------------
    print("=== HEADLINE mask/maskr: mean regret / mean probes / frac optimal "
          "(nsim=%d)" % nsim)
    print("  %-14s | %-24s | %-24s" % ("arm", "mask eps=0.35", "maskr eps=0.35"))
    for arm in ("bayes", "voi", "conf", "frozen_rule", "union_nocost", "pure",
                "beta0"):
        a = pick(cells, arm, "mask", 0.35, None, nsim)
        b = pick(cells, arm, "maskr", 0.35, None, nsim)

        def f(c):
            return ("%.5f / %5.2f / %.2f" % (c["mean_regret"], c["mean_probes"],
                                             c["frac_optimal"])) if c else "n/a"
        print("  %-14s | %-24s | %-24s" % (arm, f(a), f(b)))

    print("\n=== HEADLINE pub (nsim=%d): mean regret / mean probes" % nsim_pub)
    print("  %-14s | %s" % ("arm", "  ".join("m=%-6s" % m for m in (2, 8, 16, 49))))
    for arm in ("bayes", "voi", "conf", "frozen_rule"):
        row = []
        for m in (2, 8, 16, 49):
            c = pick(cells, arm, "pub", m, None, nsim_pub)
            row.append("%.5f/%.2f" % (c["mean_regret"], c["mean_probes"])
                       if c else "n/a")
        print("  %-14s | %s" % (arm, "  ".join("%-9s" % x for x in row)))

    print("\n=== G6 cost (mean seconds per cell)")
    for arm in ("bayes", "voi", "conf", "frozen_rule"):
        c = pick(cells, arm, "mask", 0.35, None, nsim)
        if c:
            print("  %-14s %.4f s/cell" % (arm, c["mean_seconds"]))


if __name__ == "__main__":
    main()