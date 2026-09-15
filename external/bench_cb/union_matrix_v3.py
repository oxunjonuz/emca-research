"""union_matrix_v3.py -- turn 134. The STOPPING-RULE matrix.

ONE thing varies between arms: the stopping rule. The instance builder, the
candidate generator and the agent body are frozen (build_model imported from
union_run_v2; candidate_gen byte-identical; union_agent_v3 generated from
union_agent_v2 by four mechanical substitutions, see union_agent_v3.diff).

Cells (declared in PREREG_STOPPING.md §4):
  mask   eps in {0.15, 0.25, 0.35}                 -- context-specific instance
  maskr  eps in {0.25, 0.35}   (base 0.8)          -- rich alternative
  richness family: mask@base, eps=0.35, base in
      {0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95}   -- G2's sweep
  pub    m in {2, 8, 16, 49}                       -- the published instance

Arms: frozen_rule (control = the old rule), voi (T2), voi_rate (T2b),
      conf (T3), conf_noexp / voi_rate_noexp (exploration off),
      union_nocost (no price at all), union_noexp (old rule, no exploration),
      pure / beta0 (controls).

Writes into results_stopping/ : one JSON per cell, plus SUMMARY.json.
Runs SERIALLY: a multiprocessing.Pool makes the runtime's trace layer write one
/data/owner_trace/*.json.gz per spawn and at >= 5 spawns the runtime raises a
WRITESET ALERT and kills the group (observed on turns 131/132). Serial costs
~0.03 s per run.

  python3 union_matrix_v3.py <nsim> [group] [nosummary]
"""
import json
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)

OUT = os.environ.get("STOPPING_OUT") or os.path.join(_HERE, "results_stopping")
ARMS = ["frozen_rule", "voi", "voi_rate", "conf", "conf_noexp",
        "voi_rate_noexp", "union_nocost", "union_noexp", "pure", "beta0"]
LEAN = ["frozen_rule", "voi", "voi_rate", "conf", "union_nocost"]
MASK_EPS = [0.15, 0.25, 0.35]
MASKR_EPS = [0.25, 0.35]
RICH_BASES = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
PUB_M = [2, 8, 16, 49]
T_DEFAULT = 400


def fname(inst, param, arm, tag=""):
    return os.path.join(OUT, "%s%s_p%s_%s.json"
                        % (inst, tag, str(param).replace(".", "p"), arm))


def cell(arm, inst, param, nsim, seed0=1, T=T_DEFAULT, base=None):
    from union_run_v3 import run_cell, build_model
    import union_run_v2
    rows = []
    for i in range(nsim):
        if base is not None:                      # richness family
            import numpy as np2
            np2.random.seed(seed0 + i)
            model = union_run_v2.MaskedParallel(N=50, m=1, eps=float(param),
                                                base=float(base))
            import union_agent_v3
            ag = union_agent_v3.make_agent(arm, seed0 + i)
            r = ag.run(T, model)
            d = ag.diagnostics()
            d["policy"] = dict(getattr(ag, "policy", {}))
            d["rule_name"] = getattr(ag, "rule_name", None)
            row = {"arm": arm, "inst": inst, "param": param, "base": base,
                   "seed": seed0 + i, "T": T, "regret": float(r),
                   "seconds": 0.0, "optimal": float(model.optimal)}
            row.update(d)
            for k, v in list(row.items()):
                if isinstance(v, dict):
                    row[k] = {kk: (int(vv) if hasattr(vv, "item") else vv)
                              for kk, vv in v.items()}
                elif hasattr(v, "item"):
                    row[k] = v.item()
        else:
            row = run_cell(arm, inst, param, seed0 + i, T)
            row["base"] = base
        rows.append(row)

    def m(key):
        return float(np.mean([r.get(key, 0) or 0 for r in rows]))

    regs = [r["regret"] for r in rows]
    out = {"arm": arm, "inst": inst, "param": param, "base": base, "nsim": nsim,
           "seed0": seed0, "T": T, "mean_regret": float(np.mean(regs)),
           "sem_regret": (float(np.std(regs, ddof=1) / np.sqrt(len(regs)))
                          if len(regs) > 1 else 0.0),
           "sd_regret": float(np.std(regs, ddof=1)) if len(regs) > 1 else 0.0,
           "frac_optimal": m("chosen_is_optimal"),
           "mean_probes": m("n_probes"), "mean_explore": m("n_explore_picks"),
           "mean_active": m("active_pulls"), "mean_resolved": m("n_resolved"),
           "rows": rows}
    return out


def jobs(group, arms=None):
    A = arms if arms else ARMS
    J = []
    if group in ("all", "mask"):
        J += [(a, "mask", e, None) for e in MASK_EPS for a in A]
    if group in ("all", "maskr"):
        J += [(a, "maskr", e, None) for e in MASKR_EPS for a in A]
    if group in ("all", "rich"):
        J += [(a, "mask", 0.35, b) for b in RICH_BASES for a in A]
    if group in ("all", "pub"):
        J += [(a, "pub", m, None) for m in PUB_M for a in A]
    return J


def main():
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    group = sys.argv[2] if len(sys.argv) > 2 else "all"
    write_summary = (len(sys.argv) <= 3 or sys.argv[3] != "nosummary")
    arms = None
    if len(sys.argv) > 4 and sys.argv[4] != "all":
        arms = sys.argv[4].split(",")
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    todo = jobs(group, arms)
    print("%d cells x %d sims, serial" % (len(todo), nsim), flush=True)
    t0 = time.time()
    meta = {}
    for i, (arm, inst, param, base) in enumerate(todo):
        tag = "" if base is None else "_b%s" % str(base).replace(".", "p")
        fn = fname(inst, param, arm, tag)
        if os.path.exists(fn):
            print("  skip %s" % os.path.basename(fn), flush=True)
            continue
        res = cell(arm, inst, param, nsim, base=base)
        with open(fn, "w") as f:
            json.dump(res, f, indent=1)
        meta[fn] = {"mean_regret": res["mean_regret"],
                    "mean_probes": res["mean_probes"],
                    "frac_optimal": res["frac_optimal"]}
        if (i + 1) % 10 == 0:
            print("  [%d/%d] %.0fs" % (i + 1, len(todo), time.time() - t0),
                  flush=True)
    if write_summary:
        import hashlib

        def sha(p):
            return hashlib.sha256(open(p, "rb").read()).hexdigest()
        producers = {}
        for f in ("stopping_rules.py", "union_agent_v3.py", "union_run_v3.py",
                  "make_agent_v3.py", "arbitration.py", "arbitration_scaled.py",
                  "union_instance.py", "union_run_v2.py"):
            producers[f] = sha(os.path.join(_HERE, f))
        for f in ("candidate_gen.py", "union_agent_v2.py", "arbitration.py"):
            producers["../" + f] = sha(os.path.join(os.path.dirname(_HERE), f))
        summary = {"n_cells": len(todo), "nsim": nsim, "group": group,
                   "T": T_DEFAULT, "arms": ARMS, "producers": producers,
                   "cells": meta}
        with open(os.path.join(OUT, "SUMMARY.json"), "w") as f:
            json.dump(summary, f, indent=1)
        print("wrote SUMMARY.json (%d cells recorded)" % len(meta))
    print("done in %.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
