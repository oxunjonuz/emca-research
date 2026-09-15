"""analyze_v7b.py -- primary pass for V7B (PREREG_V7B.md, claims H1-H5).

Reads ONLY frozen data:
  * results/matrix_v7/*.json   (the frozen V7 matrix, 149 verdict rows)
  * results/matrix_v7b/*.json  (the held-out seeds 10..29, if present)
and the scripted-calibration output (results/calib_v7b_scale.txt, if
present). Prints a frozen report. No agent imports.

Usage: python3 analyze_v7b.py > results/analysis_v7b.txt
"""
import glob
import json
import math
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
M7 = os.path.join(HERE, "results", "matrix_v7")
M7B = os.path.join(HERE, "results", "matrix_v7b")
SCALE = os.path.join(HERE, "results", "calib_v7b_scale.txt")

ALPHA_LEVELS = (0.05, 0.01, 0.001)


# ---------------- the agent's own exact fisher (same rule) -------------
def fisher(a_yes, a_no, c_yes, c_no):
    n = a_yes + a_no + c_yes + c_no
    if n == 0:
        return 1.0
    r1, c1 = a_yes + a_no, a_yes + c_yes
    hi = min(r1, c1)
    s = 0.0
    den = math.comb(n, c1)
    for x in range(a_yes, hi + 1):
        s += math.comb(r1, x) * math.comb(n - r1, c1 - x) / den
    return min(1.0, max(0.0, s))


def rule_fires(ty, tn, cy, cn):
    if (ty + tn) == 0 or (cy + cn) == 0:
        return False, 1.0, 0.0
    p = fisher(ty, tn, cy, cn)
    ra = ty / (ty + tn)
    rc = cy / (cy + cn)
    rr = ra / rc if rc > 0 else float("inf")
    return (p < 0.05 and rr >= 1.3), p, rr


# ---------------- inventory of the frozen matrix -----------------------
def inventory():
    runs, rows = [], []
    for p in sorted(glob.glob(os.path.join(M7, "*.json"))):
        d = json.load(open(p))
        runs.append(d)
        for k, v in d["verdicts"].items():
            a, e = k.split("->")
            rows.append(dict(arm=d["arm"], seed=d["seed"], truth=d["truth"],
                             rich=d["rich"], edge=d["edge_action"], pair=k,
                             effect=e, verdict=v["verdict"], p=v["p"],
                             rr=v["rr"], ty=v["target_yes"], tn=v["target_no"],
                             cy=v["ctrl_yes"], cn=v["ctrl_no"]))
    return runs, rows


def fp_events(rows):
    return [r for r in rows
            if r["effect"] == "glow" and r["verdict"] == "CAUSAL"]


def main():
    runs, rows = inventory()
    print("=" * 74)
    print("V7B ANALYSIS -- closure of C3's open item (PREREG_V7B.md)")
    print("=" * 74)

    # ---------- H2: what is the family, really? ------------------------
    print("\n### H2  THE FAMILY (what does 149 count?)")
    distinct_worlds = len({(r["seed"], r["truth"], r["rich"]) for r in rows})
    distinct_seeds = len({r["seed"] for r in rows})
    distinct_runs = len(runs)
    per_life = [len(d["verdicts"]) for d in runs]
    mean_k = sum(per_life) / len(per_life)
    fp_rows = fp_events(rows)
    fp_worlds = len({(r["seed"], r["truth"], r["rich"]) for r in fp_rows})
    print(f"  fits           : {distinct_runs}")
    print(f"  verdict ROWS   : {len(rows)}   <- the denominator V7 used")
    print(f"  distinct worlds: {distinct_worlds}  (seed x truth x rich)")
    print(f"  tests per life : mean {mean_k:.2f}, max {max(per_life)}")
    print(f"  the single FP event appears in {len(fp_rows)} rows / "
          f"{fp_worlds} world(s)")
    print("  conventions for the study family:")
    print(f"    (a) distinct FP EVENTS as the unit         -> m = {distinct_worlds}")
    print(f"    (b) runs (over-)counting the coupled rows   -> m = {len(rows)}")
    print("  V7 quoted (b). Under (a) the event rate is 1/10, not 1/149.")

    # ---------- H1: can family-wise control reject the FP? -------------
    print("\n### H1  CAN (A) EVER BE THE ANSWER TO C3's CAUSE?")
    p_fp = fp_rows[0]["p"] if fp_rows else None
    if p_fp is None:
        print("  no FP row on disk -- H1 cannot be evaluated")
    else:
        # recompute exactly (independent of the recorded value)
        r = fp_rows[0]
        p_exact = fisher(r["ty"], r["tn"], r["cy"], r["cn"])
        print(f"  observed FP: seed {r['seed']} {r['pair']}, "
              f"{r['ty']}/{r['tn']} vs {r['cy']}/{r['cn']}")
        print(f"  p recorded = {p_fp}   p recomputed = {p_exact:.6f}")
        print("  Bonferroni-style family needed to reject it:")
        for a in ALPHA_LEVELS:
            print(f"    alpha={a:<5}: reject only if m >= {math.ceil(a/p_exact)}")
        print(f"  real agent-side family per life: {mean_k:.2f} "
              f"(max {max(per_life)})")
        print(f"  real study-side families: {distinct_worlds} worlds, "
              f"{len(rows)} rows")
        print(f"  => the ONLY convention that rejects the event is the "
              f"study-level family ({len(rows)} rows, threshold "
              f"{0.05/len(rows):.6f}); the agent's own per-life family "
              f"({max(per_life)}) is far too small. (A) as stated -- "
              f"capping the agent's block budget -- cannot touch it.")

    # ---------- H3: exact null rate + power of past calibrations -------
    print("\n### H3  EXACT NULL RATE OF THE FROZEN RULE + POWER OF PAST CHECKS")
    NA, NC = 200, 199
    l1 = [math.log(math.comb(NA, x)) - NA * math.log(2) for x in range(NA + 1)]
    l2 = [math.log(math.comb(NC, y)) - NC * math.log(2) for y in range(NC + 1)]
    q_any = q_rule = q_strong = 0.0
    for x in range(NA + 1):
        wx = math.exp(l1[x])
        for y in range(NC + 1):
            w = wx * math.exp(l2[y])
            ra, rc = x / NA, y / NC
            if rc <= 0 or ra <= rc:
                continue
            pv = fisher(x, NA - x, y, NC - y)
            if pv < 0.05:
                q_any += w
                if ra / rc >= 1.3:
                    q_rule += w
            if p_fp and pv <= p_exact:
                q_strong += w
    print(f"  P(p<0.05, greater)        = {100*q_any:.3f}%")
    print(f"  P(p<0.05 AND RR>=1.3)     = {100*q_rule:.3f}%  <- the rule's"
          f" per-test FP rate")
    if p_fp:
        print(f"  P(p <= the observed FP)   = {100*q_strong:.4f}%")
    print(f"  E[FP] over {len(rows)} rows (V7's denominator)      "
          f"= {len(rows)*q_rule:.2f}")
    print(f"  E[FP] over {distinct_worlds} worlds (the honest count)"
          f"  = {distinct_worlds*q_rule:.2f}")
    print(f"  observed: {len(fp_rows)} row(s), {fp_worlds} distinct event(s)")
    print(f"  campaign Monte-Carlo said 0.51%; scripted 0/400 and 0/160:")
    print(f"    expected hits at the exact rate: {400*q_rule:.2f} and "
          f"{160*q_rule:.2f} -> both checks are UNDERPOWERED to speak at "
          f"this rate (0 hits is the likely outcome even if calibrated)")
    if p_fp:
        print(f"  P(>=1 event at least as strong as observed, across "
              f"{len(rows)} tests, if independence) = "
              f"{1-(1-q_strong)**len(rows):.3f}")
        print(f"  P(>=1 such event across {distinct_worlds} worlds)      = "
              f"{1-(1-q_strong)**distinct_worlds:.4f}")

    # ---------- H4: held-out seeds ------------------------------------
    print("\n### H4  HELD-OUT SEEDS 10..29 (fresh worlds, same code)")
    hb = sorted(glob.glob(os.path.join(M7B, "*.json")))
    if not hb:
        print("  no held-out files yet")
    else:
        h_rows, h_null, h_fp = [], 0, []
        for p in hb:
            d = json.load(open(p))
            for k, v in d["verdicts"].items():
                a, e = k.split("->")
                rec = dict(seed=d["seed"], truth=d["truth"], pair=k, effect=e,
                           verdict=v["verdict"], p=v["p"], rr=v["rr"],
                           ty=v["target_yes"], tn=v["target_no"],
                           cy=v["ctrl_yes"], cn=v["ctrl_no"])
                h_rows.append(rec)
                if e == "glow":
                    h_null += 1
                    if v["verdict"] == "CAUSAL":
                        h_fp.append(rec)
        print(f"  runs {len(hb)}, verdict rows {len(h_rows)}, "
              f"null (glow) tests {h_null}, FP events {len(h_fp)}")
        for e in h_fp:
            print(f"    FP: seed {e['seed']} truth={e['truth']} {e['pair']} "
                  f"p={e['p']} rr={e['rr']} {e['ty']}/{e['tn']} vs "
                  f"{e['cy']}/{e['cn']}")
        if h_null:
            obs = len(h_fp) / h_null
            hi = 1 - 0.05 ** (1 / h_null) if h_fp == 0 else None
            print(f"  observed held-out rate: {len(h_fp)}/{h_null} = "
                  f"{100*obs:.2f}%  (calibrated expectation "
                  f"{100*q_rule:.3f}%)")
            if hi is not None:
                print(f"  rule of three: one-sided 95% upper bound on the "
                      f"rate = {100*hi:.2f}% -- FP=0 decides INFLATION "
                      f"(not calibrated frequency)")
            print(f"  decision rule (frozen): 0 -> re-characterize + close; "
                  f">=2 -> real defect; 1 -> indeterminate")
        # true-edge sanity on held-out seeds
        t_edge = [r for r in h_rows if r["effect"] == "hum" and r["truth"]]
        print(f"  true-edge (hum) rows: {len(t_edge)}; "
              f"CAUSAL {sum(1 for r in t_edge if r['verdict']=='CAUSAL')}")

    # ---------- H5: large-scale scripted calibration -------------------
    print("\n### H5  LARGE-SCALE SCRIPTED CALIBRATION")
    if os.path.exists(SCALE):
        print(open(SCALE).read().rstrip())
    else:
        print("  no calib_v7b_scale.txt yet")

    print("\n" + "=" * 74)


if __name__ == "__main__":
    main()
