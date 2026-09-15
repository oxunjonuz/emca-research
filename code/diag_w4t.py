"""diag_w4t.py -- HOLD-OUT validation of A7.

The budget (120) was chosen watching seeds 0..59. That is exactly the
overfitting risk the campaign has been bitten by before, so the choice is
re-checked on seeds 60..159, which took no part in the choice.

Decision rule stated BEFORE looking:
  HOLD  if at blocks=120 the glow FP count is 0 in BOTH truth regimes over
        the held-out seeds AND true-edge detection is not worse than at 80.
  REJECT if the FP persists at a comparable rate (the "fix" was a re-roll).
"""
import agent_emca_v7 as A
from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full

STEPS = 16000
HELD = list(range(60, 160))


def run(seed, truth, rich="low"):
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


for blocks in (80, 120):
    A.PROBE_MAX_BLOCKS = blocks
    fp_on, fp_off = [], []
    tp = fn = 0
    for seed in HELD:
        ag = run(seed, True)
        ea = pick_edge_action(seed)
        for (a, e), v in ag.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_on.append((seed, a, v["p"], v["rr"]))
        v = ag.verdicts.get((ea, "hum"))
        if v and v["verdict"] == "CAUSAL":
            tp += 1
        else:
            fn += 1
        ago = run(seed, False)
        for (a, e), v in ago.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_off.append((seed, a, v["p"], v["rr"]))
    print(f"\n=== HELD-OUT seeds 60..159, PROBE_MAX_BLOCKS={blocks} ===")
    print(f"  FP truth=on : {len(fp_on)}/{len(HELD)} {fp_on[:8]}")
    print(f"  FP truth=off: {len(fp_off)}/{len(HELD)} {fp_off[:8]}")
    print(f"  true-edge: TP={tp}/{len(HELD)} FN={fn}")
    print(f"  FP rate on : {100*len(fp_on)/len(HELD):.1f}%  "
          f"off: {100*len(fp_off)/len(HELD):.1f}%")
