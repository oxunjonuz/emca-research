"""cb_family.py -- turn 128: the natural-occurrence family (see cb_instances.py).

  python3 cb_family.py <arm> <q1> <nsim> <out.json> [T] [N] [eps] [seed0]

Same statistic and same scoring as the main grid; only P(X_1=1) varies.
"""
import sys, os, json, time
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from cb_instances import make_instance
from cb_run import make_arm
from cb_agent import CBAgent


def run(q1, arm, seed, T=400, N=50, eps=0.3):
    np.random.seed(seed)
    model = make_instance(q1, N, eps)
    a = make_arm(arm)
    if isinstance(a, CBAgent):
        a.seed = seed
    r = a.run(T, model)
    out = {"arm": arm, "q1": q1, "seed": seed, "T": T, "regret": float(r),
           "n_trials_best_after_obs": None}
    if isinstance(a, CBAgent):
        out.update(a.diagnostics())
    else:
        out["chosen"] = int(a.best_action) if a.best_action is not None else None
    return out


if __name__ == "__main__":
    arm, q1, nsim, outp = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    T = int(sys.argv[5]) if len(sys.argv) > 5 else 400
    N = int(sys.argv[6]) if len(sys.argv) > 6 else 50
    eps = float(sys.argv[7]) if len(sys.argv) > 7 else 0.3
    s0 = int(sys.argv[8]) if len(sys.argv) > 8 else 1
    t0 = time.time()
    rows = [run(q1, arm, s0 + i, T, N, eps) for i in range(nsim)]
    pay = {"arm": arm, "q1": q1, "nsim": nsim, "T": T, "N": N, "eps": eps,
           "seed0": s0, "seconds": round(time.time() - t0, 2),
           "mean_regret": float(np.mean([r["regret"] for r in rows])),
           "sem_regret": float(np.std([r["regret"] for r in rows], ddof=1) /
                               np.sqrt(len(rows))),
           "frac_optimal": float(np.mean([r.get("chosen_is_optimal", 0) for r in rows])),
           "rows": rows}
    if arm.startswith("pure") or arm in ("beta0", "perm", "unc", "boot1", "boot5"):
        pay["mean_probes"] = float(np.mean([r.get("n_probes", 0) for r in rows]))
        pay["mean_opt_trials"] = float(np.mean([r.get("opt_trials", 0) for r in rows]))
        pay["frac_found_optimal"] = float(np.mean([r.get("found_optimal", 0) for r in rows]))
    with open(outp, "w") as f:
        json.dump(pay, f, indent=1)
    print(json.dumps({k: v for k, v in pay.items() if k != "rows"}))
