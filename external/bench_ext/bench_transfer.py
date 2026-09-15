#!/usr/bin/env python3
"""External-benchmark transfer test, frozen by bench_ext/PREREG_BENCH.md.

Reads ONLY the external Sachs 2005 files acquired from
cmu-phil/example-causal-datasets and their published golden-standard graph.
No own world, no own baseline. Deterministic: no unseeded randomness.
"""
import csv, json, math, hashlib, os, random, sys
from collections import defaultdict

DS = "ds"
OBS = os.path.join(DS, "sachs.experimental.mixed.txt")
GT = os.path.join(DS, "sachs.ground.truth.graph.txt")

ALPHA = 0.05
MIN_N = 50
N_NULL = 200
BASE_SEED = 20260912

PROTEINS = None


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def load():
    rows = list(csv.reader(open(OBS), delimiter="\t"))
    hdr = rows[0]
    prot = hdr[:11]
    cond = hdr[11:]
    data = [[float(x) for x in r] for r in rows[1:] if r and r[0].strip()]
    return prot, cond, data


def load_gt():
    nodes, edges = [], []
    for line in open(GT):
        s = line.strip()
        if s.startswith("Graph Nodes:"):
            nodes = s.split(":", 1)[1].strip().split(";")
        elif "-->" in s:
            a, b = s.split("-->")
            edges.append((a.split(".", 1)[1].strip().lower(), b.strip().lower()))
    return nodes, edges


def rank(v):
    """average ranks, deterministic tie handling"""
    idx = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def spearman_p(x, y):
    n = len(x)
    if n < 4:
        return 1.0
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return 1.0
    rho = max(-0.999999, min(0.999999, num / (dx * dy)))
    z = math.sqrt(n - 3) * 0.5 * math.log((1 + rho) / (1 - rho))
    return 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))


def strata(cond, data, prot):
    """row index lists per stratum. General = only first indicator active."""
    spec = cond[1:]  # all specific interventions, general stimulus excluded
    groups = defaultdict(list)
    for i, r in enumerate(data):
        active = [c for c, k in zip(cond, range(11, 20)) if r[k] > 0.5]
        specific = [c for c in active if c != cond[0]]
        if not specific:
            groups["__general__"].append(i)
        else:
            for c in specific:
                groups[c].append(i)
    return groups


def decisions(prot, data, groups):
    """returns per-pair (pooled_bool, stratum_bool, best_stratum_p)"""
    cols = {p: [r[j] for r in data] for j, p in enumerate(prot)}
    idx = {p: i for i, p in enumerate(prot)}
    out = {}
    for a in range(len(prot)):
        for b in range(a + 1, len(prot)):
            pa, pb = prot[a], prot[b]
            p_pool = spearman_p(cols[pa], cols[pb])
            # strata
            ks = [g for g in groups if len(groups[g]) >= MIN_N]
            K = max(1, len(ks))
            thr = ALPHA / K
            best, hit = 1.0, False
            for g in ks:
                ix = groups[g]
                x = [cols[pa][i] for i in ix]
                y = [cols[pb][i] for i in ix]
                pv = spearman_p(x, y)
                if pv < best:
                    best = pv
                if pv < thr:
                    hit = True
            out[(pa, pb)] = (p_pool < ALPHA, hit, p_pool, best, K)
    return out


def permute(data, seed):
    """Independently permute each protein column; marginals preserved exactly."""
    rng = random.Random(seed)
    n = len(data)
    new = [row[:] for row in data]
    for j in range(11):
        perm = list(range(n))
        rng.shuffle(perm)
        src = [row[j] for row in data]
        for i in range(n):
            new[i][j] = src[perm[i]]
    return new


def enrich(dec, true_pairs):
    """(P(true|context-exclusive), base rate, enrichment, counts)"""
    base = len(true_pairs) / len(dec)
    excl = [k for k, v in dec.items() if (not v[0]) and v[1]]
    hits = sum(1 for k in excl if k in true_pairs)
    p = hits / len(excl) if excl else 0.0
    return dict(n_exclusive=len(excl), exclusive_true=hits,
                p_true_given_exclusive=p, base_rate=base,
                enrichment=(p / base if base else 0.0))


def main():
    prot, cond, data = load()
    nodes, edges = load_gt()
    true_pairs = set()
    for a, b in edges:
        x, y = prot.index(a), prot.index(b)
        true_pairs.add((prot[min(x, y)], prot[max(x, y)]))
    groups = strata(cond, data, prot)

    dec = decisions(prot, data, groups)
    pooled_vis = [k for k, v in dec.items() if v[0]]
    recall = sum(1 for k in true_pairs if dec[k][0]) / len(true_pairs)
    precision = sum(1 for k in pooled_vis if k in true_pairs) / len(pooled_vis)

    E1 = enrich(dec, true_pairs)

    # null: permute protein columns, rerun full pipeline
    null_enr, null_excl = [], []
    for r in range(N_NULL):
        d2 = permute(data, BASE_SEED + r)
        dec2 = decisions(prot, d2, groups)
        e = enrich(dec2, true_pairs)
        null_enr.append(e["enrichment"])
        null_excl.append(e["n_exclusive"])

    out = dict(
        obs_sha256=sha256(OBS), gt_sha256=sha256(GT),
        n_rows=len(data), n_proteins=len(prot),
        strata={k: len(v) for k, v in sorted(groups.items())},
        n_true_pairs=len(true_pairs),
        pooled_visible=len(pooled_vis),
        pooled_recall=recall, pooled_precision=precision,
        E1=E1,
        null_mean_enrichment=sum(null_enr) / len(null_enr),
        null_sd_enrichment=(sum((x - sum(null_enr) / len(null_enr)) ** 2
                                for x in null_enr) / (len(null_enr) - 1)) ** 0.5,
        null_max_enrichment=max(null_enr),
        null_mean_exclusive=sum(null_excl) / len(null_excl),
        null_n_exclusive_zero=sum(1 for x in null_excl if x == 0),
        pairs=({"%s|%s" % k: dict(pooled=v[0], stratum=v[1],
                                  p_pooled=v[2], best_stratum_p=v[3], K=v[4],
                                  is_true=k in true_pairs)
                for k, v in sorted(dec.items())}),
    )
    # H verdicts by the frozen rule
    out["H1_pooled_sees_minority"] = "PASS" if recall < 0.75 else "FAIL"
    out["H2_masking_exists"] = "PASS" if E1["n_exclusive"] > 0 else "FAIL"
    null_ge = sum(1 for x in null_enr if x >= E1["enrichment"])
    out["null_ge_observed"] = null_ge
    out["H3_transfer"] = ("PASS" if (E1["enrichment"] > 1.0 and null_ge == 0)
                          else "FAIL")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
