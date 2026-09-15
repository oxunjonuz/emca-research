"""union_run.py -- turn 129 driver. One (arm, instance, param, seed) cell, or a
sweep. Prints JSON.

  python3 union_run.py cell  <arm> <inst> <param> <seed> [T] [N]
  python3 union_run.py sweep <arm> <inst> <param> <nsim> <out.json> [T] [N] [seed0]

inst:  mask   -- the context-specific instance (param = eps_rev)
       pub    -- the published parallel instance (param = m)
Arms: union/union_noctx/union_noexp/union_nocost/pure/beta0 (union_agent),
      alg1_pub/alg2_pub/sr_pub/ucb_pub (the authors' own code),
      budget_pub (declared cost-aware adaptation, see budget_agent.py).
"""
import sys, os, json, time
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)

import models as M
import algorithms as A
from union_agent import make_agent
from union_instance import MaskedParallel, PublishedParallel

PUBLISHED = {
    "alg1_pub": lambda: A.ParallelCausal(),
    "alg2_pub": lambda: A.GeneralCausal(truncate="None"),
    "sr_pub":   lambda: A.SuccessiveRejects(),
    "ucb_pub":  lambda: A.AlphaUCB(2),
}
UNION_KINDS = ("union", "union_pooledexp", "union_noctx", "union_noexp",
               "union_nocost", "pure", "beta0")


def build_model(inst, param):
    if inst == "mask":
        # param = eps (the context-specific effect size; the "reversal" is that
        # the same eps is subtracted in the other context)
        return MaskedParallel(N=50, m=1, eps=float(param))
    if inst == "maskr":
        # same, but a RICH alternative (base=0.8): the cost-aware arbiter's price
        # (rich*H + cost) is now high, so it may refuse to explore at all.
        return MaskedParallel(N=50, m=1, eps=float(param), base=0.8)
    if inst == "pub":
        return PublishedParallel(M.Parallel.create(50, int(param), 0.3))
    raise ValueError(inst)


class PublishedAdapter(object):
    """Drive the authors' own algorithm classes against either our wrapper or
    their own model. Their classes call model.sample(a) -> (x, y); our
    PublishedParallel wrapper returns (x, y, 0)."""
    def __init__(self, name):
        self.name = name
        self.alg = PUBLISHED[name]()

    def run(self, T, model):
        inner = model._m if isinstance(model, PublishedParallel) else model
        return self.alg.run(T, inner)


def run_cell(arm, inst, param, seed, T=400, N=50):
    np.random.seed(seed)
    model = build_model(inst, param)
    t0 = time.time()
    if arm in UNION_KINDS:
        ag = make_agent(arm, seed)
        r = ag.run(T, model)
        diag = ag.diagnostics()
        diag["policy"] = dict(ag.policy)
    elif arm in PUBLISHED:
        if inst != "pub":
            raise ValueError("published arms run only on the published instance")
        ag = PublishedAdapter(arm)
        r = ag.run(T, model)
        diag = {"chosen": getattr(ag.alg, "best_action", None)}
    elif arm == "budget_pub":
        from budget_agent import BudgetAgent
        ag = BudgetAgent(seed=seed)
        r = ag.run(T, model)
        diag = ag.diagnostics()
        diag["policy"] = dict(ag.policy)
    elif arm == "uniform_policy":
        # a fixed pooled-arm policy: best pooled arm only, never explores new
        # arms. The floor any context-blind method hits on mask.
        from union_agent import _UniformPolicy
        ag = _UniformPolicy(seed=seed)
        r = ag.run(T, model)
        diag = ag.diagnostics()
        diag["policy"] = dict(ag.policy)
    else:
        raise ValueError(arm)
    out = {"arm": arm, "inst": inst, "param": param, "seed": seed, "T": T,
           "regret": float(r), "seconds": round(time.time() - t0, 4),
           "optimal": float(model.optimal)}
    out.update(diag)
    # JSON-safe: numpy scalars (published arms return np.int64 best_action)
    for k, v in list(out.items()):
        if isinstance(v, dict):
            out[k] = {kk: (int(vv) if hasattr(vv, "item") else vv)
                      for kk, vv in v.items()}
        elif hasattr(v, "item"):
            out[k] = v.item()
    return out


def sweep(arm, inst, param, nsim, T=400, N=50, seed0=1):
    rows = [run_cell(arm, inst, param, seed0 + i, T, N) for i in range(nsim)]
    regs = [r["regret"] for r in rows]
    return {"arm": arm, "inst": inst, "param": param, "nsim": nsim, "T": T,
            "N": N, "seed0": seed0,
            "mean_regret": float(np.mean(regs)),
            "sem_regret": float(np.std(regs, ddof=1) / np.sqrt(len(regs))),
            "frac_optimal": float(np.mean([r.get("chosen_is_optimal", 0) for r in rows])),
            "rows": rows}


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "cell":
        arm, inst, param, seed = sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
        T = int(sys.argv[6]) if len(sys.argv) > 6 else 400
        print(json.dumps(run_cell(arm, inst, param, seed, T)))
    elif mode == "sweep":
        arm, inst, param, nsim, out = (sys.argv[2], sys.argv[3], sys.argv[4],
                                       int(sys.argv[5]), sys.argv[6])
        T = int(sys.argv[7]) if len(sys.argv) > 7 else 400
        N = int(sys.argv[8]) if len(sys.argv) > 8 else 50
        s0 = int(sys.argv[9]) if len(sys.argv) > 9 else 1
        res = sweep(arm, inst, param, nsim, T, N, s0)
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
        print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
