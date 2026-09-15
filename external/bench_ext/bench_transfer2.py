#!/usr/bin/env python3
"""External-benchmark transfer test, part 2: which half of the principle
survives on Sachs 2005?

Frozen by bench_ext/PREREG_BENCH.md. Reads only the external files.

Part 1 (bench_transfer.py) measured the campaign's literal operational form
(context-EXCLUSIVE = invisible pooled, visible in a stratum) and it came back
empty: pooled recall 0.95, zero context-exclusive pairs. This script tests the
transferable form of the same idea -- context-STABILITY of an association --
and compares every arm against the PUBLISHED numbers of the external methods.
"""
import csv, json, math, os, random, hashlib
from collections import defaultdict

DS = "ds"
OBS = os.path.join(DS, "sachs.experimental.mixed.txt")
GT20 = os.path.join(DS, "sachs.ground.truth.graph.txt")
# bnlearn's validated network (17 arcs) written out verbatim from the
# published HOWTO model string: [PKC][PKA|PKC][Raf|PKC:PKA][Mek|PKC:PKA:Raf]
# [Erk|Mek:PKA][Akt|Erk:PKA][P38|PKC:PKA][Jnk|PKC:PKA][Plcg][PIP3|Plcg]
# [PIP2|Plcg:PIP3]
GT17 = [("pkc","pka"),("pkc","raf"),("pka","raf"),("pkc","mek"),("pka","mek"),
        ("raf","mek"),("mek","erk"),("pka","erk"),("erk","akt"),("pka","akt"),
        ("pkc","p38"),("pka","p38"),("pkc","jnk"),("pka","jnk"),("plc","pip3"),
        ("plc","pip2"),("pip3","pip2")]

ALPHA = 0.05
MIN_N = 50
N_NULL = 200
BASE_SEED = 20260912


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def load():
    rows = list(csv.reader(open(OBS), delimiter="\t"))
    hdr = rows[0]
    prot, cond = hdr[:11], hdr[11:]
    data = [[float(x) for x in r] for r in rows[1:] if r and r[0].strip()]
    return prot, cond, data


def load_gt():
    nodes, edges = [], []
    for line in open(GT20):
        s = line.strip()
        if s.startswith("Graph Nodes:"):
            nodes = s.split(":", 1)[1].strip().split(";")
        elif "-->" in s:
            a, b = s.split("-->")
            edges.append((a.split(".", 1)[1].strip().lower(), b.strip().lower()))
    return nodes, edges


def key(a, b):
    return (a, b) if a < b else (b, a)


def rank(v):
    idx = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v); i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def sp(x, y):
    """Spearman rho and two-sided p, Fisher z."""
    n = len(x)
    if n < 4:
        return 0.0, 1.0
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return 0.0, 1.0
    rho = max(-0.999999, min(0.999999, num / (dx * dy)))
    z = math.sqrt(n - 3) * 0.5 * math.log((1 + rho) / (1 - rho))
    p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))
    return rho, p


def strata(cond, data):
    groups = defaultdict(list)
    for i, r in enumerate(data):
        act = [c for c, k in zip(cond, range(11, 20)) if r[k] > 0.5]
        sp_ = [c for c in act if c != cond[0]]
        if not sp_:
            groups["__general__"].append(i)
        else:
            for c in sp_:
                groups[c].append(i)
    return groups


def arms(prot, data, groups):
    cols = {p: [r[j] for r in data] for j, p in enumerate(prot)}
    ks = [g for g in sorted(groups) if len(groups[g]) >= MIN_N]
    K = max(1, len(ks))
    out = {}
    for a in range(len(prot)):
        for b in range(a + 1, len(prot)):
            pa, pb = prot[a], prot[b]
            rho_p, p_pool = sp(cols[pa], cols[pb])
            rhos, ps = [], []
            for g in ks:
                ix = groups[g]
                rr, pp = sp([cols[pa][i] for i in ix], [cols[pb][i] for i in ix])
                rhos.append(rr); ps.append(pp)
            # arm A: pooled marginal
            A = p_pool < ALPHA
            # arm B: context-STABLE -- significant pooled and every stratum
            # with n>=MIN_N significant with the same sign, at alpha/K
            thr = ALPHA / K
            same = all((p < thr and r * rho_p > 0) for r, p in zip(rhos, ps))
            B = A and same
            # arm C: general stratum must confirm (the point of the campaign:
            # a relation true in the pooled table but absent where unpolluted)
            gi = groups.get("__general__")
            if gi and len(gi) >= MIN_N:
                rg, pg = sp([cols[pa][i] for i in gi], [cols[pb][i] for i in gi])
                C = A and pg < ALPHA and rg * rho_p > 0
            else:
                C = A
            # heterogeneity of rho across strata (textbook chi-square-like)
            wsum = sum((len(groups[g]) - 3) for g in ks)
            if wsum > 0:
                zs = [math.sqrt(len(groups[g]) - 3) *
                      (0.5 * math.log((1 + max(-0.999999, min(0.999999, r))) /
                                      (1 - max(-0.999999, min(0.999999, r)))))
                      for r, g in zip(rhos, ks)]
                zbar = sum(zs) / len(zs)
                Q = sum((z - zbar) ** 2 for z in zs)
                # Q ~ chi2 with len(zs)-1 df
                D = len(zs) - 1
                p_het = 1.0 - _chi2cdf(Q, D)
                spread = max(rhos) - min(rhos)
            else:
                Q, p_het, spread = 0.0, 1.0, 0.0
            out[key(pa, pb)] = dict(
                rho_pooled=rho_p, p_pooled=p_pool, rho_general=rhos[0],
                min_stratum_p=min(ps), max_stratum_p=max(ps),
                spread=spread, Q=Q, p_het=p_het,
                A=A, B=B, C=C)
    return out


def _chi2cdf(x, k):
    """regularized lower incomplete gamma P(k/2, x/2) via series/continued frac"""
    a = k / 2.0; xx = x / 2.0
    if xx <= 0:
        return 0.0
    if xx < a + 1:
        term = 1.0 / a; s = term; n = 0
        while True:
            n += 1
            term *= xx / (a + n)
            s += term
            if abs(term) < 1e-14 * abs(s) or n > 10000:
                break
        return s * math.exp(-xx + a * math.log(xx) - math.lgamma(a))
    else:
        b = xx + 1 - a; c = 1e30; d = 1 / b; h = d
        for i in range(1, 10000):
            an = -i * (i - a)
            b += 2
            d = an * d + b
            if abs(d) < 1e-30:
                d = 1e-30
            c = b + an / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1 / d
            de = d * c
            h *= de
            if abs(de - 1) < 1e-14:
                break
        return 1.0 - math.exp(-xx + a * math.log(xx) - math.lgamma(a)) * h


def permute(data, seed):
    rng = random.Random(seed)
    n = len(data)
    new = [row[:] for row in data]
    for j in range(11):
        perm = list(range(n)); rng.shuffle(perm)
        src = [row[j] for row in data]
        for i in range(n):
            new[i][j] = src[perm[i]]
    return new


def pr(dec, arm, gt):
    sel = [k for k, v in dec.items() if v[arm]]
    tp = sum(1 for k in sel if k in gt)
    return dict(n_sel=len(sel), tp=tp, fp=len(sel) - tp, fn=len(gt) - tp,
                precision=(tp / len(sel) if sel else 0.0),
                recall=(tp / len(gt) if gt else 0.0))


def main():
    prot, cond, data = load()
    nodes, edges = load_gt()
    gt20 = {key(a, b) for a, b in edges}
    gt17 = {key(a, b) for a, b in GT17}
    groups = strata(cond, data)
    dec = arms(prot, data, groups)

    res = dict(obs_sha256=sha256(OBS), gt20_sha256=sha256(GT20),
               n_rows=len(data), strata={k: len(v) for k, v in sorted(groups.items())},
               n_gt20=len(gt20), n_gt17=len(gt17),
               gt_overlap=len(gt20 & gt17))
    for tag, gt in (("gt20", gt20), ("gt17", gt17)):
        for arm in ("A", "B", "C"):
            res["%s_arm%s" % (tag, arm)] = pr(dec, arm, gt)
    # how well does context-stability separate true from false *among* the
    # pairs the pooled arm accepted? (pooled base rate is the control)
    for tag, gt in (("gt20", gt20), ("gt17", gt17)):
        acc = [k for k, v in dec.items() if v["A"]]
        for stat in ("p_het", "spread"):
            t = sorted(dec[k][stat] for k in acc if k in gt)
            f = sorted(dec[k][stat] for k in acc if k not in gt)
            mt = sum(t) / len(t) if t else 0
            mf = sum(f) / len(f) if f else 0
            res["%s_%s_true_mean" % (tag, stat)] = mt
            res["%s_%s_false_mean" % (tag, stat)] = mf
    res["published_bnlearn_interiamb"] = dict(
        note="published on sachs observational data, test='cor'",
        skeleton_tp=8, skeleton_fp=0, skeleton_fn=9,
        arcs=8, directed=2)
    res["published_bnlearn_mbde"] = dict(
        note="intervention-aware model averaging (mbde), validated network",
        tp=17, fp=8, fn=0)
    # ---- controls: same arms under the permutation null ----
    nullA, nullB, nullC = [], [], []
    nullB_sel, nullC_sel = [], []
    for r in range(N_NULL):
        d2 = permute(data, BASE_SEED + r)
        dec2 = arms(prot, d2, groups)
        rB, rC = pr(dec2, "B", gt20), pr(dec2, "C", gt20)
        nullA.append(pr(dec2, "A", gt20)["precision"])
        nullB.append(rB["precision"]); nullC.append(rC["precision"])
        nullB_sel.append(rB["n_sel"]); nullC_sel.append(rC["n_sel"])
        if r == 0:
            res["null_check_armA_n_sel"] = pr(dec2, "A", gt20)["n_sel"]

    def ms(x):
        m = sum(x) / len(x)
        s = (sum((v - m) ** 2 for v in x) / (len(x) - 1)) ** 0.5 if len(x) > 1 else 0.0
        return m, s
    for nm, arr in (("A", nullA), ("B", nullB), ("C", nullC)):
        m, s = ms(arr)
        res["null_arm%s_precision_mean" % nm] = m
        res["null_arm%s_precision_sd" % nm] = s
        res["null_arm%s_precision_max" % nm] = max(arr)
        res["null_arm%s_ge_observed" % nm] = sum(
            1 for v in arr if v >= res["gt20_arm%s" % nm]["precision"])
    res["null_armB_sel_mean"] = sum(nullB_sel) / len(nullB_sel)
    res["null_armB_sel_max"] = max(nullB_sel)
    res["null_armB_sel_nonzero"] = sum(1 for x in nullB_sel if x > 0)
    res["null_armC_sel_mean"] = sum(nullC_sel) / len(nullC_sel)
    res["null_armC_sel_max"] = max(nullC_sel)

    # ---- precision@k: pooled ranking vs context-stability ranking ----
    allp = sorted(dec)
    by_pool = sorted(allp, key=lambda k: dec[k]["p_pooled"])
    by_het = sorted(allp, key=lambda k: dec[k]["p_het"])
    by_spread = sorted(allp, key=lambda k: -dec[k]["spread"])
    for k in (3, 5, 10, 20, 54):
        res["prec_at_%d_pooled" % k] = sum(1 for x in by_pool[:k] if x in gt20) / k
        res["prec_at_%d_het" % k] = sum(1 for x in by_het[:k] if x in gt20) / k
        res["prec_at_%d_spread" % k] = sum(1 for x in by_spread[:k] if x in gt20) / k

    print(json.dumps(res, indent=1, sort_keys=True))
    with open("preds_bench2.json", "w") as f:
        json.dump({"%s|%s" % k: v for k, v in dec.items()}, f,
                  indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
