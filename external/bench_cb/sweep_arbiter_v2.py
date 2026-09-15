#!/usr/bin/env python3
"""sweep_arbiter_v2.py -- turn 132. The base sweep, run for the FIXED arbiter
and the FROZEN one SIDE BY SIDE on identical instances.

Why side by side: the owner's instruction is to check whether the effect
DISAPPEARED or merely SHIFTED. A before/after on the same bases answers that
directly; a number for the fixed rule alone cannot.

Arms:
  union_old    -- frozen rule   (union_agent,    imports arbitration)        [old]
  union_new    -- corrected     (union_agent_v2, imports arbitration_scaled) [new]
  union_nocost -- no price at all (probe the top candidate) -- the 2-part union
  beta0_new    -- the C1 control under the corrected rule: must never probe

Instances: base swept .50 -> .95 by .05, eps=0.35, N=50, T=400, 200 sims/cell.
Every run re-executes the measured module's OWN rule; the spy prints nothing and
only tallies whether at least one candidate cleared.

The cutoffs are COMPUTED from the module, never typed here:
  old: (GU - c)/(GU + H)          = 0.816667
  new: (GU - c)/(GU + PROBE_LEN)  = 0.890909
Kept honest by an assert that PROBE_LEN is union_agent_v2.PROBE_BLOCK itself.
"""
import sys, os, json, time
import numpy as np
# NOTE (turn 132): this sweep runs SERIALLY and deliberately does NOT use
# multiprocessing.Pool. A Pool spawns many processes at once, and the runtime's
# trace layer writes one /data/owner_trace/*.json.gz per spawn; at >=5 spawns
# the runtime raises a WRITESET ALERT and kills the process group. That is a
# runtime-layer write my scripts do not cause (they write only under bench_cb/),
# surfaced here rather than swallowed. One run is ~0.03 s, so serial is cheap.

HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "ext", "latt_py3"))
sys.path.insert(0, HERE); sys.path.insert(0, CAMPAIGN)

import arbitration as AR
import arbitration_scaled as AS
import union_agent as U1
import union_agent_v2 as U2
from union_instance import MaskedParallel

assert AS.PROBE_LEN == U2.PROBE_BLOCK, (
    "PROBE_LEN must BE the declared probe block, not a new knob: %r vs %r"
    % (AS.PROBE_LEN, U2.PROBE_BLOCK))

T = 400
NSIM = 200
BASES = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
GRID = [("union_old", "union", "old"), ("union_new", "union", "new"),
        ("union_nocost", "union_nocost", "new"),
        ("beta0_new", "beta0", "new")]


def _one(job):
    """One simulation. The spy is installed inside the worker process only."""
    base, tag, kind, which, seed = job
    mod = U1 if which == "old" else U2
    rule = mod.AR.plan
    calls = []

    def spy(cands, rich, beta=1.0, **kw):
        p = rule(cands, rich, beta=beta)
        calls.append(len(p.probe_order))
        return p
    mod.AR.plan = spy
    try:
        np.random.seed(seed)
        model = MaskedParallel(N=50, m=1, eps=0.35, base=base)
        ag = mod.make_agent(kind, seed)
        reg = ag.run(T, model)
        probes, n_explore = ag.n_probes, ag.n_explore_picks
    finally:
        mod.AR.plan = rule
    return (base, tag, seed,
            {"regret": float(reg), "probes": float(probes),
             "explore": float(n_explore),
             "clear": (float(np.mean([1 if c > 0 else 0 for c in calls]))
                       if calls else None)})


def main():
    # usage: sweep_arbiter_v2.py [nsim] [bases_csv] [out_json]
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else NSIM
    bases = ([float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2
             else BASES)
    out_json = sys.argv[3] if len(sys.argv) > 3 else "sweep_arbiter_v2.json"
    jobs = [(base, tag, kind, which, i + 1)
            for base in bases for tag, kind, which in GRID for i in range(nsim)]
    print(f"{len(jobs)} runs, serial, bases={bases}", flush=True)
    t0 = time.time()
    acc = {}
    for i, job in enumerate(jobs):
        base, tag, seed, d = _one(job)
        acc.setdefault((base, tag), []).append(d)
        if (i + 1) % 1000 == 0:
            print(f"  [{i+1}/{len(jobs)}] {time.time()-t0:.0f}s", flush=True)

    rows = []
    print("\n" + f"{'base':>5} | {'OLD regret':>10} {'sem':>7} {'probes':>7} {'clear%':>7} | "
          f"{'NEW regret':>10} {'sem':>7} {'probes':>7} {'clear%':>7} | "
          f"{'nocost r':>9} {'probes':>7} | {'beta0 probes':>12}")
    for base in bases:
        row = {"base": base, "nsim": nsim, "T": T}
        for tag in ("union_old", "union_new", "union_nocost", "beta0_new"):
            ds = acc[(base, tag)]
            regs = np.array([d["regret"] for d in ds])
            cl = [d["clear"] for d in ds if d["clear"] is not None]
            row[tag + "_regret"] = float(regs.mean())
            row[tag + "_sem"] = float(regs.std(ddof=1) / np.sqrt(len(regs)))
            row[tag + "_probes"] = float(np.mean([d["probes"] for d in ds]))
            row[tag + "_explore"] = float(np.mean([d["explore"] for d in ds]))
            row[tag + "_clear_frac"] = (float(np.mean(cl)) if cl else None)
        row["new_minus_old"] = row["union_new_regret"] - row["union_old_regret"]
        rows.append(row)
        print(f"{base:>5.2f} | {row['union_old_regret']:>10.5f} {row['union_old_sem']:>7.5f} "
              f"{row['union_old_probes']:>7.3f} {(row['union_old_clear_frac'] if row['union_old_clear_frac'] is not None else -1):>7.4f} | "
              f"{row['union_new_regret']:>10.5f} {row['union_new_sem']:>7.5f} "
              f"{row['union_new_probes']:>7.3f} {(row['union_new_clear_frac'] if row['union_new_clear_frac'] is not None else -1):>7.4f} | "
              f"{row['union_nocost_regret']:>9.5f} {row['union_nocost_probes']:>7.3f} | "
              f"{row['beta0_new_probes']:>12.3f}")
    json.dump(rows, open(os.path.join(HERE, out_json), "w"), indent=1)
    print(f"\nwrote {out_json}  ({time.time()-t0:.0f}s total)")
    print(f"cutoffs: old={AS.cutoff_old():.6f}  new={AS.cutoff_new():.6f}"
          f"  (GU={AS.GAIN_UNIT} PROBE_LEN={AS.PROBE_LEN} "
          f"PROBE_COST={AS.PROBE_COST_DEFAULT} H={AS.H_DEFAULT})")


if __name__ == "__main__":
    main()
