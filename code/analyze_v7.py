"""analyze_v7.py -- per-claim attribution for the V7 matrix (PREREG_V7 §2).

Reads ONLY results/matrix_v7/*.json. Emits verdicts for C2 (generation),
C3 (verification) and C1 (choice) SEPARATELY, plus the economic block
(secondary observation, no verdict force). Prints a frozen report.

Usage: python3 analyze_v7.py > results/analysis_v7.txt
"""
import glob
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX = os.path.join(HERE, "results", "matrix_v7")

# ---- prereg thresholds (NOT to be moved after runs) ------------------
C2_ON_MIN = 8        # truth=on: true pair nominated in >= 8/10 seeds
C2_OFF_MAX = 2       # truth=off: nominated in <= 2/10 seeds
C3_FP_MAX = 0        # false positives on the decoy -- zero
C3_FN_MAX = 2        # false negatives on the true edge
C1_NOGEN_MIN = 8     # full probes in >= 8/10 conflict seeds
C1_BETA0_FRAC = 0.2  # beta0 probes <= 0.2 x full
C1_PERM_MIN = 8      # perm first probe follows permuted argmax >= 8/10


def load():
    rows = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(MATRIX, "*.json"))):
        d = json.load(open(p))
        rows[(d["arm"], d["truth"], d["rich"], d["decoy"])].append(d)
    for k in rows:
        rows[k].sort(key=lambda d: d["seed"])
    return rows


def true_pair_causal(d):
    v = d["verdicts"].get(d["edge_action"] + "->hum")
    return bool(v and v["verdict"] == "CAUSAL")


def fp_count(d):
    return sum(1 for k, v in d["verdicts"].items()
               if k.endswith("->glow") and v["verdict"] == "CAUSAL")


def nominated(d, action, effect):
    return any(c[0] == action and c[1] == effect for c in d["candidates_seen"])


def main():
    rows = load()
    print("=" * 70)
    print("V7 ANALYSIS -- per-claim attribution (PREREG_V7 §2)")
    print("=" * 70)

    # ---------------- C2 GENERATION -----------------------------------
    print("\n### C2 GENERATION (candidate list = f(agent tables))")
    on = rows[("v7_full", True, "low", True)]
    off = rows[("v7_full", False, "low", True)]
    on_nom = sum(1 for d in on if nominated(d, d["edge_action"], "hum"))
    off_nom = sum(1 for d in off if nominated(d, d["edge_action"], "hum"))
    print(f"  truth=on  true pair nominated: {on_nom}/10 (need >= {C2_ON_MIN})")
    print(f"  truth=off true pair nominated: {off_nom}/10 (need <= {C2_OFF_MAX})")
    # anti-hardcode: does nomination FOLLOW the randomised edge_action?
    print("  per-seed (on): edge -> nominated?")
    for d in on:
        print(f"     seed {d['seed']:2d} edge={d['edge_action']:6s} "
              f"nominated={nominated(d, d['edge_action'], 'hum')} "
              f"n_cand={d['n_candidates_total']}")
    c2 = (on_nom >= C2_ON_MIN and off_nom <= C2_OFF_MAX)
    print(f"  VERDICT C2: {'PASS' if c2 else 'FAIL'}")
    # the nogen control: its list must differ from the generated one
    nogen = rows[("v7_nogen", True, "low", True)]
    nogen_nom = sum(1 for d in nogen if nominated(d, d["edge_action"], "hum"))
    print(f"  CONTROL v7_nogen (designer list 'wait->hum'): true pair "
          f"nominated {nogen_nom}/10 -- the designer list is FIXED, so it "
          f"misses the randomised edge in most seeds (contrast with C2).")

    # ---------------- C3 VERIFICATION ---------------------------------
    print("\n### C3 VERIFICATION (do-intervention on SELF-GENERATED list)")
    fp = sum(fp_count(d) for d in on) + sum(fp_count(d) for d in off)
    fn = sum(1 for d in on if not true_pair_causal(d))
    n_causal = sum(1 for d in on if true_pair_causal(d))
    print(f"  truth=on  CAUSAL on true pair: {n_causal}/10")
    print(f"  truth=on  FN (true pair not CAUSAL): {fn}/10 (need <= {C3_FN_MAX})")
    print(f"  FP (any glow CAUSAL, on+off): {fp} (need == {C3_FP_MAX})")
    print("  per-seed (on): edge verdict / glow verdicts")
    for d in on:
        v = d["verdicts"].get(d["edge_action"] + "->hum")
        gv = {k.split("->")[0]: vv["verdict"] for k, vv in d["verdicts"].items()
              if k.endswith("->glow")}
        print(f"     seed {d['seed']:2d} "
              f"true={(v['verdict'] if v else 'NONE'):10s}"
              f" glow={gv}")
    c3 = (fp <= C3_FP_MAX and fn <= C3_FN_MAX)
    print(f"  VERDICT C3: {'PASS' if c3 else 'FAIL'}")

    # ---------------- C1 CHOICE ---------------------------------------
    print("\n### C1 CHOICE (verify vs exploit the permitted alternative)")
    full_hi = rows[("v7_full", True, "high", True)]
    full_lo = rows[("v7_full", True, "low", True)]
    beta_hi = rows[("v7_beta0", True, "high", True)]
    beta_lo = rows[("v7_beta0", True, "low", True)]
    perm_hi = rows[("v7_perm", True, "high", True)]

    def probes(ds):
        return [d["probe_trials"] for d in ds]

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    fh, fl = probes(full_hi), probes(full_lo)
    bh, bl = probes(beta_hi), probes(beta_lo)
    print(f"  full  probes rich=high: {fh}  mean {mean(fh):.0f}")
    print(f"  full  probes rich=low : {fl}  mean {mean(fl):.0f}")
    print(f"  beta0 probes rich=high: {bh}  mean {mean(bh):.0f}")
    print(f"  beta0 probes rich=low : {bl}  mean {mean(bl):.0f}")
    # (i) non-constancy: full probes in the conflict, beta0 (near) none
    n_full_probe = sum(1 for x in fh if x >= 1)
    c1_i = (n_full_probe >= C1_NOGEN_MIN
            and mean(bh) <= C1_BETA0_FRAC * mean(fh))
    print(f"  (i) full probes in >=1 conflict seed: {n_full_probe}/10 "
          f"(need >= {C1_NOGEN_MIN}); beta0/full = "
          f"{mean(bh)/mean(fh) if mean(fh) else 0:.3f} "
          f"(need <= {C1_BETA0_FRAC}) -> {'PASS' if c1_i else 'FAIL'}")
    # (ii) state-dependence: perm's first probe follows the permuted argmax
    ok_perm = 0
    n_perm = 0
    for d in perm_hi + rows[("v7_perm", True, "low", True)]:
        rk = d.get("ranked_at_first_probe")
        fpc = d.get("first_probe")
        if not rk or not fpc:
            continue
        n_perm += 1
        ranked = sorted(rk, key=lambda c: (-c[2], -c[3], c[0], c[1]))
        if (fpc[0], fpc[1]) == (ranked[0][0], ranked[0][1]):
            ok_perm += 1
    c1_ii = n_perm > 0 and ok_perm >= C1_PERM_MIN
    print(f"  (ii) perm first probe == permuted argmax: {ok_perm}/{n_perm} "
          f"(need >= {C1_PERM_MIN}) -> {'PASS' if c1_ii else 'FAIL'}")
    # (iii) the price of the choice is measured: fewer probes when rich=high,
    #       but not zero
    c1_iii = (mean(fh) < mean(fl) and mean(fh) > 0)
    print(f"  (iii) probes(high) {mean(fh):.0f} < probes(low) {mean(fl):.0f}"
          f" and > 0 -> {'PASS' if c1_iii else 'FAIL'}")
    c1 = c1_i and c1_ii and c1_iii
    print(f"  VERDICT C1: {'PASS' if c1 else 'FAIL'} "
          f"(legs i={c1_i} ii={c1_ii} iii={c1_iii})")

    # ---------------- ECONOMY (secondary, no verdict) -----------------
    print("\n### ECONOMY (secondary observation, no verdict force)")
    hdr = f"  {'arm':12s} {'rich':5s} {'reward':>9s} {'fruits':>7s} " \
          f"{'deaths':>7s} {'probes':>7s}"
    print(hdr)
    for (arm, truth, rich, decoy), ds in sorted(rows.items()):
        if not truth:
            continue
        print(f"  {arm:12s} {rich:5s} "
              f"{mean([d['total_reward'] for d in ds]):9.1f} "
              f"{mean([d['fruits_eaten'] for d in ds]):7.2f} "
              f"{mean([d['deaths'] for d in ds]):7.1f} "
              f"{mean([d['probe_trials'] for d in ds]):7.0f}")

    # ---------------- ORACLE DECOMPOSITION ----------------------------
    print("\n### ORACLE DECOMPOSITION (gross value of the edge, secondary)")
    oracle = rows[("v7_oracle", True, "low", True)]
    forager = rows[("v7_forager", True, "low", True)]
    print(f"  oracle reward {mean([d['total_reward'] for d in oracle]):.1f} "
          f"vs full {mean([d['total_reward'] for d in full_lo]):.1f} "
          f"vs forager {mean([d['total_reward'] for d in forager]):.1f} "
          f"vs beta0 {mean([d['total_reward'] for d in beta_lo]):.1f}")
    print(f"  oracle fruits {mean([d['fruits_eaten'] for d in oracle]):.1f} "
          f"vs full {mean([d['fruits_eaten'] for d in full_lo]):.1f}")

    print("\n" + "=" * 70)
    print(f"SUMMARY: C2={'PASS' if c2 else 'FAIL'} "
          f"C3={'PASS' if c3 else 'FAIL'} C1={'PASS' if c1 else 'FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
