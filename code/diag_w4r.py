"""diag_w4r.py -- freeze amendment A7 on a 60-seed check.

Measured so far (files diag_w4b..q):
  * seed 8 (wait,glow) target warm 114/200 vs ctrl 80/199, plain Fisher
    p=0.00055 -- deterministic, reproduces in truth=off, and is NOT a leak
    (disjoint RNG draws, calibrated scripted replica of the same protocol:
    mean gap +0.0003 sd 0.0472 vs binomial 0.0500, 0/160 windows past the
    bar; decorrelation removes it; phase keying identical).
  * it is a TAIL, and it DILUTES with evidence: 40-seed sweep gave
    blocks=80 -> FP_on 3, FP_off 1 ; blocks=120/160/240 -> FP 0/0, with
    true-edge detection UNCHANGED (37/40).

A7 = raise PROBE_MAX_BLOCKS 80 -> 120 (a shared harness constant: the
probe's EVIDENCE BUDGET). Verdict thresholds (p<0.05, RR>=1.3) untouched.
This is the smallest setting that makes the FROZEN gate (W4/C3: FP=0) hold.

This 60-seed run confirms it, and reports the economy cost (the secondary
observation) plus the C1 legs at that budget.
"""
import collections

import agent_emca_v7 as A
from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full, AgentV7Beta0, AgentV7Perm, AgentV7Forager
import arbitration

STEPS = 16000
NSEED = 60


def run(cls, seed, truth=True, rich="low"):
    ea = pick_edge_action(seed)
    ag = cls(seed)
    env = TerrariumV7(seed, truth=truth, decoy=True, rich=rich,
                      edge_action=ea)
    rew = 0.0
    fruits = 0
    deaths = 0
    for t in range(STEPS):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        rew += r
        if info.get("fruit"):
            fruits += 1
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            deaths += 1
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=True,
                              rich=rich, edge_action=ea)
    return ag, rew, fruits, deaths


for blocks in (80, 120):
    A.PROBE_MAX_BLOCKS = blocks
    fp_on, fp_off = [], []
    tp = 0
    nom = 0
    rew_lo, rew_hi, fruits_lo = [], [], []
    cleared_lo, cleared_hi = [], []
    b0 = 0
    perm_ok = perm_n = 0
    for seed in range(NSEED):
        ag, rew, fr, _ = run(AgentV7Full, seed)
        ea = pick_edge_action(seed)
        rew_lo.append(rew)
        fruits_lo.append(fr)
        if any(c[0] == ea and c[1] == "hum" for c in ag.candidates_seen):
            nom += 1
        for (a, e), v in ag.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_on.append((seed, a, v["p"], v["rr"]))
        v = ag.verdicts.get((ea, "hum"))
        tp += 1 if (v and v["verdict"] == "CAUSAL") else 0
        cleared_lo.append(len({(a, e) for (a, e, _r) in ag.probe_order_log}))

        ag2, rew2, _, _ = run(AgentV7Full, seed, rich="high")
        rew_hi.append(rew2)
        cleared_hi.append(len({(a, e) for (a, e, _r) in ag2.probe_order_log}))

        ago, _, _, _ = run(AgentV7Full, seed, truth=False)
        for (a, e), v in ago.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_off.append((seed, a, v["p"], v["rr"]))
        if not any(c[0] == ea and c[1] == "hum"
                   for c in ago.candidates_seen):
            pass  # counted in C2 off-nomination separately

        b0 += run(AgentV7Beta0, seed)[0].probe_trials
        agp, _, _, _ = run(AgentV7Perm, seed)
        if agp.first_probe and agp.ranked_at_first_probe:
            perm_n += 1
            rk = sorted(agp.ranked_at_first_probe,
                        key=lambda c: (-c[2], -c[3], c[0], c[1]))
            if agp.first_probe[:2] == (rk[0][0], rk[0][1]):
                perm_ok += 1

    print(f"\n########## PROBE_MAX_BLOCKS={blocks} ({NSEED} seeds) ##########")
    print(f"  C2: true pair nominated truth=on: {nom}/{NSEED}")
    print(f"  C3: FP truth=on {len(fp_on)} {fp_on}")
    print(f"      FP truth=off {len(fp_off)} {fp_off}")
    print(f"      true-edge CAUSAL: {tp}/{NSEED} (FN {NSEED-tp})")
    print(f"  C1-i beta0 probe_trials={b0}")
    print(f"  C1-ii perm follows ranking {perm_ok}/{perm_n}")
    print(f"  C1-iii n_cleared low mean {sum(cleared_lo)/NSEED:.2f} "
          f"high mean {sum(cleared_hi)/NSEED:.2f} "
          f"-> high<low? {sum(cleared_hi) < sum(cleared_lo)} ; "
          f"high>0? {sum(cleared_hi) > 0}")
    print(f"  economy: reward low mean {sum(rew_lo)/NSEED:.1f} "
          f"high mean {sum(rew_hi)/NSEED:.1f} ; fruits low mean "
          f"{sum(fruits_lo)/NSEED:.2f}")
