"""cb_matrix.py -- turn 128: run one (arm, m) cell over N seeds and write JSON.

  python3 cb_matrix.py <arm> <m> <nsim> <out.json> [T] [N] [eps] [seed0]
"""
import sys, os, json, time
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from cb_run import run_cell

def main():
    arm, m, nsim, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    T = int(sys.argv[5]) if len(sys.argv) > 5 else 400
    N = int(sys.argv[6]) if len(sys.argv) > 6 else 50
    eps = float(sys.argv[7]) if len(sys.argv) > 7 else 0.3
    s0 = int(sys.argv[8]) if len(sys.argv) > 8 else 1
    t0 = time.time()
    rows = [run_cell(arm, m, s0 + i, T, N, eps) for i in range(nsim)]
    payload = {"arm": arm, "m": m, "nsim": nsim, "T": T, "N": N, "eps": eps,
               "seed0": s0, "seconds": round(time.time() - t0, 2),
               "mean_regret": float(np.mean([r["regret"] for r in rows])),
               "sem_regret": float(np.std([r["regret"] for r in rows], ddof=1) /
                                   np.sqrt(len(rows))),
               "frac_optimal": float(np.mean([r.get("chosen_is_optimal", 0)
                                              for r in rows])),
               "rows": rows}
    if arm.startswith("pure") or arm in ("beta0", "perm", "unc", "boot1", "boot5"):
        payload["frac_empty_gen_run"] = float(np.mean(
            [1.0 if r.get("n_gen_calls", 0) and
             r.get("n_empty_gen", 0) == r.get("n_gen_calls", 0) else 0.0
             for r in rows]))
        payload["mean_probes"] = float(np.mean([r.get("n_probes", 0) for r in rows]))
        payload["mean_opt_trials"] = float(np.mean([r.get("opt_trials", 0)
                                                    for r in rows]))
        payload["frac_found_optimal"] = float(np.mean([r.get("found_optimal", 0)
                                                       for r in rows]))
    with open(out, "w") as f:
        json.dump(payload, f, indent=1)
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}))

if __name__ == "__main__":
    main()
