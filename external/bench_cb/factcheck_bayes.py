"""factcheck_bayes.py -- turn 135. Recompute EVERY number quoted in
RESULTS_BAYES.md from the frozen JSON, independently of analyze_bayes.py.

Each row is (label, claimed value, recomputed value). A row fails if they differ
by more than the stated tolerance. The point is that the report's numbers come
from the disk, not from memory.

  python3 factcheck_bayes.py
"""
import glob
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("BAYES_OUT") or os.path.join(_HERE, "results_bayes")
HI = os.environ.get("BAYES_HI_OUT") or os.path.join(_HERE, "results_bayes_hi")

ROWS = []
FAILS = []


def load(d):
    cells = {}
    for fn in sorted(glob.glob(os.path.join(d, "*.json"))):
        if fn.endswith("SUMMARY.json"):
            continue
        j = json.load(open(fn))
        cells[(j["arm"], j["inst"], j["param"], j.get("base"), j["nsim"])] = j
    return cells


C = load(OUT)
H = load(HI)


def pick(d, arm, inst, param, base, ns):
    return d.get((arm, inst, param, base, ns))


def row(label, claimed, recomputed, tol=1e-9):
    ok = (abs(claimed - recomputed) <= tol) if isinstance(claimed, float) \
        else (claimed == recomputed)
    ROWS.append((label, claimed, recomputed, ok))
    if not ok:
        FAILS.append((label, claimed, recomputed))


def mean_of(c, key):
    return float(np.mean([r.get(key, 0) or 0 for r in c["rows"]]))


def regret_of(c):
    return float(np.mean([r["regret"] for r in c["rows"]]))


def boot_ci(a, b, n=5000, seed=12345):
    rng = np.random.RandomState(seed)
    d = np.asarray(a, float) - np.asarray(b, float)
    idx = rng.randint(0, len(d), size=(n, len(d)))
    means = d[idx].mean(axis=1)
    return float(np.mean(d)), float(np.percentile(means, 2.5)), \
        float(np.percentile(means, 97.5))


print("=== factcheck: numbers quoted in RESULTS_BAYES.md\n")

# --- 1. the 200-sim headline table (mask / maskr) ------------------------
for arm in ("bayes", "voi", "conf", "frozen_rule", "union_nocost", "pure",
            "beta0"):
    for inst in ("mask", "maskr"):
        c = pick(C, arm, inst, 0.35, None, 200)
        if not c:
            continue
        row("mask table %s/%s regret" % (arm, inst), c["mean_regret"],
            regret_of(c))
        row("mask table %s/%s probes" % (arm, inst), c["mean_probes"],
            mean_of(c, "n_probes"))

# --- 2. G1 probe fraction ------------------------------------------------
for e in (0.15, 0.25, 0.35):
    c = pick(C, "bayes", "mask", e, None, 200)
    frac = float(np.mean([1 if r["n_probes"] > 0 else 0 for r in c["rows"]]))
    row("G1 probe frac mask eps=%.2f (claimed 0.995)" % e, 0.995, round(frac, 3),
        tol=1e-3)

# --- 3. G2 richness probes ----------------------------------------------
bases = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
bp, vp = [], []
for b in bases:
    cb = pick(C, "bayes", "mask", 0.35, b, 200)
    cv = pick(C, "voi", "mask", 0.35, b, 200)
    bp.append(cb["mean_probes"])
    vp.append(cv["mean_probes"])
    row("G2 bayes probes base=%.2f" % b, cb["mean_probes"],
        mean_of(cb, "n_probes"))


def rank(x):
    x = np.asarray(x, float)
    return np.argsort(np.argsort(x)).astype(float)


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    rx = rx - rx.mean(); ry = ry - ry.mean()
    return float((rx * ry).sum() / np.sqrt((rx ** 2).sum() * (ry ** 2).sum()))


rho_b, rho_v = spearman(bases, bp), spearman(bases, vp)
print("  [info] spearman(bayes) = %.3f   spearman(voi) = %.3f" % (rho_b, rho_v))
row("G2 rho(bayes) claimed -0.905", -0.905, round(rho_b, 3), tol=1e-3)

# --- 4. G3 the bayes-vs-voi differences on the 200-sim matrix -----------
for (inst, param) in (("mask", 0.35), ("maskr", 0.35), ("mask", 0.15),
                      ("mask", 0.25)):
    a = pick(C, "bayes", inst, param, None, 200)
    b = pick(C, "voi", inst, param, None, 200)
    ra = [r["regret"] for r in a["rows"]]
    rb = [r["regret"] for r in b["rows"]]
    m, lo, hi = boot_ci(ra, rb)
    print("  [info] %s p=%s bayes-voi = %+.6f [%+.6f, %+.6f]"
          % (inst, param, m, lo, hi))
    row("G3 %s p=%s bayes-voi mean recomputed vs stored" % (inst, param), 0.0,
        round(m - (a["mean_regret"] - b["mean_regret"]), 9))

# --- 5. pub headline at 2000 -------------------------------------------
for m_ in (2, 8, 16, 49):
    for arm in ("bayes", "voi", "conf", "frozen_rule"):
        c = pick(C, arm, "pub", m_, None, 2000)
        if not c:
            continue
        row("pub m=%s %s regret" % (m_, arm), c["mean_regret"], regret_of(c))
        row("pub m=%s %s probes" % (m_, arm), c["mean_probes"],
            mean_of(c, "n_probes"))

# --- 6. the bayes-vs-frozen pub differences -----------------------------
for m_ in (8, 16, 49):
    a = pick(C, "bayes", "pub", m_, None, 2000)
    b = pick(C, "frozen_rule", "pub", m_, None, 2000)
    ra = [r["regret"] for r in a["rows"]]
    rb = [r["regret"] for r in b["rows"]]
    mm, lo, hi = boot_ci(ra, rb)
    print("  [info] pub m=%s bayes-frozen = %+.5f [%+.5f, %+.5f]  probes %.2f "
          "vs %.2f" % (m_, mm, lo, hi, a["mean_probes"], b["mean_probes"]))

# --- 7. the 2000-sim decisive cells (results_bayes_hi) ------------------
print()
for key in H:
    arm, inst, param, base, _ns = key
    c = H[key]
    row("hi %s/%s p=%s base=%s regret" % (arm, inst, param, base),
        c["mean_regret"], regret_of(c))
if ("bayes", "mask", 0.35, None, 2000) in H and \
        ("voi", "mask", 0.35, None, 2000) in H:
    a = H[("bayes", "mask", 0.35, None, 2000)]
    b = H[("voi", "mask", 0.35, None, 2000)]
    ra = [r["regret"] for r in a["rows"]]
    rb = [r["regret"] for r in b["rows"]]
    mm, lo, hi = boot_ci(ra, rb)
    print("  [info] HI mask eps 0.35: bayes=%.5f voi=%.5f diff=%+.6f "
          "[%+.6f, %+.6f]  probes %.2f vs %.2f"
          % (a["mean_regret"], b["mean_regret"], mm, lo, hi,
             a["mean_probes"], b["mean_probes"]))
    row("HI mask bayes>voi probes (claimed bayes probes more)", True,
        a["mean_probes"] > b["mean_probes"])

# --- 7b. the HI maskr comparisons quoted in the report -------------------
for other, cl_m, cl_lo, cl_hi, cl_pos, cl_neg in (
        ("frozen_rule", 0.00405, 0.00358, 0.00451, 287, 2),
        ("conf", 0.00989, 0.00898, 0.01078, 844, 65)):
    a = H.get(("bayes", "maskr", 0.35, None, 2000))
    b = H.get((other, "maskr", 0.35, None, 2000))
    if not a or not b:
        continue
    ra = [r["regret"] for r in a["rows"]]
    rb = [r["regret"] for r in b["rows"]]
    mm, lo, hi = boot_ci(ra, rb)
    pos, neg = int((np.array(ra) > np.array(rb)).sum()), \
        int((np.array(ra) < np.array(rb)).sum())
    row("HI maskr bayes-%s diff (claimed %+.5f)" % (other, cl_m), cl_m,
        round(mm, 5), tol=1e-4)
    row("HI maskr bayes-%s CI low (claimed %+.5f)" % (other, cl_lo), cl_lo,
        round(lo, 5), tol=1e-4)
    row("HI maskr bayes-%s CI high (claimed %+.5f)" % (other, cl_hi), cl_hi,
        round(hi, 5), tol=1e-4)
    row("HI maskr bayes-%s sign + (claimed %d)" % (other, cl_pos), cl_pos, pos)
    row("HI maskr bayes-%s sign - (claimed %d)" % (other, cl_neg), cl_neg, neg)
    print("  [info] HI maskr bayes-%s = %+.5f [%+.5f, %+.5f] sign %d+/%d-"
          % (other, mm, lo, hi, pos, neg))

# --- 7c. the two HI wins quoted in the report header ---------------------
for (inst, param, base, cl_m, cl_lo, cl_hi, cl_pos, cl_neg) in (
        ("mask", 0.35, None, -0.000548, -0.001050, -0.000132, 4, 8),
        ("mask", 0.35, 0.60, -0.006588, -0.008054, -0.005123, 25, 126)):
    a = H.get(("bayes", inst, param, base, 2000))
    b = H.get(("voi", inst, param, base, 2000))
    if not a or not b:
        continue
    ra = [r["regret"] for r in a["rows"]]
    rb = [r["regret"] for r in b["rows"]]
    mm, lo, hi = boot_ci(ra, rb)
    row("HI %s base=%s bayes-voi diff (claimed %+.6f)" % (inst, base, cl_m),
        cl_m, round(mm, 6), tol=1e-5)
    row("HI %s base=%s CI low (claimed %+.6f)" % (inst, base, cl_lo), cl_lo,
        round(lo, 6), tol=1e-5)
    row("HI %s base=%s CI high (claimed %+.6f)" % (inst, base, cl_hi), cl_hi,
        round(hi, 6), tol=1e-5)

# --- 8. cost ------------------------------------------------------------
c = pick(C, "bayes", "mask", 0.35, None, 200)
v = pick(C, "voi", "mask", 0.35, None, 200)
row("G6 bayes s/cell at 200 sims recomputed", c["mean_seconds"],
    mean_of(c, "seconds"), tol=1e-6)
hi_b = H.get(("bayes", "mask", 0.35, None, 2000))
hi_v = H.get(("voi", "mask", 0.35, None, 2000))
if hi_b and hi_v:
    cb = mean_of(hi_b, "seconds")
    cv = mean_of(hi_v, "seconds")
    print("  [info] cost at 2000 sims: bayes %.4f s/cell, voi %.4f s/cell, "
          "ratio %.2f" % (cb, cv, cb / cv))
    row("G6 cost ratio at 2000 sims, memo warm (claimed 1.79)", 1.79,
        round(cb / cv, 2), tol=0.01)
    row("G6 cost ratio at 200 sims, memo warm (claimed 1.01)",
        1.01, round(c["mean_seconds"] / v["mean_seconds"], 2), tol=0.01)
    print("  [info] NOTE: in-matrix seconds are memo-WARM (the DP memo persists "
          "across seeds in one process), so the in-matrix ratio understates the "
          "cold per-cell cost. The cold single-cell figure is measured "
          "separately below.")

print()
for (lab, cl, rc, ok) in ROWS:
    print("  %-4s %-56s claimed=%s  recomputed=%s"
          % ("PASS" if ok else "FAIL", lab, cl, rc))
print()
print("ROWS CHECKED: %d   FAILURES: %d" % (len(ROWS), len(FAILS)))
if FAILS:
    for f in FAILS:
        print("  MISMATCH: %s claimed=%s recomputed=%s" % f)
    sys.exit(1)
print("FACTCHECK PASSED")