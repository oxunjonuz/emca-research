"""analyze_v8.py -- primary pass over the V8 matrix (PREREG_V8 §3).

Implements the frozen three-leg gate for every primary contrast:
  (1) paired bootstrap CI (10 000 resamples) excludes 0;
  (2) one-sided paired sign test p < 0.05 in the predicted direction;
  (3) the two halves of each run's second half (epochs 4-5 and 6-7) agree
      in sign with the full-run difference.
Reads only results/matrix_v8/*.json. Prints the report to stdout.

Usage: python3 analyze_v8.py > results/analysis_v8.txt
"""
import glob
import json
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_v8")
from agent_emca_v8 import (two_prop_z, gamma_of, fisher_exact_2x2,
                           RR_ACCEPT)   # the frozen rule's own arithmetic
GAPS = ["0.20", "0.10", "0.05", "0.03"]
QS = [0.0, 0.25, 0.5, 0.75, 1.0]
ACT = ("wait", "press", "grasp")
P_BG = 0.35
P_EDGE = {"0.20": 0.55, "0.10": 0.45, "0.05": 0.40, "0.03": 0.38}


def load():
    runs = {}
    for f in glob.glob(os.path.join(D, "*.json")):
        with open(f) as fh:
            d = json.load(fh)
        runs[os.path.basename(f)[:-5]] = d
    return runs


def tag(arm, seed, gap, q, persist, truth=True):
    return (f"{arm}_s{seed}_g{gap}_q{q}_{'p' if persist else 'n'}"
            f"_{'on' if truth else 'off'}")


def get(runs, arm, seed, gap, q=0.0, persist=False, truth=True):
    return runs.get(tag(arm, seed, gap, q, persist, truth))


def boot_ci(diffs, reps=10000, seed=12345):
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(reps):
        means.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return means[int(0.025 * reps)], means[int(0.975 * reps) - 1]


def sign_p_dir(diffs, predict):
    """One-sided sign test in the DECLARED direction. `predict` = +1
    (A > B expected), -1 (A < B expected), 0 (direction not declared:
    report the measured direction with a two-sided test). Zeros dropped.
    Returns (p, k_positive, n)."""
    nz = [d for d in diffs if d != 0]
    if not nz:
        return 1.0, 0, 0
    k = sum(1 for d in nz if d > 0)
    n = len(nz)
    if predict >= 0:
        p = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    else:
        p = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    if predict == 0:                       # two-sided
        p = min(1.0, 2.0 * min(
            sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n),
            sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)))
    return min(1.0, p), k, n


def halves(a, b, key="per_epoch_reward"):
    """Difference between arms a and b in each half of the second half of
    the run (epochs 4-5 and 6-7)."""
    def s(d, lo, hi):
        return sum(d[key][lo:hi])
    h1 = s(a, 4, 6) - s(b, 4, 6)
    h2 = s(a, 6, 8) - s(b, 6, 8)
    return h1, h2


def _get(runs, spec, seed, gap, q):
    return runs.get(tag(spec["arm"], seed, gap, q,
                        spec.get("persist", False), spec.get("truth", True)))


def contrast(runs, specA, specB, gap, q=0.0, seeds=range(8), label="",
             predict=1):
    """The frozen three-leg gate on reward(A) - reward(B), paired by seed.
    specA/specB are dicts {arm, persist, truth} so that arm sets differing
    only in a KNOB (e.g. the amortization cache) can be compared."""
    if isinstance(specA, str):
        specA = {"arm": specA}
    if isinstance(specB, str):
        specB = {"arm": specB}
    diffs, A, B, h1s, h2s, keys = [], [], [], [], [], []
    for s in seeds:
        a = _get(runs, specA, s, gap, q)
        b = _get(runs, specB, s, gap, q)
        if a is None or b is None:
            continue
        diffs.append(a["total_reward"] - b["total_reward"])
        A.append(a["total_reward"])
        B.append(b["total_reward"])
        h1, h2 = halves(a, b)
        h1s.append(h1)
        h2s.append(h2)
        keys.append(s)
    if not diffs:
        return None
    lo, hi = boot_ci(diffs)
    p, k, n = sign_p_dir(diffs, predict)
    full_sign = 1 if statistics.mean(diffs) > 0 else -1
    hs1 = 1 if statistics.mean(h1s) > 0 else -1
    hs2 = 1 if statistics.mean(h2s) > 0 else -1
    leg1 = (lo > 0) or (hi < 0)
    leg2 = p < 0.05
    # leg 3 reads the halves against the DECLARED direction when one was
    # declared (predict != 0), against the observed sign otherwise.
    target = predict if predict != 0 else full_sign
    leg3 = (hs1 == target and hs2 == target)
    print(f"  {label or (specA['arm']+' - '+specB['arm'])} gap {gap} q={q} "
          f"persist A={'on' if specA.get('persist') else 'off'} "
          f"B={'on' if specB.get('persist') else 'off'} "
          f"truth={'on' if specA.get('truth', True) else 'off'}")
    print(f"    mean A {statistics.mean(A):10.1f}  mean B {statistics.mean(B):10.1f}  "
          f"paired diff {statistics.mean(diffs):9.1f}  CI [{lo:.0f}, {hi:.0f}]")
    print(f"    sign {k}/{n} p={p:.4f} (predicted {'A>B' if predict>0 else ('A<B' if predict<0 else 'two-sided')})"
          f"   halves {hs1:+d}/{hs2:+d} vs target {target:+d}   legs: "
          f"CI={'PASS' if leg1 else 'FAIL'} sign={'PASS' if leg2 else 'FAIL'} "
          f"halves={'PASS' if leg3 else 'FAIL'}  -> "
          f"{'PASS' if (leg1 and leg2 and leg3) else 'FAIL'}")
    return {"diff": statistics.mean(diffs), "ci": (lo, hi), "p": p, "k": k,
            "n": n, "legs": (leg1, leg2, leg3), "seeds": keys,
            "h1": statistics.mean(h1s), "h2": statistics.mean(h2s),
            "meanA": statistics.mean(A), "meanB": statistics.mean(B),
            "sign": full_sign}


def observed_gap(run):
    """The agent's own end-of-epoch contrast, from its own counts:
    rate(true action) - rate(others pooled)."""
    out = []
    for k, row in enumerate(run["epoch_log"]):
        if k >= len(run["epoch_actions_true"]):
            break
        if row.get("n", 0) == 0:
            continue
        true_a = run["epoch_actions_true"][k]
        c = row["counts"]
        h, n = c[true_a]
        oh = sum(v[0] for a, v in c.items() if a != true_a)
        on = sum(v[1] for a, v in c.items() if a != true_a)
        if n == 0 or on == 0:
            continue
        out.append(h / n - oh / on)
    return out


def main():
    runs = load()
    print("=" * 74)
    print("V8 ANALYSIS -- continuous confidence / self-reinforcement / "
          "amortization")
    print("=" * 74)
    print(f"runs loaded: {len(runs)}")

    # ---------------- Block C ----------------
    print("\n### BLOCK C -- CONTINUOUS CONFIDENCE (three-leg gate)")
    resC = {}
    for gap in GAPS:
        print(f"\n -- gap {gap} (p_edge {P_EDGE[gap]} vs 0.35) --")
        resC[gap] = {}
        resC[gap]["C1"] = contrast(runs, "graded", "threshold", gap,
                                   label="C1 graded-threshold")
        resC[gap]["C2"] = contrast(runs, "graded", "coin", gap,
                                   label="C2 graded-coin (information)")
        resC[gap]["C3"] = contrast(runs, "threshold", "coin", gap,
                                   label="C3 threshold-coin (verdict vs coin)")

    print("\n  C4 PRICE: steps spent gathering, mean over seeds")
    print(f"    {'arm':16s}" + "".join(f"{g:>10s}" for g in GAPS))
    for arm in ("graded", "graded1", "threshold", "thresholdpool", "coin",
                "oracle", "rot"):
        row = []
        for gap in GAPS:
            v = [get(runs, arm, s, gap) for s in range(8)]
            v = [x for x in v if x]
            row.append(statistics.mean(x["steps_gathering"] for x in v)
                       if v else float("nan"))
        print(f"    {arm:16s}" + "".join(f"{x:10.0f}" for x in row))
    print("\n  C4 PRICE: reward, mean over seeds")
    print(f"    {'arm':16s}" + "".join(f"{g:>10s}" for g in GAPS))
    for arm in ("graded", "graded1", "threshold", "thresholdpool", "coin",
                "oracle", "rot"):
        row = []
        for gap in GAPS:
            v = [get(runs, arm, s, gap) for s in range(8)]
            v = [x for x in v if x]
            row.append(statistics.mean(x["total_reward"] for x in v)
                       if v else float("nan"))
        print(f"    {arm:16s}" + "".join(f"{x:10.0f}" for x in row))

    print("\n  C4 PRICE: fraction of effort spent acquiring evidence "
          "(steps_gathering / steps), graded vs threshold")
    for gap in GAPS:
        g = [get(runs, "graded", s, gap) for s in range(8)]
        t = [get(runs, "threshold", s, gap) for s in range(8)]
        g = [x for x in g if x]
        t = [x for x in t if x]
        fr = statistics.mean(x["steps_gathering"] / x["steps"] for x in g)
        tr = statistics.mean(x["steps_gathering"] / x["steps"] for x in t)
        print(f"    gap {gap}: graded {fr:.3f}  threshold {tr:.3f}  "
              f"ratio {tr/fr if fr else float('nan'):.2f}")

    print("\n  C4b AGENT-LEVEL evidence demand: per epoch, the step at which "
          "each rule first acquires a belief, in units of its own evidence")
    print(f"    {'gap':6s}{'graded n@gamma>0.5':>22s}{'threshold n@fire':>20s}"
          f"{'ratio':>8s}{'threshold fire rate':>22s}")
    for gap in GAPS:
        gn, tn, fires, tot = [], [], 0, 0
        for s in range(8):
            rg = get(runs, "graded", s, gap)
            rt = get(runs, "threshold", s, gap)
            if rg:
                for k, row in enumerate(rg["epoch_log"]):
                    if k >= len(rg["epoch_actions_true"]) or row.get("n", 0) == 0:
                        continue
                    ta = rg["epoch_actions_true"][k]
                    c = row["counts"]
                    h, n = c[ta]
                    oh = sum(v[0] for a, v in c.items() if a != ta)
                    on = sum(v[1] for a, v in c.items() if a != ta)
                    if n and on:
                        # the number of trials-per-action at which this
                        # epoch's evidence would first cross 0.5, read
                        # from the run's own end-of-epoch contrast
                        z_end = two_prop_z(h, n, oh, on)
                        n_tri = n
                        # scale: gamma>0.5 needs z>=0.674; the z achieved
                        # at n trials scales as sqrt(n), so n* =
                        # n*(0.674/z_end)^2 when z_end>0.674
                        if z_end > 0.674:
                            gn.append(n_tri * (0.674 / z_end) ** 2)
            if rt:
                for k, row in enumerate(rt["epoch_log"]):
                    if k >= len(rt["epoch_actions_true"]) or row.get("n", 0) == 0:
                        continue
                    ta = rt["epoch_actions_true"][k]
                    c = row["counts"]
                    cand = max(c, key=lambda a: (c[a][0] / c[a][1]) if c[a][1] else 0)
                    h, n = c[cand]
                    others = [a for a in c if a != cand]
                    hc, nc = c[others[0]]
                    if n and nc:
                        rr = (h / n) / (hc / nc) if hc else float("inf")
                        p = fisher_exact_2x2(h, hc, n - h, nc - hc)
                        fires += 1 if (p < 0.05 and rr >= RR_ACCEPT) else 0
                        tot += 1
                        if p < 0.05 and rr >= RR_ACCEPT:
                            tn.append(n)
        if gn and tn:
            print(f"    {gap:6s}{statistics.mean(gn):22.0f}"
                  f"{statistics.mean(tn):20.0f}"
                  f"{statistics.mean(tn)/statistics.mean(gn):8.2f}"
                  f"{fires/tot if tot else float('nan'):22.3f}")
        else:
            print(f"    {gap:6s}{'n/a':>22s}{'n/a':>20s}{'n/a':>8s}"
                  f"{fires/tot if tot else float('nan'):22.3f}")
    for gap in GAPS:
        gt, gf = [], []
        for s in range(8):
            r = get(runs, "graded", s, gap)
            if not r:
                continue
            for k, row in enumerate(r["epoch_log"]):
                if k >= len(r["epoch_actions_true"]) or row.get("n", 0) < 20:
                    continue
                true_a = r["epoch_actions_true"][k]
                c = row["counts"]
                h, n = c[true_a]
                oh = sum(v[0] for a, v in c.items() if a != true_a)
                on = sum(v[1] for a, v in c.items() if a != true_a)
                if n == 0 or on == 0:
                    continue
                gt.append(gamma_of(two_prop_z(h, n, oh, on)))
                for a in ACT:
                    if a == true_a:
                        continue
                    ha, na = c[a]
                    oh2 = sum(v[0] for b, v in c.items() if b != a)
                    on2 = sum(v[1] for b, v in c.items() if b != a)
                    if na and on2:
                        gf.append(gamma_of(two_prop_z(ha, na, oh2, on2)))
        if gt and gf:
            try:
                from scipy.stats import mannwhitneyu
                u, pmw = mannwhitneyu(gt, gf, alternative="greater")
            except Exception:
                pmw = float("nan")
            print(f"    gap {gap}: mean gamma true {statistics.mean(gt):.4f} "
                  f"(n={len(gt)}) vs false {statistics.mean(gf):.4f} "
                  f"(n={len(gf)})  MW p={pmw:.3e}  -> "
                  f"{'PASS' if statistics.mean(gt) > statistics.mean(gf) and pmw < 0.05 else 'FAIL'}")

    # ---------------- Block A ----------------
    print("\n### BLOCK A -- SELF-REINFORCEMENT AS A BATTERY")
    print("\n  A1 the loop's size: agent's own end-of-epoch contrast "
          "(rate_true - rate_others), persistence on vs off")
    print(f"    {'gap':6s} {'arm':8s} {'persist':8s} {'observed':>10s} "
          f"{'true':>8s} {'ratio':>7s} {'analytic':>9s}")
    for gap in ("0.20", "0.10"):
        for arm in ("graded", "rot"):
            for persist in (False, True):
                vals = []
                for s in range(8):
                    r = get(runs, arm, s, gap, 0.0, persist)
                    if not r:
                        continue
                    vals.extend(observed_gap(r))
                if not vals:
                    continue
                true_gap = P_EDGE[gap] - P_BG
                ana = (P_EDGE[gap] * 1.25 - P_BG) if persist else true_gap
                print(f"    {gap:6s} {arm:8s} "
                      f"{'on' if persist else 'off':8s} "
                      f"{statistics.mean(vals):10.4f} {true_gap:8.4f} "
                      f"{statistics.mean(vals)/true_gap:7.2f} {ana:9.4f}")

    print("\n  A1 verdicts (analytic vs measured, tolerance ±0.03; prereg A7)"
          "\n    prediction applies to the arm that can reach the 75% "
          "consistency (graded); rot is the CONTROL and its expected value "
          "is the TRUE gap in both regimes (prereg A17)")
    from env_terrarium_v8 import P_BG as _pb
    a1_rows = []
    for gap in ("0.20", "0.10"):
        for arm in ("graded", "rot"):
            for persist in (False, True):
                vals = []
                for s in range(8):
                    r = get(runs, arm, s, gap, 0.0, persist)
                    if not r:
                        continue
                    vals.extend(observed_gap(r))
                if not vals:
                    continue
                measured = statistics.mean(vals)
                true_gap = P_EDGE[gap] - _pb
                if arm == "graded" and persist:
                    ana = P_EDGE[gap] * 1.25 - _pb
                else:
                    ana = true_gap      # control, or no consistency payment
                ok = abs(measured - ana) < 0.03
                a1_rows.append(ok)
                print(f"    [{'PASS' if ok else 'FAIL'}] gap {gap} {arm:7s} "
                      f"persist={'on ' if persist else 'off'} measured "
                      f"{measured:.4f} vs expected {ana:.4f}")
    print(f"    A1 overall: {'PASS' if all(a1_rows) else 'FAIL'} "
          f"({sum(a1_rows)}/{len(a1_rows)} legs)")

    print("\n  A2b THE CLEAN WITHIN-WORLD CONTRAST (the interesting one): "
          "in a world that PAYS CONSISTENCY, does acting on a belief pay? "
          "graded - rot, persistence ON, same seeds")
    for gap in ("0.20", "0.10"):
        contrast(runs, {"arm": "graded", "persist": True},
                 {"arm": "rot", "persist": True}, gap, predict=1,
                 label="A2b graded-rot (persist ON)")
    for gap in ("0.20", "0.10"):
        contrast(runs, {"arm": "graded", "persist": False},
                 {"arm": "rot", "persist": False}, gap, predict=1,
                 label="A2c graded-rot (persist OFF, the same contrast "
                       "without the consistency payment)")

    print("\n  A2d how much of the persist-ON reward gap is the world's own "
          "enrichment (not the agent's)? oracle is free evidence, so its "
          "advantage over rot in the two worlds bounds it")
    for persist in (False, True):
        v = get(runs, "oracle", 0, "0.20", 0.0, persist)
        print(f"    persist={'on' if persist else 'off'}: oracle at gap 0.20 "
              f"seed 0 reward {v['total_reward'] if v else 'n/a'} vs rot "
              f"{get(runs,'rot',0,'0.20',0.0,persist)['total_reward']}")

    print("\n  A4 direction battery: does the belief identify the "
          "epoch's true action?")
    for arm in ("graded", "coin", "threshold"):
        for gap in ("0.20", "0.10"):
            hit = tot = 0
            for s in range(8):
                r = get(runs, arm, s, gap)
                if not r:
                    continue
                for k, row in enumerate(r["epoch_log"]):
                    if k >= len(r["epoch_actions_true"]) or row.get("n", 0) < 20:
                        continue
                    if row.get("belief") is None:
                        continue
                    tot += 1
                    hit += 1 if row["belief"] == r["epoch_actions_true"][k] else 0
            if tot:
                print(f"    {arm:10s} gap {gap}: agreement {hit}/{tot} = "
                      f"{hit/tot:.3f}")

    print("\n  A-null truth=off: agreement must not exceed truth=on")
    for persist in (False, True):
        hit = tot = 0
        for s in range(10):
            r = get(runs, "graded", s, "0.10", 0.0, persist, truth=False)
            if not r:
                continue
            for k, row in enumerate(r["epoch_log"]):
                if k >= len(r["epoch_actions_true"]) or row.get("n", 0) < 20:
                    continue
                if row.get("belief") is None:
                    continue
                tot += 1
                hit += 1 if row["belief"] == r["epoch_actions_true"][k] else 0
        print(f"    truth=off persist={'on' if persist else 'off'}: "
              f"{hit}/{tot} = {hit/tot if tot else float('nan'):.3f}")

    # ---------------- Block F ----------------
    print("\n### BLOCK F -- AMORTIZATION (gap 0.10)")
    print("\n  F1 reward(carry) - reward(fresh), per stickiness q "
          "(declared: negative-or-zero at q=0, positive and growing with q)")
    for q, pred in ((0.0, -1), (0.25, 0), (0.5, 1), (0.75, 1), (1.0, 1)):
        contrast(runs, "f_carry", "f_fresh", "0.10", q=q, predict=pred,
                 label=f"F1 carry-fresh")
    print("\n  F2 reuse is free: carry's gathering effort as a share of "
          "fresh's (need <= 0.60 at q >= 0.5)")
    for q in QS:
        f = [get(runs, "f_fresh", s, "0.10", q) for s in range(8)]
        c = [get(runs, "f_carry", s, "0.10", q) for s in range(8)]
        f = [x for x in f if x]
        c = [x for x in c if x]
        if not f or not c:
            continue
        fg = statistics.mean(x["steps_gathering"] for x in f)
        cg = statistics.mean(x["steps_gathering"] for x in c)
        fb = statistics.mean(x["steps_belief"] for x in f)
        cb = statistics.mean(x["steps_belief"] for x in c)
        print(f"    q={q}: carry gather {cg:.0f} (believe {cb:.0f}) vs "
              f"fresh gather {fg:.0f} (believe {fb:.0f}) = {cg/fg:.3f} of "
              f"fresh gather   (need <= 0.60)")
    print("\n  F3 endpoint: carry vs oracle at q=1 (must reach >= 95%); "
          "carry vs fresh at q=0 (must not exceed the noise band)")
    r1 = contrast(runs, "f_carry", "oracle", "0.10", q=1.0, predict=-1,
                  label="F3 carry-oracle q=1.0")
    if r1:
        print(f"    -> carry reaches {100*r1['meanA']/r1['meanB']:.1f}% of "
              f"oracle at q=1")
    contrast(runs, "f_carry", "f_fresh", "0.10", q=0.0, predict=-1,
             label="F3 carry-fresh q=0.0")

    print("\n  F3b payoff reading (Block G, prereg §3 F3 mirror): at "
          "q=1 the oracle arm's own gathering is 0 by construction; the "
          "carry arm's is measured above.")
    print("\n  F4 the curve, stated plainly: carry-fresh paired difference "
          "and carry's gathering share vs q")
    print(f"    {'q':>6s}{'carry-fresh diff':>18s}{'carry gather/fresh':>20s}")
    for q in QS:
        f = [get(runs, "f_fresh", s, "0.10", q) for s in range(8)]
        c = [get(runs, "f_carry", s, "0.10", q) for s in range(8)]
        f = [x for x in f if x]
        c = [x for x in c if x]
        d = statistics.mean(x["total_reward"] for x in c) - \
            statistics.mean(x["total_reward"] for x in f)
        fg = statistics.mean(x["steps_gathering"] for x in f)
        cg = statistics.mean(x["steps_gathering"] for x in c)
        print(f"    {q:6.2f}{d:18.0f}{cg/fg:20.3f}")

    print("\n  Economy table (mean reward, 8 seeds)")
    print(f"    {'arm':14s}{'gap/q':>10s}{'reward':>12s}{'gather':>10s}"
          f"{'believe':>10s}{'pays':>8s}")
    for arm in ("graded", "threshold", "coin", "oracle", "rot"):
        for gap in GAPS:
            v = [get(runs, arm, s, gap) for s in range(8)]
            v = [x for x in v if x]
            if not v:
                continue
            print(f"    {arm:14s}{gap:>10s}"
                  f"{statistics.mean(x['total_reward'] for x in v):12.0f}"
                  f"{statistics.mean(x['steps_gathering'] for x in v):10.0f}"
                  f"{statistics.mean(x['steps_belief'] for x in v):10.0f}"
                  f"{statistics.mean(x['pays_world'] for x in v):8.0f}")

    print("\n" + "=" * 74)
    print("SUMMARY")
    for gap in GAPS:
        c1 = resC[gap]["C1"]
        c2 = resC[gap]["C2"]
        c3 = resC[gap]["C3"]
        print(f"  gap {gap}: C1 {'PASS' if c1 and all(c1['legs']) else 'FAIL'} "
              f"({c1['diff']:+.0f})  "
              f"C2 {'PASS' if c2 and all(c2['legs']) else 'FAIL'} "
              f"({c2['diff']:+.0f})  "
              f"C3 {'PASS' if c3 and all(c3['legs']) else 'FAIL'} "
              f"({c3['diff']:+.0f})")
    print("=" * 74)


if __name__ == "__main__":
    main()
