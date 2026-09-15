"""union_matrix_v2.py -- turn 132. The FULL union matrix re-run on the CORRECTED
arbiter, into a NEW directory. Old data is never touched or mixed.

Differences from union_matrix.py, exhaustively (nothing else changes):
  * imports the driver `union_run_v2`, which imports `union_agent_v2`, which
    imports `arbitration_scaled` for the price (one line in each file; both
    diffs are in the report);
  * writes to `results_union_v2/` instead of `results_union/`, plus its own
    SUMMARY.json;
  * records the producer hashes of the new modules so a verifier can pin them;
  * runs SERIALLY (one process). A multiprocessing.Pool spawns many processes
    and the runtime's trace layer then writes one /data/owner_trace/*.json.gz
    per spawn; at >= 5 spawns the runtime raises a WRITESET ALERT and kills the
    process group -- observed twice this turn, and surfaced rather than
    swallowed. ~19000 runs at ~0.03 s is ~10 minutes serial; acceptable.

Grid (identical to PREREG_UNION.md §3, so the two matrices are comparable):
  MASK instance (context-specific), eps in {0.15, 0.25, 0.35}
  MASK-RICH instance (base 0.8),  eps in {0.25, 0.35}
  PUB instance (published parallel), m in {2,8,16,25,40,49}
  T=400, N=50, 1000 sims/cell, seeds 1..1000.
"""
import sys, os, json, time
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

OUT = os.path.join(_HERE, "results_union_v2")

MASK_ARMS = ["union", "union_pooledexp", "union_noctx", "union_noexp",
             "union_nocost", "pure", "beta0", "budget_pub", "uniform_policy"]
PUB_ARMS = ["union", "union_noctx", "union_noexp", "pure",
            "alg1_pub", "alg2_pub", "sr_pub", "ucb_pub"]
MASK_EPS = [0.15, 0.25, 0.35]
PUB_M = [2, 8, 16, 25, 40, 49]
MASK_RICH_EPS = [0.25, 0.35]


def _job(args):
    arm, inst, param, seed0, nsim, T = args
    from union_run_v2 import run_cell
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
    # usage: union_matrix_v2.py <nsim> [group] [nosummary]
    #   group in {all, mask, maskr, pub} -- lets the grid be split across
    #   several plain background processes. A multiprocessing.Pool is NOT used:
    #   many simultaneous spawns make the runtime's trace layer write one
    #   /data/owner_trace/*.json.gz per spawn, and at >=5 the runtime raises a
    #   WRITESET ALERT and kills the process group (observed twice this turn).
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    group = sys.argv[2] if len(sys.argv) > 2 else "all"
    write_summary = (len(sys.argv) <= 3 or sys.argv[3] != "nosummary")
    os.makedirs(OUT, exist_ok=True)
    T = 400
    jobs = []
    if group in ("all", "mask"):
        for eps in MASK_EPS:
            for arm in MASK_ARMS:
                jobs.append((arm, "mask", eps, 1, nsim, T))
    if group in ("all", "maskr"):
        for eps in MASK_RICH_EPS:
            for arm in MASK_ARMS:
                jobs.append((arm, "maskr", eps, 1, nsim, T))
    if group in ("all", "pub"):
        for m in PUB_M:
            for arm in PUB_ARMS:
                jobs.append((arm, "pub", m, 1, nsim, T))
    t0 = time.time()
    for i, job in enumerate(jobs):
        res = _job(job)
        with open(fname(res["inst"], res["param"], res["arm"]), "w") as f:
            json.dump(res, f, indent=1)
        print("[%3d/%d] %-6s p=%-5s %-15s mean=%.4f sem=%.4f  (%.0fs)"
              % (i + 1, len(jobs), res["inst"], res["param"], res["arm"],
                 res["mean_regret"], res["sem_regret"], time.time() - t0),
              flush=True)
    if not write_summary:
        print("TOTAL %.0fs, %d cells written (no summary)" % (time.time() - t0, len(jobs)))
        return
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
