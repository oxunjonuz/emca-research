"""analyze_stopping.py -- turn 134. Verdicts for PREREG_STOPPING.md §4.

Reads only the frozen JSON in results_stopping/ (never re-runs an agent) and
prints the gates G0-G6 plus the headline table. Numbers here are the ones the
report quotes; factcheck_stopping.py recomputes them independently.

  python3 analyze_stopping.py [nsim]
"""
import glob
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("STOPPING_OUT") or os.path.join(_HERE, "results_stopping")


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
    """Bootstrap 95% CI of mean(a) - mean(b), paired by index (same seeds)."""
    rng = np.random.RandomState(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    idx = rng.randint(0, len(d), size=(n, len(d)))
    means = d[idx].mean(axis=1)
    return float(np.mean(d)), float(np.percentile(means, 2.5)), \
        float(np.percentile(means, 97.5))


def sign_test(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    pos = int((d > 0).sum())
    neg = int((d < 0).sum())
    return pos, neg


def main():
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    cells = load()
    print("cells loaded: %d (nsim=%d)\n" % (len(cells), nsim))

    # ---- G0 transplant control -------------------------------------------
    print("=== G0 transplant control: frozen_rule vs union (must be identical)")
    g0_ok = True
    for (arm, inst, param, base, ns) in list(cells):
        if arm != "frozen_rule" or ns != nsim:
            continue
        alt = pick(cells, "union", inst, param, base, ns)
        if alt is None:
            continue
        a = cells[(arm, inst, param, base, ns)]
        ka = [(r["seed"], r["regret"], r["n_probes"]) for r in a["rows"]]
        kb = [(r["seed"], r["regret"], r["n_probes"]) for r in alt["rows"]]
        same = ka == kb
        g0_ok = g0_ok and same
        print("  %-6s p=%-5s base=%-5s  %s" % (inst, param, base,
                                               "IDENTICAL" if same else "DIFFER"))
    print("  G0 PASS = %s\n" % g0_ok)

    # ---- G1 the new rule must act ----------------------------------------
    print("=== G1 the new rule must act (voi probes on >=80%% of mask cells)")
    g1 = []
    for e in (0.15, 0.25, 0.35):
        c = pick(cells, "voi", "mask", e, None, nsim)
        if c is None:
            continue
        frac = float(np.mean([1 if r["n_probes"] > 0 else 0 for r in c["rows"]]))
        g1.append(frac)
        print("  mask eps=%.2f  probes>0 on %.1f%% of seeds, mean probes %.2f"
              % (e, 100 * frac, c["mean_probes"]))
    print("  G1 PASS = %s\n" % (bool(g1) and min(g1) >= 0.80))

    # ---- G2 probes must fall as the world gets richer --------------------
    print("=== G2 the stopping point must be DERIVED: probes vs world richness")
    print("  base   voi_probes  frozen_probes  conf_probes  nocost_probes")
    bases = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    vp, fp, cp, np_ = [], [], [], []
    for b in bases:
        row = []
        for arm in ("voi", "frozen_rule", "conf", "union_nocost"):
            c = pick(cells, arm, "mask", 0.35, b, nsim)
            row.append(c["mean_probes"] if c else float("nan"))
        vp.append(row[0]); fp.append(row[1]); cp.append(row[2]); np_.append(row[3])
        print("  %.2f   %10.2f  %13.2f  %11.2f  %13.2f"
              % (b, row[0], row[1], row[2], row[3]))
    # Spearman rho of voi probes vs base
    def spearman(x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        rx -= rx.mean(); ry -= ry.mean()
        den = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
        return float((rx * ry).sum() / den) if den else float("nan")
    rho = spearman(bases, vp)
    print("  Spearman rho(voi probes, richness) = %.3f  (G2 wants <= 0)" % rho)
    print("  G2 PASS = %s\n" % (rho <= 0.0))

    # ---- G3 regret: voi vs frozen_rule -----------------------------------
    print("=== G3 regret: voi vs frozen_rule (bootstrap 95%% CI, sign test)")
    for inst, params in (("mask", (0.15, 0.25, 0.35)), ("maskr", (0.25, 0.35))):
        for p in params:
            a = pick(cells, "voi", inst, p, None, nsim)
            b = pick(cells, "frozen_rule", inst, p, None, nsim)
            if not a or not b:
                continue
            ra = [r["regret"] for r in a["rows"]]
            rb = [r["regret"] for r in b["rows"]]
            m, lo, hi = boot_ci(ra, rb)
            pos, neg = sign_test(ra, rb)
            verdict = ("voi BETTER" if hi < 0 else
                       "voi WORSE" if lo > 0 else "NO DIFFERENCE")
            print("  %-6s eps=%.2f  diff=%+.5f CI=[%+.5f,%+.5f] sign %d+/%d-  %s"
                  % (inst, p, m, lo, hi, pos, neg, verdict))
    print()

    # ---- G4 the probability-only rule ------------------------------------
    print("=== G4 conf (probability only) vs nocost (no price at all)")
    print("  base   conf_probes  nocost_probes   conf_regret  nocost_regret")
    for b in bases:
        c = pick(cells, "conf", "mask", 0.35, b, nsim)
        n = pick(cells, "union_nocost", "mask", 0.35, b, nsim)
        if c and n:
            print("  %.2f   %11.2f  %13.2f  %11.5f  %13.5f"
                  % (b, c["mean_probes"], n["mean_probes"], c["mean_regret"],
                     n["mean_regret"]))
    print("  P1 (preregistered): conf tracks nocost, not a stopping rule\n")

    # ---- G5 controls ------------------------------------------------------
    print("=== G5 controls")
    for arm in ("beta0", "pure", "union_noexp"):
        c = pick(cells, arm, "mask", 0.35, None, nsim)
        if c:
            print("  %-12s mean probes %.2f  regret %.5f"
                  % (arm, c["mean_probes"], c["mean_regret"]))
    print()

    # ---- headline table ---------------------------------------------------
    print("=== HEADLINE (nsim=%d): mean regret / mean probes / frac optimal" % nsim)
    print("  %-14s | %-22s | %-22s" % ("arm", "mask eps=0.35", "maskr eps=0.35"))
    for arm in ("frozen_rule", "voi", "voi_rate", "conf", "union_nocost",
                "union_noexp", "pure", "beta0"):
        a = pick(cells, arm, "mask", 0.35, None, nsim)
        b = pick(cells, arm, "maskr", 0.35, None, nsim)
        f = lambda c: ("%.5f / %5.2f / %.2f" % (c["mean_regret"],
                                                c["mean_probes"],
                                                c["frac_optimal"])) if c else "n/a"
        print("  %-14s | %-22s | %-22s" % (arm, f(a), f(b)))


if __name__ == "__main__":
    main()
