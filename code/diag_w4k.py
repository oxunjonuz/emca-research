"""diag_w4k.py -- does seed 8's decoy excess DILUTE with more evidence?

Established (diag_w4b..j): the seed-8 (wait,glow) CAUSAL (target warm
114/200 vs ctrl 80/199, p=0.00055) is not a code leak -- the two arms use
disjoint world-RNG draws, the scripted replica of the same protocol is
calibrated (mean gap +0.0003, sd 0.0472 vs binomial 0.0500, 0/160 windows
past the bar), and decorrelating the glow coin removes it.

So it is a TAIL of an honest test. A tail event is a property of the SAMPLE
SIZE as well as the luck: if the probe simply collects more steps, an
honest fluctuation at one window has to persist to survive. This measures
the verdict as PROBE_MAX_BLOCKS grows (80 -> 160 -> 320), thresholds
UNCHANGED (p<0.05, RR>=1.3), over the truth regime (FP on glow + detection
of the true edge) and over the null regime (truth=off, FP on glow).
"""
import collections

import agent_emca_v7 as A
from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full

STEPS = 22000


def run(seed, truth, blocks, maxt):
    A.PROBE_MAX_BLOCKS = blocks
    ea = pick_edge_action(seed)
    ag = AgentV7Full(seed)
    env = TerrariumV7(seed, truth=truth, decoy=True, rich="low",
                      edge_action=ea)
    for t in range(maxt):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=True,
                              rich="low", edge_action=ea)
    return ea, ag


for blocks, maxt in ((80, 16000), (160, 22000), (320, 30000)):
    print(f"\n########## PROBE_MAX_BLOCKS={blocks} "
          f"(~{blocks*5} steps/arm)  steps={maxt} ##########")
    for truth in (True, False):
        tag = "TRUTH on " if truth else "NULL  off"
        fp = []
        tp = 0
        fn = []
        for seed in range(10):
            ea, ag = run(seed, truth, blocks, maxt)
            for (a, e), v in ag.verdicts.items():
                if e == "glow" and v["verdict"] == "CAUSAL":
                    fp.append((seed, a, v["p"], v["rr"]))
            if truth:
                v = ag.verdicts.get((ea, "hum"))
                if v and v["verdict"] == "CAUSAL":
                    tp += 1
                else:
                    fn.append((seed, v["verdict"] if v else "NONE"))
        print(f"  {tag}: glow FP={len(fp)} {fp} ; true-edge {tp}/10 ; "
              f"misses={fn}")
