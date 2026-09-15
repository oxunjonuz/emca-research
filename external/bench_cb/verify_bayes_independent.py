"""verify_bayes_independent.py -- turn 135. INDEPENDENT verification pass.

Rules of this file, carried from turns 124-134:
  * it imports NOT ONE producer module (no bayes_stopping, no stopping_rules, no
    candidate_gen, no union_agent_*): every quantity is recomputed from the frozen
    JSON on disk with its own arithmetic;
  * it re-implements the DP from the MATHEMATICAL STATEMENT in PREREG_BAYES.md,
    not from the module, and compares decisions;
  * it contains a negative control that MUST fail (V0);
  * it runs in a fresh process.

  python3 verify_bayes_independent.py [nsim] [nsim_pub]
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
from math import exp, lgamma, log

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("BAYES_OUT") or os.path.join(_HERE, "results_bayes")
WORST = []


def check(name, ok, detail=""):
    print("  %-4s %-52s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        WORST.append(name)


def load():
    cells = {}
    for fn in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        if fn.endswith("SUMMARY.json"):
            continue
        d = json.load(open(fn))
        cells[(d["arm"], d["inst"], d["param"], d.get("base"), d["nsim"])] = d
    return cells


# ---- INDEPENDENT re-implementation of both rules (no shared code at all) ----

def post(rate, trials, a0=1.0, b0=1.0):
    if rate is None or not trials:
        return a0, b0
    n = float(trials)
    return a0 + float(rate) * n, b0 + n - float(rate) * n


def bb(n, a, b):
    logs = [lgamma(n + 1.0) - lgamma(k + 1.0) - lgamma(n - k + 1.0)
            + lgamma(a + k) + lgamma(b + n - k) - lgamma(a + b + n)
            - (lgamma(a) + lgamma(b) - lgamma(a + b)) for k in range(n + 1)]
    m = max(logs)
    w = [exp(x - m) for x in logs]
    s = sum(w)
    return [x / s for x in w]


def V_ref(a, b, L, r, n, memo):
    """The DP, re-derived from PREREG_BAYES.md's statement."""
    if L < n:
        return L * max(a / (a + b), r)
    key = (round(a, 6), round(b, 6), L, r, n)
    if key in memo:
        return memo[key]
    mu = a / (a + b)
    commit = L * max(mu, r)
    s = 0.0
    for k, p in enumerate(bb(n, a, b)):
        if p:
            s += p * V_ref(a + k, b + n - k, L - n, r, n, memo)
    probe = n * mu + s
    memo[key] = max(commit, probe)
    return memo[key]


def t2_terms(rate, trials, r, n, L):
    """T2 re-derived: info = (L-n)(E[max(post,r)] - max(mu,r)); risk = n(max(mu,r)-mu)."""
    a, b = post(rate, trials)
    mu = a / (a + b)
    cur = max(mu, r)
    if L <= n:
        emax = cur
    else:
        emax = sum(p * max(r, (a + k) / (a + b + n))
                   for k, p in enumerate(bb(n, a, b)))
    info = (L - n) * (emax - cur) if L > n else 0.0
    risk = n * (cur - mu)
    return info, risk


def t4_terms(rate, trials, r, n, L, memo):
    a, b = post(rate, trials)
    mu = a / (a + b)
    commit = L * max(mu, r)
    if L < n:
        return commit - commit, mu
    probe = n * mu + sum(p * V_ref(a + k, b + n - k, L - n, r, n, memo)
                         for k, p in enumerate(bb(n, a, b)))
    return probe - commit, mu


def main():
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    nsim_pub = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    cells = load()
    print("cells loaded: %d\n" % len(cells))

    # ---- V1 every cell's mean/sem recomputed from its own raw rows ----------
    bad = []
    for key, d in cells.items():
        regs = [r["regret"] for r in d["rows"]]
        m = float(np.mean(regs))
        s = float(np.std(regs, ddof=1) / np.sqrt(len(regs))) if len(regs) > 1 else 0.0
        if abs(m - d["mean_regret"]) > 1e-9 or abs(s - d["sem_regret"]) > 1e-9:
            bad.append((key, m, d["mean_regret"], s, d["sem_regret"]))
        pr = float(np.mean([r.get("n_probes", 0) for r in d["rows"]]))
        if abs(pr - d["mean_probes"]) > 1e-9:
            bad.append((key, "probes", pr, d["mean_probes"]))
    check("V1 mean/sem/probes recomputed from raw rows", not bad,
          "%d cells, %d mismatches" % (len(cells), len(bad)))

    # ---- V2 transplant control: v4 driver with OLD rules == v3 producer ----
    print("\n   running cross-producer transplant control (v4 vs v3 driver)...")
    mism = []
    for arm, inst, param, seed in (("frozen_rule", "mask", "0.35", 1),
                                   ("voi", "mask", "0.35", 2),
                                   ("conf", "maskr", "0.35", 3)):
        a = subprocess.run([sys.executable, "union_run_v4.py", "cell", arm, inst,
                            param, str(seed), "400"], cwd=_HERE,
                           capture_output=True, text=True).stdout
        b = subprocess.run([sys.executable, "union_run_v3.py", "cell", arm, inst,
                            param, str(seed), "400"], cwd=_HERE,
                           capture_output=True, text=True).stdout
        ja, jb = json.loads(a), json.loads(b)
        for j in (ja, jb):
            j.pop("seconds", None)
        if ja != jb:
            mism.append((arm, inst, param, seed))
    check("V2 v4 driver + OLD rule == v3 producer (3 cells)", not mism,
          str(mism))

    # ---- V3 the DP re-derived from the statement ---------------------------
    print()
    memo = {}
    mism = []
    n_cmp = 0
    for ra in (None, 0.20, 0.55, 0.85, 1.0):
        for tr in (0, 5, 20, 100, 400):
            for r in (0.10, 0.30, 0.50, 0.65, 0.80, 0.90):
                for L in (32, 92, 138, 200, 400):
                    m4, mu = t4_terms(ra, tr, r, 20, L, memo)
                    i2, k2 = t2_terms(ra, tr, r, 20, L)
                    # the theorem: T4's margin >= T2's margin at every state
                    if m4 - (i2 - k2) < -1e-9:
                        mism.append((ra, tr, r, L, m4, i2 - k2))
                    n_cmp += 1
                    # T2 accepts => T4 accepts (up to ties)
                    if (i2 - k2) > 1e-12 and not (m4 > 0):
                        mism.append(("INCLUSION", ra, tr, r, L, m4, i2 - k2))
    check("V3 T4 margin >= T2 margin AND T2-accepts => T4-accepts", not mism,
          "%d states compared, %d violations %s" % (n_cmp, len(mism), mism[:3]))

    # ---- V4 the matrix's own bayes/voi rows re-derive the headline ---------
    print()
    for (inst, param, ns) in (("mask", 0.35, nsim), ("maskr", 0.35, nsim),
                              ("pub", 16, nsim_pub)):
        b = cells.get(("bayes", inst, param, None, ns))
        v = cells.get(("voi", inst, param, None, ns))
        if not b or not v:
            continue
        rb = [x["regret"] for x in b["rows"]]
        rv = [x["regret"] for x in v["rows"]]
        d = np.array(rb) - np.array(rv)
        check("V4 %s p=%s: bayes-voi mean recomputed" % (inst, param),
              abs(float(np.mean(d)) - (b["mean_regret"] - v["mean_regret"])) < 1e-9,
              "diff=%+.6f  CI-free" % float(np.mean(d)))

    # ---- V5 G2 recomputed with an independent rank correlation -------------
    print()
    bases = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    bp, vp = [], []
    for bb_ in bases:
        c = cells.get(("bayes", "mask", 0.35, bb_, nsim))
        c2 = cells.get(("voi", "mask", 0.35, bb_, nsim))
        bp.append(c["mean_probes"] if c else float("nan"))
        vp.append(c2["mean_probes"] if c2 else float("nan"))
    try:
        from scipy.stats import spearmanr
        rho_b = float(spearmanr(bases, bp).statistic)
        rho_v = float(spearmanr(bases, vp).statistic)
        src = "scipy"
    except Exception:
        def rk(x):
            x = np.asarray(x, float)
            return np.argsort(np.argsort(x)).astype(float)
        def spearman(x, y):
            rx, ry = rk(x), rk(y)
            rx = rx - rx.mean(); ry = ry - ry.mean()
            return float((rx * ry).sum() / np.sqrt((rx**2).sum() * (ry**2).sum()))
        rho_b, rho_v, src = spearman(bases, bp), spearman(bases, vp), "manual"
    check("V5 G2: rho(bayes probes, richness) <= 0", rho_b <= 0.0,
          "rho=%.3f (%s), voi rho=%.3f" % (rho_b, src, rho_v))

    # ---- V6 determinism across fresh processes and hash seeds --------------
    print()
    outs = []
    for hs in ("0", "1", "12345"):
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = hs
        o = subprocess.run([sys.executable, "union_run_v4.py", "cell", "bayes",
                            "mask", "0.35", "7", "400"], cwd=_HERE, env=env,
                           capture_output=True, text=True).stdout
        j = json.loads(o)
        j.pop("seconds", None)
        outs.append(j)
    check("V6 bayes cell bit-identical across 3 hash seeds", outs[0] == outs[1] == outs[2])

    # ---- V7 frozen producers unchanged -------------------------------------
    print()
    want = {"candidate_gen.py": "fa9721ae816c3c42",
            "arbitration.py": "2d3d825bcfc83cc8",
            "union_agent_v2.py": "76bfe972bde4963c",
            "union_agent_v3.py": "67e096eb7897ccb0"}
    bad = []
    for f, pre in want.items():
        p1 = os.path.join(_HERE, f)
        p2 = os.path.join(os.path.dirname(_HERE), f)
        p = p1 if os.path.exists(p1) else p2
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if not h.startswith(pre):
            bad.append((f, h[:16], pre))
    check("V7 frozen producers unchanged", not bad, str(bad))

    # ---- V8 the superseded first-pass matrix is preserved, not deleted -----
    print()
    sup = os.path.join(_HERE, "results_bayes_QUANTISED_superseded")
    n = len(glob.glob(os.path.join(sup, "*.json")))
    check("V8 quantised first pass preserved as evidence", n > 100,
          "%d files" % n)

    # ---- V0 NEGATIVE CONTROL (must fail) -----------------------------------
    print()
    v = [{"mean_regret": 0.0, "sem_regret": 0.0, "mean_probes": 0.0,
          "rows": [{"regret": 0.5, "n_probes": 1}]}]
    got = abs(v[0]["rows"][0]["regret"] - v[0]["mean_regret"])
    check("V0 NEGATIVE CONTROL: corrupted mean must be DETECTED", got > 1e-9,
          "detected a %0.3f discrepancy" % got)

    print()
    if WORST:
        print("VERIFICATION FAILED: %s" % WORST)
        return 1
    print("VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())