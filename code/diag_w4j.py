"""diag_w4j.py -- test the PHASE-ATTRIBUTION leak hypothesis for seed 8.

The probe marker records the PRE-move phase (`f["phase"]` from the view
BEFORE the step), but the world runs the glow coin from the position AFTER
the move and the phase AFTER the clock advances. At a warm->cold boundary
the two disagree: the step is SCORED as warm while the world never drew the
glow coin. Measured earlier: 129 of 1200 scored steps consumed only ONE
world draw instead of two.

If those boundary steps fall asymmetrically on the two arms, the warm
stratum is contaminated with guaranteed-glow=False samples -> a biased
comparison. This script:

  1. logs, for the real agent at seed 8, (cand, arm, pre_phase, post_phase,
     draws, glow) for every scored step;
  2. counts boundary steps (pre warm, post cold) per arm;
  3. re-derives the verdict from a CORRECTED log keyed by POST-phase;
  4. repeats for seeds 0..19, reporting how many glow FPs survive.
"""
import collections
import json
import math

from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full

STEPS = 16000


def fisher_greater(a_yes, a_no, c_yes, c_no):
    n = a_yes + a_no + c_yes + c_no
    if n == 0:
        return 1.0
    r1, c1 = a_yes + a_no, a_yes + c_yes
    hi = min(r1, c1)
    p = 0.0
    denom = math.comb(n, c1)
    for x in range(a_yes, hi + 1):
        p += math.comb(r1, x) * math.comb(n - r1, c1 - x) / denom
    return min(1.0, p)


def collect(seed):
    """Return the list of scored-step records with the world's OWN phase."""
    ea = pick_edge_action(seed)
    ag = AgentV7Full(seed)
    env = TerrariumV7(seed, truth=True, decoy=True, rich="low",
                      edge_action=ea)
    recs = []
    for t in range(STEPS):
        o = env.obs()
        pre_phase = env.phase
        a = ag.act(o)
        mark = getattr(ag, "_probe_mark", None)
        cand = ((ag.probe_state["cand"].action,
                 ag.probe_state["cand"].effect) if ag.probe_state else None)
        o2, r, done, info = env.step(a)
        if mark is not None:
            recs.append({"cand": cand, "arm": mark[0], "act": mark[1],
                         "pre_phase": mark[2], "world_phase": env.phase,
                         "turned": pre_phase != env.phase,
                         "glow": bool(info.get("glow"))})
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=True, decoy=True,
                              rich="low", edge_action=ea)
    return ag, recs


def verdict_from(recs, key_filter, phase_field):
    """Rebuild the (target, ctrl) warm tally for the given candidate and
    derive (verdict, p, rr, ty, tn, cy, cn)."""
    log = {"target": collections.defaultdict(lambda: [0, 0]),
           "ctrl": collections.defaultdict(lambda: [0, 0])}
    for r in recs:
        if r["cand"] != key_filter:
            continue
        ph = r[phase_field]
        if ph != "warm":
            continue
        arm = r["arm"]
        log[arm][ph][0 if r["glow"] else 1] += 1
    ty, tn = log["target"]["warm"]
    cy, cn = log["ctrl"]["warm"]
    if (ty + tn) == 0 or (cy + cn) == 0:
        return ("UNRESOLVED", 1.0, 0.0, ty, tn, cy, cn)
    p = fisher_greater(ty, tn, cy, cn)
    ra = ty / (ty + tn)
    rc = cy / (cy + cn)
    rr = (ra / rc) if rc > 0 else float("inf")
    if p < 0.05 and rr >= 1.3:
        v = "CAUSAL"
    elif p < 0.05 and rr < 1.3:
        v = "REJECT"
    elif p >= 0.05 and rr < 1.3:
        v = "REJECT"
    else:
        v = "UNRESOLVED"
    return (v, p, rr, ty, tn, cy, cn)


print("=== seed 8, the failing case, in detail ===")
ag, recs = collect(8)
key = ("wait", "glow")
mine = [r for r in recs if r["cand"] == key]
print(f"scored steps for {key}: {len(mine)}")
print("  by (arm, pre_phase, world_phase):",
      dict(collections.Counter((r["arm"], r["pre_phase"], r["world_phase"])
                               for r in mine)))
print("  boundary steps (pre != world):",
      dict(collections.Counter((r["arm"], r["turned"]) for r in mine)))
print("  glow among boundary steps:",
      dict(collections.Counter((r["arm"], r["glow"]) for r in mine
                               if r["turned"])))
print("  pre-phase keying :", verdict_from(recs, key, "pre_phase"))
print("  world-phase keying:", verdict_from(recs, key, "world_phase"))

print("\n=== all 40 seeds: FP counts under both keyings ===")
tot_pre = tot_world = 0
detail = []
for seed in range(20):
    ag, recs = collect(seed)
    for k in sorted({r["cand"] for r in recs}):
        if k[1] != "glow":
            continue
        vp = verdict_from(recs, k, "pre_phase")
        vw = verdict_from(recs, k, "world_phase")
        if vp[0] == "CAUSAL":
            tot_pre += 1
        if vw[0] == "CAUSAL":
            tot_world += 1
        if vp[0] == "CAUSAL" or vw[0] == "CAUSAL":
            detail.append((seed, k, "pre:" + vp[0], round(vp[1], 5),
                           round(vp[2], 3), "world:" + vw[0],
                           round(vw[1], 5), round(vw[2], 3)))
print(f"glow CAUSALs, pre-phase keying : {tot_pre} / 20 seeds")
print(f"glow CAUSALs, world-phase keying: {tot_world} / 20 seeds")
for d in detail:
    print("   ", d)
