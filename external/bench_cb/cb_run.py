"""cb_run.py -- turn 128 driver: one (arm, m, seed) cell of the causal-bandit
comparison, or a whole sweep. Prints JSON to stdout.

Usage:
  python3 cb_run.py cell   <arm> <m> <seed> [T] [N] [eps]
  python3 cb_run.py sweep  <arm> <m> <nsim> [T] [N] [eps] [seed0]
  python3 cb_run.py faithful <nsim> [m ...]      # published arms, Fig-2a shape

All randomness is the authors' global NumPy RNG, seeded per run with the run's
seed -- applied to every arm equally.
"""
import sys, os, json, time
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)

import models as M
import algorithms as A
from cb_agent import CBAgent

PUBLISHED = {
    "alg1_pub": lambda: A.ParallelCausal(),
    "alg2_pub": lambda: A.GeneralCausal(truncate="None"),
    "sr_pub":   lambda: A.SuccessiveRejects(),
    "ucb_pub":  lambda: A.AlphaUCB(2),
}
MINN = {"pure_minn5": 5, "pure_minn10": 10, "pure_minn20": 20}


def make_arm(name):
    if name in PUBLISHED:
        return PUBLISHED[name]()
    min_n = MINN.get(name)
    beta = 0.0 if name == "beta0" else None
    kind = {"beta0": "pure", "perm": "pure", "pure_minn5": "pure",
            "pure_minn10": "pure", "pure_minn20": "pure"}.get(name, name)
    return CBAgent(kind=kind, seed=0, min_n=min_n, beta=beta)


def run_cell(arm, m, seed, T=400, N=50, eps=0.3):
    np.random.seed(seed)
    model = M.Parallel.create(N, m, eps)
    a = make_arm(arm)
    if isinstance(a, CBAgent):
        a.seed = seed
    t0 = time.time()
    r = a.run(T, model)
    out = {"arm": arm, "m": m, "seed": seed, "T": T, "N": N, "eps": eps,
           "regret": float(r), "seconds": round(time.time() - t0, 3),
           "m_true": int(model.m)}
    if isinstance(a, CBAgent):
        out.update(a.diagnostics())
    else:
        out["chosen"] = int(a.best_action) if a.best_action is not None else None
    return out


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "cell":
        arm, m, seed = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        T = int(sys.argv[5]) if len(sys.argv) > 5 else 400
        N = int(sys.argv[6]) if len(sys.argv) > 6 else 50
        eps = float(sys.argv[7]) if len(sys.argv) > 7 else 0.3
        print(json.dumps(run_cell(arm, m, seed, T, N, eps)))
    elif mode == "sweep":
        arm, m, nsim = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        T = int(sys.argv[5]) if len(sys.argv) > 5 else 400
        N = int(sys.argv[6]) if len(sys.argv) > 6 else 50
        eps = float(sys.argv[7]) if len(sys.argv) > 7 else 0.3
        s0 = int(sys.argv[8]) if len(sys.argv) > 8 else 1
        rows = [run_cell(arm, m, s0 + i, T, N, eps) for i in range(nsim)]
        print(json.dumps(rows))
    elif mode == "faithful":
        nsim = int(sys.argv[2])
        ms = [int(x) for x in sys.argv[3:]] or [2, 8, 16, 25, 40, 49]
        rows = []
        for m in ms:
            for name in ["alg1_pub", "sr_pub", "alg2_pub", "ucb_pub"]:
                for i in range(nsim):
                    rows.append(run_cell(name, m, 1 + i))
                print(json.dumps({"arm": name, "m": m,
                                  "mean": float(np.mean([r["regret"] for r in rows
                                                         if r["arm"] == name and r["m"] == m]))}),
                      file=sys.stderr)
        print(json.dumps(rows))
