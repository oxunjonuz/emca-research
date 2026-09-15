#!/usr/bin/env python3
"""diag_union_cost.py -- turn 131.

WHY does the cost-aware arbiter hurt in the RICH regime?
Frozen data (results_union/maskr_p0p35_*.json):
    union        mean_regret 0.031252   mean_probes 0.018
    union_nocost mean_regret 0.020972   mean_probes 4.396
The two arms differ in ONE switch (use_cost). So the arbiter is rejecting
candidates that the unconditional rule would take. This script replays the SAME
cells and records, at every decision point, the arbiter's own arithmetic:
    rich_rate, rhs = rich_rate*H + PROBE_COST, the candidate scores, the values
    beta*GAIN_UNIT*score, and how many candidates cleared.

No producer is imported for the ANALYSIS; the agent modules are imported only to
reproduce the run itself (that is the thing being diagnosed).
"""
import sys, os, json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "ext", "latt_py3"))
sys.path.insert(0, HERE)
sys.path.insert(0, CAMPAIGN)

import candidate_gen as CG
import arbitration as AR
import union_agent as UA
from union_run import build_model

T = 400
NSIM = 200          # enough to be stable; declared

def trace_one(seed, inst="maskr", param=0.35, kind="union"):
    model = build_model(inst, param)
    ag = UA.make_agent(kind, seed)
    # monkey-patch nothing: re-implement the run loop's decision bookkeeping by
    # wrapping AR.plan so we can see every call.
    calls = []
    real_plan = AR.plan
    def spy_plan(cands, rich, beta=1.0, **kw):
        p = real_plan(cands, rich, beta=beta, **kw)
        calls.append({"rich": rich, "rhs": p.rhs,
                      "n_cands": len(cands),
                      "scores": [round(c.score, 4) for c in cands],
                      "values": list(p.values),
                      "n_cleared": len(p.probe_order)})
        return p
    AR.plan = spy_plan
    try:
        ag.run(T, model)
    finally:
        AR.plan = real_plan
    return ag, calls

def main():
    for kind in ("union", "union_nocost"):
        allcalls = []
        probes = []
        for s in range(NSIM):
            ag, calls = trace_one(s + 1, kind=kind)
            allcalls.extend(calls)
            probes.append(ag.n_probes)
        n = len(allcalls)
        cleared = [c["n_cleared"] for c in allcalls]
        rhs_vals = [c["rhs"] for c in allcalls]
        rich_vals = [c["rich"] for c in allcalls]
        ncands = [c["n_cands"] for c in allcalls]
        # distribution of the TOP candidate's value vs rhs
        top_vals = [max(c["values"]) if c["values"] else None for c in allcalls]
        zero_clear = sum(1 for x in cleared if x == 0)
        print(f"=== {kind} ===")
        print(f"  decision points (AR.plan calls): {n}")
        print(f"  mean n_cands: {sum(ncands)/n:.2f}")
        print(f"  mean rich_rate: {sum(rich_vals)/n:.4f}")
        print(f"  mean rhs: {sum(rhs_vals)/n:.4f}   (min {min(rhs_vals):.4f} max {max(rhs_vals):.4f})")
        print(f"  cleared==0 at {zero_clear}/{n} = {100*zero_clear/n:.1f}% of decisions")
        tv = [v for v in top_vals if v is not None]
        if tv:
            print(f"  top candidate value: mean {sum(tv)/len(tv):.4f}, "
                  f"max {max(tv):.4f}, min {min(tv):.4f}")
            print(f"  top value > rhs at {sum(1 for c in allcalls if c['values'] and max(c['values'])>c['rhs'])}/{n}")
        print(f"  probes per run: mean {sum(probes)/len(probes):.3f}, total {sum(probes)}")
        # histogram of top value buckets
        if tv:
            buckets = Counter()
            for v in tv:
                buckets[round(v, 0)] += 1
            print(f"  top-value buckets (rounded): {dict(sorted(buckets.items()))}")
        # save
        json.dump({"kind": kind, "n_decisions": n, "mean_rhs": sum(rhs_vals)/n,
                   "mean_rich": sum(rich_vals)/n, "zero_clear_frac": zero_clear/n,
                   "mean_probes": sum(probes)/len(probes)},
                  open(os.path.join(HERE, f"diag_cost_{kind}.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
