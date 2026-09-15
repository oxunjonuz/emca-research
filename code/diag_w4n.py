"""diag_w4n.py -- decide the pre-matrix amendment A7: raise the probe's
EVIDENCE BUDGET (PROBE_MAX_BLOCKS), thresholds untouched.

Evidence gathered (diag_w4b..m):
  * seed 8 (wait,glow) CAUSAL: target warm 114/200 vs ctrl 80/199, plain
    two-proportion Fisher p=0.00055, RR=1.418 -- reproduces in truth=off
    (so it is not about the cause) and is deterministic.
  * NOT a code leak: the arms consume DISJOINT world-RNG draws; a scored
    warm step consumes exactly 2 draws both arms; a scripted replica of the
    identical protocol is calibrated (mean gap +0.0003, sd 0.0472 vs
    binomial 0.0500, 0/160 windows past the bar); decorrelating the glow
    coin removes it; pre-move vs world phase keying is identical.
  * It is a TAIL: the scripted replica at the SAME seed shows no gap, so the
    excess lives in the particular stream indices the agent happened to
    consume -- and it DILUTES with more evidence (80 -> 1 FP, 160 -> 0,
    320 -> 0), while true-edge detection is unchanged (9/10).

A7 raises the evidence budget only (a shared harness constant, applied to
every arm); the verdict thresholds (p<0.05, RR>=1.3) are NOT touched. This
script confirms, over 20 seeds, that A7 removes the FP and preserves the
true-edge detection and the C1 legs.
"""
import collections

import agent_emca_v7 as A
from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full, AgentV7Beta0, AgentV7Perm

STEPS = 16000
SEEDS = range(20)


def run(cls, seed, truth=True, rich="low"):
    ea = pick_edge_action(seed)
    ag = cls(seed)
    env = TerrariumV7(seed, truth=truth, decoy=True, rich=rich,
                      edge_action=ea)
    rew = 0.0
    for t in range(STEPS):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        rew += r
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=True,
                              rich=rich, edge_action=ea)
    return ag, rew


for blocks in (80, 160, 320):
    A.PROBE_MAX_BLOCKS = blocks
    fp = []
    tp = 0
    fn = []
    for seed in SEEDS:
        ag, _ = run(AgentV7Full, seed)
        ea = pick_edge_action(seed)
        for (a, e), v in ag.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp.append((seed, a, v["p"], v["rr"]))
        v = ag.verdicts.get((ea, "hum"))
        if v and v["verdict"] == "CAUSAL":
            tp += 1
        else:
            fn.append(seed)
    # null regime FP
    fp_off = []
    for seed in SEEDS:
        ag, _ = run(AgentV7Full, seed, truth=False)
        for (a, e), v in ag.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_off.append((seed, a, v["p"], v["rr"]))
    # C1 legs at this budget
    b0 = sum(run(AgentV7Beta0, s)[0].probe_trials for s in SEEDS)
    perm_ok = perm_n = 0
    for s in SEEDS:
        agp, _ = run(AgentV7Perm, s)
        if agp.first_probe and agp.ranked_at_first_probe:
            perm_n += 1
            rk = sorted(agp.ranked_at_first_probe,
                        key=lambda c: (-c[2], -c[3], c[0], c[1]))
            if agp.first_probe[:2] == (rk[0][0], rk[0][1]):
                perm_ok += 1
    lo = [run(AgentV7Full, s, rich="low")[0].probe_trials for s in SEEDS]
    hi = [run(AgentV7Full, s, rich="high")[0].probe_trials for s in SEEDS]
    print(f"\n=== PROBE_MAX_BLOCKS={blocks} ===")
    print(f"  truth=on : glow FP={len(fp)} {fp}")
    print(f"             true-edge TP={tp}/20  misses={fn}")
    print(f"  truth=off: glow FP={len(fp_off)} {fp_off}")
    print(f"  C1: beta0 probe_trials={b0} ; perm follows {perm_ok}/{perm_n}")
    print(f"  C1-iii: probes low mean={sum(lo)/20:.0f} high mean={sum(hi)/20:.0f}"
          f" ; high<low? {sum(hi) < sum(lo)} ; high>0? {sum(hi) > 0}")