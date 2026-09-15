"""union_matrix.py -- turn 129. The preregistered grid, multiprocessing.

  python3 union_matrix.py <nsim> [procs]

Grid (PREREG_UNION.md §3):
  MASK instance (context-specific), eps swept over {0.15, 0.25, 0.35}:
      arms: union, union_noctx, union_noexp, union_nocost, pure, beta0,
            budget_pub, uniform_policy
  PUB instance (published parallel), m swept over {2,8,16,25,40,49}:
      arms: union, union_noctx, union_noexp, pure, alg1_pub, alg2_pub, sr_pub,
            ucb_pub

Writes one JSON per (inst, param, arm) into results_union/ and a SUMMARY.json.
"""
import sys, os, json, time
from multiprocessing import Pool

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)

OUT = os.path.join(_HERE, "results_union")

MASK_ARMS = ["union", "union_pooledexp", "union_noctx", "union_noexp",
             "union_nocost", "pure", "beta0", "budget_pub", "uniform_policy"]
PUB_ARMS = ["union", "union_noctx", "union_noexp", "pure",
            "alg1_pub", "alg2_pub", "sr_pub", "ucb_pub"]
MASK_EPS = [0.15, 0.25, 0.35]
PUB_M = [2, 8, 16, 25, 40, 49]
MASK_RICH_EPS = [0.25, 0.35]

def _job(args):
    arm, inst, param, seed0, nsim, T = args
    from union_run import run_cell
    import numpy as np
    rows = [run_cell(arm, inst, param, seed0 + i, T) for i in range(nsim)]
    regs = [r["regret"] for r in rows]
    return {"arm": arm, "inst": inst, "param": param, "nsim": nsim, "seed0": seed0,
            "T": T, "mean_regret": float(np.mean(regs)),
            "sem_regret": float(np.std(regs, ddof=1) / np.sqrt(len(regs))),
            "sd_regret": float(np.std(regs, ddof=1)),
            "frac_optimal": float(np.mean([r.get("chosen_is_optimal", 0) for r in rows])),
            "mean_probes": float(np.mean([r.get("n_probes", 0) for r in rows])),
            "mean_explore": float(np.mean([r.get("n_explore_picks", 0) for r in rows])),
            "rows": rows}


def fname(inst, param, arm):
    return os.path.join(OUT, "%s_p%s_%s.json" % (inst, str(param).replace(".", "p"), arm))


def main():
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    os.makedirs(OUT, exist_ok=True)
    T = 400
    jobs = []
    for eps in MASK_EPS:
        for arm in MASK_ARMS:
            jobs.append((arm, "mask", eps, 1, nsim, T))
    for eps in MASK_RICH_EPS:
        for arm in MASK_ARMS:
            jobs.append((arm, "maskr", eps, 1, nsim, T))
    for m in PUB_M:
        for arm in PUB_ARMS:
            jobs.append((arm, "pub", m, 1, nsim, T))
    t0 = time.time()
    with Pool(procs) as p:
        for i, res in enumerate(p.imap_unordered(_job, jobs)):
            fn = fname(res["inst"], res["param"], res["arm"])
            with open(fn, "w") as f:
                json.dump(res, f, indent=1)
            print("[%3d/%d] %-6s p=%-5s %-15s mean=%.4f sem=%.4f  (%.0fs)"
                  % (i + 1, len(jobs), res["inst"], res["param"], res["arm"],
                     res["mean_regret"], res["sem_regret"], time.time() - t0),
                  flush=True)
    # summary
    summary = {}
    for fn in sorted(os.listdir(OUT)):
        if fn.endswith(".json") and fn != "SUMMARY.json":
            with open(os.path.join(OUT, fn)) as f:
                d = json.load(f)
            key = "%s|%s|%s" % (d["inst"], d["param"], d["arm"])
            summary[key] = {k: d[k] for k in
                            ("mean_regret", "sem_regret", "sd_regret", "frac_optimal",
                             "mean_probes", "mean_explore", "nsim")}
    with open(os.path.join(OUT, "SUMMARY.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("TOTAL %.0fs, %d cells" % (time.time() - t0, len(summary)))


if __name__ == "__main__":
    main()
