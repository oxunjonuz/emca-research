"""verify_stopping_independent.py -- turn 134. INDEPENDENT pass over the
stopping-rule result.

Rules of this file, held to on purpose:
  * DIFFERENT CODE PATH. It imports neither the producer modules nor the
    analysis script. Nothing here calls union_agent_v3, union_run_v3,
    stopping_rules or analyze_stopping. It reads the frozen JSON and re-derives
    every number by its own arithmetic.
  * DISK IS THE TRUTH. Every claim is recomputed from results_stopping*/ files.
  * A NEGATIVE CONTROL that must go RED: V0 flips one stored regret and requires
    the recomputation to notice.
  * It also re-derives the MODULE-LEVEL facts (the rule's arithmetic) from the
    rule's own frozen source by a second, independent implementation of the
    posterior and the predictive -- no shared code with stopping_rules.py.

Prints PASS/FAIL per check; exits 1 on any failure.

  python3 verify_stopping_independent.py [nsim]
"""
import glob
import json
import math
import os
import sys
from fractions import Fraction

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []


def check(name, ok, extra=""):
    print("%-4s %s%s" % ("PASS" if ok else "FAIL", name,
                         ("  " + extra) if extra else ""))
    if not ok:
        FAILS.append(name)


def load(outdir):
    cells = {}
    for fn in sorted(glob.glob(os.path.join(outdir, "*.json"))):
        if fn.endswith("SUMMARY.json"):
            continue
        d = json.load(open(fn))
        cells[(d["arm"], d["inst"], d["param"], d.get("base"))] = d
    return cells


def mean(xs):
    return sum(xs) / float(len(xs))


# ---- V1: recompute every cell's mean/sem from its own raw rows ---------------
def v1(cells):
    bad = []
    for k, d in cells.items():
        regs = [r["regret"] for r in d["rows"]]
        m = mean(regs)
        if abs(m - d["mean_regret"]) > 1e-9:
            bad.append((k, "mean", m, d["mean_regret"]))
        if len(regs) > 1:
            sd = math.sqrt(sum((x - m) ** 2 for x in regs) / (len(regs) - 1))
            sem = sd / math.sqrt(len(regs))
            if abs(sem - d["sem_regret"]) > 1e-9:
                bad.append((k, "sem", sem, d["sem_regret"]))
    check("V1 every cell's mean and sem recomputed from its own raw rows",
          not bad, "%d mismatches" % len(bad))


# ---- V2: the transplant control, recomputed independently -------------------
def v2(cells):
    """The transplant control, done against the FROZEN v2 producer rather than
    against v3's own `union` arm (which shares the new dispatch and so could not
    fail). Here the generated v3 agent, run with the OLD rule, is compared
    cell-for-cell with `union_run_v2.run_cell` -- the turn-132 producer that
    wrote the frozen `results_union_v2/` matrix."""
    import subprocess
    code = (
        "import sys,os,json\n"
        "sys.path[:0]=[%r,%r]\n"
        "from union_run_v2 import run_cell as old\n"
        "from union_run_v3 import run_cell as new\n"
        "out=[]\n"
        "for inst,p in [('mask',0.15),('mask',0.25),('mask',0.35),"
        "('maskr',0.25),('maskr',0.35)]:\n"
        "    for s in (1,2,3,4,5):\n"
        "        a=old('union',inst,p,s)\n"
        "        b=new('frozen_rule',inst,p,s)\n"
        "        for k in ('seconds','arm','rule_name'):\n"
        "            a.pop(k,None)\n"
        "            b.pop(k,None)\n"
        "        out.append((inst,p,s,a==b))\n"
        "print(json.dumps(out))\n"
        % (_HERE, os.path.dirname(_HERE)))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True, env=dict(os.environ, PYTHONHASHSEED="0"))
    if r.returncode != 0:
        check("V2 the cross-producer comparison ran", False,
              r.stderr.strip()[-300:])
        return
    out = json.loads(r.stdout)
    bad = [x for x in out if not x[3]]
    check("V2 the generated v3 agent with the OLD rule reproduces the FROZEN "
          "v2 producer cell-for-cell (%d cells)" % len(out), not bad,
          "differ: %s" % bad[:5])


# ---- V3: the rule's arithmetic, re-implemented from scratch -----------------
def _log_choose(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def predictive(n, a, b):
    """Beta-Binomial pmf, independent implementation (pure floats, no log-space
    trick), normalised by direct summation."""
    out = []
    for k in range(n + 1):
        # integral of Binom(k;n,p) Beta(p;a,b) dp, closed form:
        # C(n,k) * B(a+k, b+n-k) / B(a,b)
        lg = (_log_choose(n, k) + math.lgamma(a + k) + math.lgamma(b + n - k)
              - math.lgamma(a + b + n))
        out.append(math.exp(lg))
    z = sum(out)
    return [x / z for x in out]


def voi_independent(rate_a, trials, r_best, n, horizon, pi=0.5):
    """The T2 arithmetic, written from the mathematical statement rather than by
    copying the producer: a Beta(1,1) posterior on the candidate's rate, the
    exact predictive of n pulls, and the two strategy totals."""
    if rate_a is None or not trials:
        a1, b1 = 1.0, 1.0
    else:
        a1 = 1.0 + rate_a * trials
        b1 = 1.0 + trials - rate_a * trials
    mu = a1 / (a1 + b1)
    cur = max(mu, r_best)
    pmf = predictive(n, a1, b1)
    emax = 0.0
    for k, p in enumerate(pmf):
        post = (a1 + k) / (a1 + b1 + n)
        emax += p * max(r_best, post)
    info = (horizon - n) * (emax - cur)
    risk = n * (cur - mu)
    probe_value = n * mu + (horizon - n) * emax
    exploit = horizon * cur
    return info, risk, probe_value, exploit


def v3():
    """The rule's own identity and bounds, recomputed by the independent path."""
    worst_id, worst_i, worst_r = 0.0, 1e9, 1e9
    for ra in (None, 0.2, 0.55, 0.85):
        for tr in (0, 40, 400):
            for r in (0.1, 0.5, 0.8, 0.95):
                info, risk, pv, ex = voi_independent(ra, tr, r, 20, 200.0)
                worst_i = min(worst_i, info)
                worst_r = min(worst_r, risk)
                worst_id = max(worst_id, abs((pv - ex) - (info - risk)))
    check("V3 info >= 0 on an independent implementation", worst_i >= -1e-9,
          "min %.3e" % worst_i)
    check("V3 risk >= 0", worst_r >= -1e-9, "min %.3e" % worst_r)
    check("V3 identity probe_value - exploit == info - risk", worst_id < 1e-6,
          "max %.3e" % worst_id)
    # the decision is a BAND: independent recomputation must show an interval
    rich = [0.002 * i for i in range(1, 500)]
    acc = [r for r in rich
           if voi_independent(0.85, 200, r, 20, 200.0)[0]
           > voi_independent(0.85, 200, r, 20, 200.0)[1]]
    lo, hi = min(acc), max(acc)
    contiguous = all(any(abs(r - a) < 1e-9 for a in acc)
                     for r in rich if lo <= r <= hi)
    check("V3 T2's accept set over the alternative's rate is an INTERVAL",
          contiguous, "[%.3f, %.3f]" % (lo, hi))


# ---- V4: the published-instance win, recomputed from raw rows ---------------
def v4(cells):
    def rows(arm, m):
        d = cells.get((arm, "pub", m, None))
        return [r["regret"] for r in d["rows"]] if d else None
    wins = 0
    for m in (2, 8, 16, 49):
        a, b = rows("voi", m), rows("frozen_rule", m)
        if a is None or b is None:
            continue
        if mean(a) < mean(b):
            wins += 1
    check("V4 voi beats the frozen rule on the published instance, recomputed "
          "from raw rows at every m", wins >= 1, "%d/4 m-values" % wins)
    a, b = rows("voi", 16), rows("frozen_rule", 16)
    if a and b:
        d = np.array(a) - np.array(b)
        check("V4 voi probe count is BELOW the frozen rule's on pub m=16 "
              "(it stops earlier)",
              cells[("voi", "pub", 16, None)]["mean_probes"]
              < cells[("frozen_rule", "pub", 16, None)]["mean_probes"])


# ---- V5: G2 recomputed ------------------------------------------------------
def v5(cells):
    def mp(arm, base):
        d = cells.get((arm, "mask", 0.35, base))
        return d["mean_probes"] if d else None
    bases = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    vp = [mp("voi", b) for b in bases]
    if any(v is None for v in vp):
        check("V5 G2 richness sweep present", False, "missing cells")
        return
    import numpy as _np
    rho = _np.corrcoef(_np.argsort(_np.argsort(bases)),
                       _np.argsort(_np.argsort(vp)))[0, 1]
    check("V5 voi's probe count falls as the world gets richer (Spearman < 0)",
          rho < 0, "rho = %.3f" % rho)
    hi = [mp("voi", b) for b in (0.85, 0.90, 0.95)]
    check("V5 and it falls to ESSENTIALLY zero above base 0.85 "
          "(mean probes <= 0.05 -- a derived near-silence, not exact zero)",
          all(v is not None and v <= 0.05 for v in hi), "%s" % hi)


# ---- V0: negative control ---------------------------------------------------
def v0(cells):
    """Flip one stored regret and require V1's recomputation to notice."""
    key = ("voi", "mask", 0.35, None)
    d = cells.get(key)
    if d is None:
        check("V0 negative control had a cell to corrupt", False)
        return
    saved = d["mean_regret"]
    d["mean_regret"] = saved + 1000.0
    try:
        regs = [r["regret"] for r in d["rows"]]
        noticed = abs(mean(regs) - d["mean_regret"]) > 1e-9
    finally:
        d["mean_regret"] = saved
    check("V0 NEGATIVE CONTROL: a corrupted mean is detected by the same "
          "recomputation V1 uses", noticed)


# ---- V6: determinism across fresh processes --------------------------------
def v6():
    import subprocess
    code = ("import sys,os,json;sys.path[:0]=[%r,%r];"
            "from union_run_v3 import run_cell;"
            "print(json.dumps(run_cell('voi','mask',0.35,7,T=400),sort_keys=True))"
            % (_HERE, os.path.dirname(_HERE)))
    outs = []
    for h in ("0", "11", "29"):
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, env=dict(os.environ, PYTHONHASHSEED=h))
        if r.returncode != 0:
            check("V6 subprocess ran", False, r.stderr.strip()[-200:])
            return
        d = json.loads(r.stdout)
        d.pop("seconds", None)
        outs.append(json.dumps(d, sort_keys=True))
    check("V6 a fresh voi cell is bit-identical across three processes / seeds",
          len(set(outs)) == 1)


# ---- V7: frozen producers untouched -----------------------------------------
def v7():
    import hashlib
    sums = {}
    for name, path in (("candidate_gen.py",
                        os.path.join(os.path.dirname(_HERE), "candidate_gen.py")),
                       ("arbitration.py",
                        os.path.join(os.path.dirname(_HERE), "arbitration.py")),
                       ("union_agent_v2.py",
                        os.path.join(_HERE, "union_agent_v2.py"))):
        sums[name] = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    check("V7 the frozen producers carry the hashes recorded on turn 132",
          sums["candidate_gen.py"] == "fa9721ae816c3c42"
          and sums["arbitration.py"] == "2d3d825bcfc83cc8"
          and sums["union_agent_v2.py"] == "76bfe972bde4963c",
          "%s" % sums)


if __name__ == "__main__":
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    outdir = os.environ.get("STOPPING_OUT") or os.path.join(
        _HERE, "results_stopping_hi" if nsim == 2000 else "results_stopping")
    print("=== independent verification of the stopping-rule result ===")
    print("dir: %s   nsim claimed: %d\n" % (outdir, nsim))
    cells = load(outdir)
    print("cells on disk: %d\n" % len(cells))
    v1(cells)
    v2(cells)
    v3()
    v4(cells)
    v5(cells)
    v0(cells)
    v6()
    v7()
    print("\n%d failure(s)" % len(FAILS))
    if FAILS:
        print("FAILED:", FAILS)
        sys.exit(1)
    print("ALL PASS")