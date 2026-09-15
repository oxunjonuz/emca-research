"""cb_isolate_run.py -- turn 128: freeze the C1-isolation and control numbers.

  python3 cb_isolate_run.py <what> <out.json>

what:
  isolate_pub   -- published instance, modes none/inject_true/inject_forced
  isolate_grey  -- supplementary 2-parent instance, modes none/inject_true
  controls_pub  -- published instance, greedy_half / rnd_probe / obs_only / know_probe
  beta_sweep    -- supplementary instance, arbiter beta swept
  horizon_grey  -- supplementary instance, observational half lengthened
"""
import sys, os, json
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import models as M
from cb_c1_isolate import C1Iso
from cb_controls import CBFixed
from cb_grey import make_grey
from cb_agent import CBAgent
import candidate_gen as CG


def summarise(rows):
    return {"n": len(rows),
            "mean_regret": float(np.mean([r["regret"] for r in rows])),
            "sem_regret": float(np.std([r["regret"] for r in rows], ddof=1) /
                                np.sqrt(len(rows))),
            "frac_optimal": float(np.mean([r["chosen_is_optimal"] for r in rows])),
            "mean_probes": float(np.mean([r["probes"] for r in rows])),
            "mean_opt_trials": float(np.mean([r["opt_trials"] for r in rows])),
            "rows": rows}


def rec(a):
    return {"regret": float(a.regret), "probes": len(a.probes),
            "opt_trials": int(a.tab["a%d" % a.optimal_arm]["y1"][1]),
            "chosen_is_optimal": int(a.chosen_is_optimal)}


def main():
    what, out = sys.argv[1], sys.argv[2]
    NS = 300
    res = {"what": what, "nsim": NS}

    if what == "isolate_pub":
        res["cells"] = {}
        for m in [2, 8, 25, 49]:
            for mode in ["none", "inject_true", "inject_forced"]:
                rows = []
                for i in range(NS):
                    np.random.seed(1 + i)
                    model = M.Parallel.create(50, m, 0.3)
                    a = C1Iso(mode, seed=1 + i, target="a50")
                    a.run(400, model)
                    rows.append(rec(a))
                res["cells"]["%s_m%d" % (mode, m)] = summarise(rows)

    elif what == "isolate_grey":
        res["cells"] = {}
        for mode in ["none", "inject_true"]:
            rows = []
            for i in range(NS):
                np.random.seed(1 + i)
                model = make_grey()
                a = C1Iso(mode, seed=1 + i, target="a2")
                a.run(400, model)
                rows.append(rec(a))
            res["cells"][mode] = summarise(rows)

    elif what == "controls_pub":
        res["cells"] = {}
        for m in [2, 8, 25, 49]:
            for pol in ["greedy_half", "rnd_probe", "obs_only", "know_probe"]:
                rows = []
                for i in range(NS):
                    np.random.seed(1 + i)
                    model = M.Parallel.create(50, m, 0.3)
                    a = CBFixed(pol, seed=1 + i)
                    a.run(400, model)
                    rows.append(rec(a))
                res["cells"]["%s_m%d" % (pol, m)] = summarise(rows)

    elif what == "beta_sweep":
        res["cells"] = {}
        for beta in [0.0, 1.0, 5.0, 10.0, 20.0, 50.0]:
            rows = []
            for i in range(NS):
                np.random.seed(1 + i)
                model = make_grey()
                a = CBAgent(kind="pure", seed=1 + i, beta=beta)
                a.run(400, model)
                rows.append(rec(a))
            res["cells"]["beta_%s" % beta] = summarise(rows)

    elif what == "horizon_grey":
        res["cells"] = {}
        acts = ["a0", "a1", "a2", "a3"]
        for T in [400, 1000, 2000, 4000, 8000]:
            rows = []
            for i in range(100):
                np.random.seed(1 + i)
                model = make_grey()
                a = CBAgent(kind="pure", seed=1 + i)
                for _ in range(T // 2):
                    a._observe(model, model.K - 1)
                cands = CG.generate_flat(a._flat_table(), acts)
                a.run(T, model)
                r = rec(a)
                r["n_cands_after_half"] = len(cands)
                rows.append(r)
            s = summarise(rows)
            s["frac_no_candidate"] = float(np.mean(
                [1.0 if r["n_cands_after_half"] == 0 else 0.0 for r in rows]))
            res["cells"]["T_%d" % T] = s
    else:
        raise SystemExit("unknown: " + what)

    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: (v if k != "cells" else
                          {kk: {x: vv for x, vv in vv.items() if x != "rows"}
                           for kk, vv in v.items()}) for k, v in res.items()},
                     indent=1))


if __name__ == "__main__":
    main()
