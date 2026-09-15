#!/usr/bin/env python3
"""run_cells_v2.py -- turn 132. Run a SHARD of the union-v2 grid in one plain
process and write one JSON per cell. Shards are launched as separate background
shell jobs; no multiprocessing.Pool is used (see union_matrix_v2.py for why).

  python3 run_cells_v2.py <nsim> <shard> <nshards> [group]
"""
import sys, os, json, time
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

from union_matrix_v2 import MASK_ARMS, PUB_ARMS, MASK_EPS, PUB_M, MASK_RICH_EPS, \
    OUT, fname, _job


def cells(group="all"):
    c = []
    if group in ("all", "mask"):
        for eps in MASK_EPS:
            for arm in MASK_ARMS:
                c.append(("mask", eps, arm))
    if group in ("all", "maskr"):
        for eps in MASK_RICH_EPS:
            for arm in MASK_ARMS:
                c.append(("maskr", eps, arm))
    if group in ("all", "pub"):
        for m in PUB_M:
            for arm in PUB_ARMS:
                c.append(("pub", m, arm))
    return c


def main():
    nsim = int(sys.argv[1])
    shard = int(sys.argv[2])
    nshards = int(sys.argv[3])
    group = sys.argv[4] if len(sys.argv) > 4 else "all"
    os.makedirs(OUT, exist_ok=True)
    T = 400
    todo = [c for i, c in enumerate(cells(group)) if i % nshards == shard]
    t0 = time.time()
    for k, (inst, param, arm) in enumerate(todo):
        fn = fname(inst, param, arm)
        if os.path.exists(fn):
            print("[shard %d] skip %s %s %s" % (shard, inst, param, arm), flush=True)
            continue
        res = _job((arm, inst, param, 1, nsim, T))
        with open(fn, "w") as f:
            json.dump(res, f, indent=1)
        print("[shard %d %2d/%d] %-6s p=%-5s %-15s mean=%.4f (%.0fs)"
              % (shard, k + 1, len(todo), inst, param, arm,
                 res["mean_regret"], time.time() - t0), flush=True)
    print("[shard %d] DONE %d cells in %.0fs" % (shard, len(todo), time.time() - t0))


if __name__ == "__main__":
    main()
