#!/usr/bin/env python3
"""The honest head-to-head. My ported arms vs the PUBLISHED external methods,
on the external benchmark's own ground truth, with significance, and with the
unfairness direction declared rather than hidden.
"""
import json, math
from scipy import stats


def key(a, b):
    return (a, b) if a < b else (b, a)


def fisher(a, b, c, d):
    return stats.fisher_exact([[a, b], [c, d]])[1]


def main():
    dec = {tuple(k.split("|")): v
           for k, v in json.load(open("preds_bench2.json")).items()}
    GT20 = [("pkc","pka"),("pkc","raf"),("pka","raf"),("pkc","mek"),("pka","mek"),
            ("raf","mek"),("mek","erk"),("pka","erk"),("erk","akt"),("pka","akt"),
            ("pkc","p38"),("pka","p38"),("pkc","jnk"),("pka","jnk"),("plc","pip3"),
            ("plc","pip2"),("pip3","pip2")]
    gt17 = {key(a, b) for a, b in GT20}
    gt20 = set(gt17) | {(("pkc","pka"))}  # placeholder replaced below

    # 20-edge ground truth parsed from the published file
    gt20 = set()
    for line in open("ds/sachs.ground.truth.graph.txt"):
        if "-->" in line:
            a, b = line.strip().split("-->")
            gt20.add(key(a.split(".", 1)[1].strip().lower(), b.strip().lower()))

    def arms(gt):
        r = {}
        for arm in ("A", "B", "C"):
            sel = [k for k, v in dec.items() if v[arm]]
            tp = sum(1 for k in sel if k in gt)
            r[arm] = dict(n_sel=len(sel), tp=tp, fp=len(sel) - tp,
                          fn=len(gt) - tp,
                          precision=(tp / len(sel) if sel else 0.0),
                          recall=(tp / len(gt) if gt else 0.0))
        return r

    out = {}
    out["arms_gt20"] = arms(gt20)
    out["arms_gt17"] = arms(gt17)

    # significance of the precision jump A -> C (Pooled vs pooled+context)
    a = out["arms_gt17"]["A"]; c = out["arms_gt17"]["C"]
    out["fisher_precision_A_vs_C_gt17"] = fisher(a["tp"], a["fp"], c["tp"], c["fp"])
    a = out["arms_gt20"]["A"]; c = out["arms_gt20"]["C"]
    out["fisher_precision_A_vs_C_gt20"] = fisher(a["tp"], a["fp"], c["tp"], c["fp"])

    # published external numbers, restated as precision/recall vs the 17-arc net
    # inter.iamb: skeleton tp 8 fp 0 fn 9 ; mbde: tp 17 fp 8 fn 0
    out["published_interiamb"] = dict(tp=8, fp=0, fn=9, precision=1.0, recall=8/17)
    out["published_mbde"] = dict(tp=17, fp=8, fn=0, precision=17/25, recall=1.0)
    out["gt17_size"] = len(gt17)
    out["gt20_size"] = len(gt20)

    # head-to-head at the SAME ground truth (gt17), same target = skeleton
    out["head_to_head_gt17"] = {
        "my_naive_pooled_A": out["arms_gt17"]["A"],
        "my_context_stable_C": out["arms_gt17"]["C"],
        "published_interiamb": dict(tp=8, fp=0, fn=9, precision=1.0, recall=8/17),
        "published_mbde_intervention_aware": dict(tp=17, fp=8, fn=0,
                                                  precision=17/25, recall=1.0),
    }

    # declared unfairness: my arms are skeleton-only (direction ignored);
    # the published ones are partly directed. Also the pooled marginal is a
    # WEAKER stand-in than any published method, so beating it proves little.
    out["declared_caveats"] = [
        "My arms score SKELETON only (direction ignored); published inter.iamb "
        "and mbde are evaluated on directed arcs, where mbde is favoured.",
        "My naive pooled arm (Spearman univariate) is WEAKER than any published "
        "method: published inter.iamb reaches precision 1.00 on the same file "
        "vs my pooled arm's 0.30. Beating the naive marginal is therefore NOT "
        "evidence against published methods.",
        "Direction is not recovered at all by my arms; the campaign's mechanism "
        "in the worlds produced directed edges, so this port loses a capacity.",
        "The intervention indicator columns in the external file are the "
        "experimenters' assignment; my context arms READ them, they do not "
        "choose or discover them. C1/C2 are not exercised.",
    ]

    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
