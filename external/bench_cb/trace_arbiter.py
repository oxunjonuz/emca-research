#!/usr/bin/env python3
"""trace_arbiter.py -- turn 132. What does the arbiter actually see?

Before choosing a repair, measure the objects the rule compares. For every
decision point on mask (base .5) and maskr (base .8), record:
    rich_rate (the agent's own observed pooled alternative payoff)
    the top candidate's score and the candidate scores
    value = GAIN_UNIT * score
    rhs_old = rich*H + c ,  rhs_new = rich*PROBE_LEN + c
and the headroom bound 1 - rich.

Also record, per decision, whether the agent is in the band where the two rules
differ. No producer is imported for the ANALYSIS; the agent modules are imported
only to reproduce the run (that is the object being diagnosed).
"""
import sys, os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "ext", "latt_py3"))
sys.path.insert(0, HERE); sys.path.insert(0, CAMPAIGN)

import arbitration as AR
import arbitration_scaled as AS
import union_agent as UA
from union_run import build_model

T = 400
NSIM = 100


def trace(inst, param, kind="union"):
    rows = []
    for s in range(NSIM):
        model = build_model(inst, param)
        ag = UA.make_agent(kind, s + 1)
        real = AR.plan

        def spy(cands, rich, beta=1.0, **kw):
            p = real(cands, rich, beta=beta, **kw)
            scores = [c.score for c in cands]
            rows.append({
                "rich": rich,
                "n_cands": len(cands),
                "top_score": max(scores) if scores else 0.0,
                "top_value": AS.GAIN_UNIT * (max(scores) if scores else 0.0),
                "rhs_old": rich * AS.H_DEFAULT + AS.PROBE_COST_DEFAULT,
                "rhs_new": rich * AS.PROBE_LEN + AS.PROBE_COST_DEFAULT,
                "cleared_old": len(p.probe_order),
                "headroom": 1.0 - rich,
            })
            return p
        AR.plan = spy
        try:
            ag.run(T, model)
        finally:
            AR.plan = real
    return rows


def summarize(rows, label):
    n = len(rows)
    rich = np.array([r["rich"] for r in rows])
    ts = np.array([r["top_score"] for r in rows])
    tv = np.array([r["top_value"] for r in rows])
    ro = np.array([r["rhs_old"] for r in rows])
    rn = np.array([r["rhs_new"] for r in rows])
    co = np.array([r["cleared_old"] for r in rows])
    band = (rich > AS.cutoff_old()) & (rich <= AS.cutoff_new())
    print(f"=== {label}: {n} decision points ===")
    print(f"  rich_rate      mean {rich.mean():.4f}  min {rich.min():.4f} max {rich.max():.4f}")
    print(f"  top candidate score  mean {ts.mean():.4f}  max {ts.max():.4f}")
    print(f"  top value      mean {tv.mean():.2f}  max {tv.max():.2f}")
    print(f"  rhs_old        mean {ro.mean():.2f}   rhs_new mean {rn.mean():.2f}")
    print(f"  headroom 1-rich mean {(1-rich).mean():.4f}")
    print(f"  cleared>0 (old rule): {int((co>0).sum())}/{n} = {100*(co>0).mean():.2f}%")
    print(f"  would clear (new rule): {int((tv>rn).sum())}/{n} = {100*(tv>rn).mean():.2f}%")
    print(f"  decisions in the disagreement band ({AS.cutoff_old():.4f},{AS.cutoff_new():.4f}]: {int(band.sum())}")
    print(f"  of those, old clears {int(((tv>ro)&band).sum())}, new clears {int(((tv>rn)&band).sum())}")
    return {"n": n, "rich_mean": float(rich.mean()), "rich_max": float(rich.max()),
            "top_score_mean": float(ts.mean()), "top_score_max": float(ts.max()),
            "top_value_max": float(tv.max()),
            "rhs_old_mean": float(ro.mean()), "rhs_new_mean": float(rn.mean()),
            "frac_cleared_old": float((co > 0).mean()),
            "frac_would_clear_new": float((tv > rn).mean()),
            "n_in_band": int(band.sum())}


def main():
    out = {}
    for inst, param, base in [("mask", 0.35, 0.5), ("maskr", 0.35, 0.8)]:
        rows = trace(inst, param)
        out[f"{inst}_base{base}"] = summarize(rows, f"{inst} (base {base})")
        json.dump(rows[:2000], open(os.path.join(HERE, f"trace_{inst}.json"), "w"), indent=1)
    json.dump(out, open(os.path.join(HERE, "trace_arbiter_summary.json"), "w"), indent=1)
    print("\nwrote trace_arbiter_summary.json + trace_mask.json + trace_maskr.json")


if __name__ == "__main__":
    main()
