"""diag_w4q.py -- two decisions before the matrix, both on measurement:

(1) A7: the smallest evidence budget (PROBE_MAX_BLOCKS) that makes W4
    (FP=0) hold REPRODUCIBLY over 40 seeds, at the frozen thresholds.
(2) Is C1-iii achievable at all with the FROZEN arbiter? Dump the actual
    candidate scores, the arbiter's rhs in both rich regimes, and how many
    candidates clear -- BEFORE choosing any metric.
"""
import collections

import agent_emca_v7 as A
from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full
import arbitration

STEPS = 16000
NSEED = 40


def run(seed, truth=True, rich="low"):
    ea = pick_edge_action(seed)
    ag = AgentV7Full(seed)
    env = TerrariumV7(seed, truth=truth, decoy=True, rich=rich,
                      edge_action=ea)
    for t in range(STEPS):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=True,
                              rich=rich, edge_action=ea)
    return ag


print("=== (1) FP sweep over 40 seeds, frozen thresholds ===")
for blocks in (80, 120, 160, 240):
    A.PROBE_MAX_BLOCKS = blocks
    fp_on, fp_off = [], []
    tp = 0
    for seed in range(NSEED):
        ag = run(seed, truth=True)
        ea = pick_edge_action(seed)
        for (a, e), v in ag.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_on.append((seed, a, v["p"], v["rr"]))
        v = ag.verdicts.get((ea, "hum"))
        tp += 1 if (v and v["verdict"] == "CAUSAL") else 0
        ago = run(seed, truth=False)
        for (a, e), v in ago.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_off.append((seed, a, v["p"], v["rr"]))
    print(f"  blocks={blocks:3d}: FP_on={len(fp_on)} {fp_on}")
    print(f"               FP_off={len(fp_off)} {fp_off} ; true-edge TP={tp}/{NSEED}")

print("\n=== (2) the arbiter's actual decision margins ===")
A.PROBE_MAX_BLOCKS = 160
for rich in ("low", "high"):
    rhs = 0.05 * arbitration.H_DEFAULT + arbitration.PROBE_COST_DEFAULT \
        if rich == "low" else 0.60 * arbitration.H_DEFAULT + \
        arbitration.PROBE_COST_DEFAULT
    print(f"\n  rich={rich}: rich_rate={0.05 if rich=='low' else 0.60} "
          f"rhs={rhs} (GAIN_UNIT={arbitration.GAIN_UNIT})")
    cnt = collections.Counter()
    for seed in range(10):
        ag = run(seed, rich=rich)
        scores = [(c[0], c[1], round(c[2], 4)) for c in ag.candidates_seen]
        values = [round(arbitration.GAIN_UNIT * c[2], 2)
                  for c in ag.candidates_seen]
        cleared = [(c[0], c[1]) for c in ag.candidates_seen
                   if arbitration.GAIN_UNIT * c[2] > rhs]
        print(f"   seed {seed}: scores={scores} values={values} "
              f"cleared={len(cleared)}")
        cnt[len(cleared)] += 1
    print(f"   cleared-count distribution: {dict(cnt)}")
