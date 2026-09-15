#!/usr/bin/env python3
"""Independent reproduction of the EXTERNAL published constraint-based result.

The bnlearn HOWTO reports, on the observational Sachs file with a
constraint-based algorithm (inter.iamb, test='cor'):

    skeleton: tp 8  fp 0  fn 9        (validated 17-arc network)
    DAG:      8 arcs, only 2 directed

This is an independent attempt to reproduce that published number with my own
constraint-based skeleton search (IAMB-style: discover each node's Markov
blanket by incremental association, then prune with Fisher-z partial
correlations), sharing no code with bnlearn and no code with my arms above.
If it lands near the published 8, the external result is reproduced; if it
does not, that is reported too.
"""
import csv, json, math
from itertools import combinations
from scipy import stats

OBS = "ds/sachs.2005.continuous.txt"
ALPHA = 0.05


def key(a, b):
    return (a, b) if a < b else (b, a)


GT17 = [("pkc","pka"),("pkc","raf"),("pka","raf"),("pkc","mek"),("pka","mek"),
        ("raf","mek"),("mek","erk"),("pka","erk"),("erk","akt"),("pka","akt"),
        ("pkc","p38"),("pka","p38"),("pkc","jnk"),("pka","jnk"),("plc","pip3"),
        ("plc","pip2"),("pip3","pip2")]


def pcorr_p(X, i, j, S):
    """p-value for partial Spearman? bnlearn used test='cor' = partial Pearson
    on the raw (continuous) data. Use Pearson partial correlation, Fisher z."""
    cols = [i, j] + list(S)
    A = X[:, cols]
    C = stats.pearsonr if False else None
    # partial correlation via residual correlation
    import numpy as np
    Z = np.column_stack([A[:, 0], A[:, 1]])
    if S:
        R = A[:, 2:]
        R = np.column_stack([R, np.ones(len(R))])
        beta = np.linalg.lstsq(R, Z, rcond=None)[0]
        Z = Z - R @ beta
    n = len(Z)
    r = np.corrcoef(Z[:, 0], Z[:, 1])[0, 1]
    r = max(-0.999999, min(0.999999, float(r)))
    df = n - len(S) - 2
    if df < 1:
        return 1.0
    t = r * math.sqrt(df / (1 - r * r))
    return float(2 * stats.t.sf(abs(t), df))


def mb(X, nodes, target):
    """IAMB: grow then shrink the Markov blanket of `target`."""
    names = [n for n in nodes if n != target]
    idx = {n: i for i, n in enumerate(nodes)}
    mb_set = []
    # forward
    while True:
        best, bestp = None, 1.0
        for c in names:
            if c in mb_set:
                continue
            for S in [tuple(sorted(mb_set))]:
                p = pcorr_p(X, idx[target], idx[c], [idx[s] for s in S])
                if p < bestp:
                    best, bestp = c, p
        if best is None or bestp >= ALPHA:
            break
        mb_set.append(best)
    # backward
    changed = True
    while changed:
        changed = False
        for c in list(mb_set):
            rest = [s for s in mb_set if s != c]
            p = pcorr_p(X, idx[target], idx[c], [idx[s] for s in rest])
            if p >= ALPHA:
                mb_set.remove(c)
                changed = True
    return mb_set


def main():
    import numpy as np
    rows = list(csv.reader(open(OBS), delimiter="\t"))
    hdr = rows[0]
    X = np.array([[float(x) for x in r] for r in rows[1:] if r and r[0].strip()])
    nodes = hdr[:11]

    skeleton = set()
    for t in nodes:
        for c in mb(X, nodes, t):
            skeleton.add(key(t, c))

    gt = {key(a, b) for a, b in GT17}
    tp = len(skeleton & gt)
    fp = len(skeleton - gt)
    fn = len(gt - skeleton)
    print(json.dumps(dict(
        n_rows=len(X),
        skeleton_size=len(skeleton),
        tp_edges=tp, fp_edges=fp,
        fn_against_gt17=fn,
        published_interiamb_skeleton=dict(tp=8, fp=0, fn=9),
        note=("published scatter over the data is expected: the HOWTO reports "
              "the DAG inter.iamb returns, skeleton-of-that = 8 true / 0 false "
              "/ 9 missed"),
        reproduced_near_published=(abs(tp - 8) <= 3),
    ), indent=1))


if __name__ == "__main__":
    main()
