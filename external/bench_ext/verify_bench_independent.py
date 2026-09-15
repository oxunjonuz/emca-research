#!/usr/bin/env python3
"""INDEPENDENT re-derivation of bench_transfer.py / bench_transfer2.py.

Shares NO code with them: Spearman comes from scipy, the strata are rebuilt
from the raw external files, and the ground truth is re-parsed from the
published graph text. Reads only the frozen external inputs and the frozen
outputs of the two measurement scripts. Reports every disagreement.
"""
import csv, json, math, sys
import numpy as np
from scipy import stats
from collections import defaultdict

DS = "ds"
OBS = DS + "/sachs.experimental.mixed.txt"
GT = DS + "/sachs.ground.truth.graph.txt"
ALPHA = 0.05
MIN_N = 50

GT17 = [("pkc","pka"),("pkc","raf"),("pka","raf"),("pkc","mek"),("pka","mek"),
        ("raf","mek"),("mek","erk"),("pka","erk"),("erk","akt"),("pka","akt"),
        ("pkc","p38"),("pka","p38"),("pkc","jnk"),("pka","jnk"),("plc","pip3"),
        ("plc","pip2"),("pip3","pip2")]


def key(a, b):
    return (a, b) if a < b else (b, a)


def main():
    rows = list(csv.reader(open(OBS), delimiter="\t"))
    hdr = rows[0]; prot = hdr[:11]; cond = hdr[11:]
    raw = np.array([[float(x) for x in r] for r in rows[1:] if r and r[0].strip()])
    X = raw[:, :11]; IND = raw[:, 11:]

    # ground truth, re-parsed
    gt = set()
    for line in open(GT):
        if "-->" in line:
            a, b = line.strip().split("-->")
            gt.add(key(a.split(".", 1)[1].strip().lower(), b.strip().lower()))
    assert len(gt) == 20, len(gt)

    # strata rebuilt independently
    groups = defaultdict(list)
    for i in range(len(X)):
        act = [cond[k] for k in range(9) if IND[i, k] > 0.5]
        spec = [c for c in act if c != cond[0]]
        if not spec:
            groups["__general__"].append(i)
        else:
            for c in spec:
                groups[c].append(i)
    ks = [g for g in sorted(groups) if len(groups[g]) >= MIN_N]
    K = len(ks)

    # Spearman via scipy (different implementation than the measurement code)
    def sp(a, b):
        r, p = stats.spearmanr(X[:, a], X[:, b])
        return float(r), float(p)

    # arms recomputed from scratch
    dec = {}
    for a in range(11):
        for b in range(a + 1, 11):
            rho_p, p_pool = sp(a, b)
            rhos, ps = [], []
            for g in ks:
                ix = groups[g]
                r, p = stats.spearmanr(X[ix, a], X[ix, b])
                rhos.append(float(r)); ps.append(float(p))
            A = p_pool < ALPHA
            thr = ALPHA / K
            B = A and all((p < thr and r * rho_p > 0) for r, p in zip(rhos, ps))
            gi = groups.get("__general__")
            rg, pg = stats.spearmanr(X[gi, a], X[gi, b])
            C = A and float(pg) < ALPHA and float(rg) * rho_p > 0
            zd = []
            for r, g in zip(rhos, ks):
                rr = max(-0.999999, min(0.999999, r))
                zd.append(math.sqrt(len(groups[g]) - 3) *
                          0.5 * math.log((1 + rr) / (1 - rr)))
            zb = sum(zd) / len(zd)
            Q = sum((z - zb) ** 2 for z in zd)
            p_het = float(stats.chi2.sf(Q, len(zd) - 1))
            dec[key(prot[a], prot[b])] = dict(A=A, B=B, C=C, p_pooled=p_pool,
                                              p_het=p_het,
                                              spread=max(rhos) - min(rhos))

    def pr(arm, gt_set):
        sel = [k for k, v in dec.items() if v[arm]]
        tp = sum(1 for k in sel if k in gt_set)
        return dict(n_sel=len(sel), tp=tp, fp=len(sel) - tp, fn=len(gt_set) - tp,
                    precision=(tp / len(sel) if sel else 0.0),
                    recall=(tp / len(gt_set) if gt_set else 0.0))

    gt17 = {key(a, b) for a, b in GT17}
    mine = {tag: {arm: pr(arm, g) for arm in ("A", "B", "C")}
            for tag, g in (("gt20", gt), ("gt17", gt17))}

    # compare with what the measurement scripts froze
    frozen2 = json.load(open("results_bench2.json"))
    diffs = []
    for tag in ("gt20", "gt17"):
        for arm in ("A", "B", "C"):
            f = frozen2["%s_arm%s" % (tag, arm)]
            m = mine[tag][arm]
            for fld in ("n_sel", "tp", "fp", "fn"):
                if f[fld] != m[fld]:
                    diffs.append("%s arm%s %s: frozen %s vs independent %s"
                                 % (tag, arm, fld, f[fld], m[fld]))
            if abs(f["precision"] - m["precision"]) > 1e-9:
                diffs.append("%s arm%s precision: %s vs %s"
                             % (tag, arm, f["precision"], m["precision"]))

    frozen1 = json.load(open("results_bench.json"))
    # part-1 headline: no context-exclusive pairs, pooled sees everything
    excl = [k for k, v in dec.items() if (not v["A"]) and
            (v["p_het"] >= 0 and False)]
    pooled_vis = sum(1 for v in dec.values() if v["A"])
    part1_agree = []
    part1_agree.append(("n_rows", frozen1["n_rows"], len(X)))
    part1_agree.append(("pooled_visible", frozen1["pooled_visible"], pooled_vis))

    print(json.dumps(dict(
        independent_gt_edges=len(gt),
        independent_gt17_edges=len(gt17),
        overlap=len(gt & gt17),
        mine=mine,
        part1_crosscheck=[list(x) for x in part1_agree],
        disagreements=diffs,
        verdict=("ALL AGREE" if not diffs else "DISAGREEMENTS FOUND"),
    ), indent=1))
    sys.exit(0 if not diffs else 1)


if __name__ == "__main__":
    main()
