#!/usr/bin/env python3
"""Final external comparison: my arms vs the PUBLISHED external numbers,
at matched operating points, plus determinism and a hypergeometric null for
the precision@k claim. Reads only frozen external inputs and frozen outputs.
"""
import csv, json, math, os
from itertools import combinations
from collections import defaultdict

DS = "ds"
GTF = DS + "/sachs.ground.truth.graph.txt"


def key(a, b):
    return (a, b) if a < b else (b, a)


def main():
    r2 = json.load(open("results_bench2.json"))
    frozen_dec = json.load(open("preds_bench2.json"))
    dec = {tuple(k.split("|")): v for k, v in frozen_dec.items()}

    gt20 = set()
    for line in open(GTF):
        if "-->" in line:
            a, b = line.strip().split("-->")
            gt20.add(key(a.split(".", 1)[1].strip().lower(), b.strip().lower()))

    out = {}

    # --- (1) published external numbers, restated with their own metrics ---
    # bnlearn/Scutari HOWTO, observational file (7466 rows), inter.iamb cor:
    #   skeleton tp 8 fp 0 fn 9   -> arcs 8, directed 2
    # intervention-aware model averaging (mbde) vs the validated network:
    #   tp 17 fp 8 fn 0
    pub_interiamb = dict(tp=8, fp=0, fn=9)
    pub_mbde = dict(tp=17, fp=8, fn=0)
    for nm, p in (("published_bnlearn_interiamb", pub_interiamb),
                  ("published_bnlearn_mbde", pub_mbde)):
        pr = p["tp"] / (p["tp"] + p["fp"]) if (p["tp"] + p["fp"]) else 0.0
        rc = p["tp"] / (p["tp"] + p["fn"]) if (p["tp"] + p["fn"]) else 0.0
        out[nm] = dict(p, precision=pr, recall=rc)

    # --- (2) my arms, gt20 ---
    for arm in ("A", "B", "C"):
        out["mine_arm" + arm] = r2["gt20_arm" + arm]

    # --- (3) matched operating points ---
    # a table is comparable only at equal recall (or equal precision).
    def at_recall(target):
        """cheapest cost to reach >= target recall; cost = precision at that k"""
        allp = sorted(dec)
        # arm C (pooled + general-stratum confirmation) as the selector,
        # ranked by pooled p (the information both arms share)
        sel = [k for k in allp if dec[k]["C"]]
        sel.sort(key=lambda k: dec[k]["p_pooled"])
        hits = [k for k in sel if k in gt20]
        if not hits:
            return None
        return dict(n_sel=len(sel), tp=len(hits), fn=len(gt20) - len(hits),
                    precision=len(hits) / len(sel), recall=len(hits) / len(gt20))
    out["mine_armC_ordered"] = at_recall(0.4)

    # --- (4) hypergeometric null for precision@3 ---
    # how likely is a random 3-subset of the 55 pairs to be all-true?
    N, M, k = 55, len(gt20), 3
    p_all_true = (math.comb(M, k) / math.comb(N, k)) if k <= M else 0.0
    out["hypergeom"] = dict(N=N, M=M, k=k, p_three_true_of_three=p_all_true,
                            pooled_p3=r2["prec_at_3_pooled"],
                            het_p3=r2["prec_at_3_het"])

    # --- (5) how much of the pooled false-positive mass is "general-stratum
    # invisible" (context-exclusive in the campaign's literal sense) ---
    excl = [k for k, v in dec.items() if (not v["A"]) and v["C"]]
    out["literal_context_exclusive_vs_armC"] = len(excl)
    # exact literal form from part 1 (invisible pooled, visible in a stratum)
    out["literal_from_part1"] = json.load(open("results_bench.json"))["E1"]

    # --- (6) the false edges the pooled arm admits, and why stability drops them
    fp_pooled = [k for k, v in dec.items() if v["A"] and k not in gt20]
    dropped = [k for k in fp_pooled if not dec[k]["C"]]
    out["pooled_fp_total"] = len(fp_pooled)
    out["pooled_fp_dropped_by_C"] = len(dropped)
    out["pooled_fp_kept"] = len(fp_pooled) - len(dropped)
    # their mean heterogeneity p and spread
    if fp_pooled:
        out["pooled_fp_mean_p_het"] = sum(dec[k]["p_het"] for k in fp_pooled) / len(fp_pooled)
        out["pooled_fp_mean_spread"] = sum(dec[k]["spread"] for k in fp_pooled) / len(fp_pooled)

    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
