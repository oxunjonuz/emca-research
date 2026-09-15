"""diag_w4d.py -- measure the PROBE PROTOCOL's false-positive rate.

W4 (no CAUSAL on the decoy) failed at seed 8: (wait,glow) target warm
114/200 vs ctrl 80/199, Fisher p=0.00055. The world oracle says glow is
action-independent in warm (verify_env_v7 NV4 passes), so under
exchangeability this should not happen. Two candidate explanations:

  (a) a rare deterministic fluke of that seed's RNG stream (turn-104
      lesson: one seed's story is not a mechanism), or
  (b) a real protocol leak -- the two arms see non-exchangeable step
      sets.

This measures the null directly: run the REAL agent probe protocol on
regimes where glow carries NO causal information, over many seeds, and
count how many CAUSAL verdicts appear on glow. If the rate is ~0, seed 8
is a fluke; if it is percent-level, the protocol is biased and must be
fixed before the matrix.

Regimes:
  OFF   truth=off, decoy=on   (prereg C3's own regime: no cause at all)
  GLOWU decoy=on, truth=on, but at seed 8's geometry reproduced
  UNIT  a purpose-built action-independent glow, un-gated in phase:
        patched via a subclass so the ONLY difference from the real
        world is that glow does not depend on phase or action
"""
import collections
import sys

from env_terrarium_v7 import TerrariumV7, pick_edge_action, pick_decoy_action
from agent_emca_v7 import AgentV7Full

STEPS = 16000
NSEED = 20


def run(seed, truth, decoy, rich="low", cls=None):
    ea = pick_edge_action(seed)
    ag = AgentV7Full(seed)
    env = (cls or TerrariumV7)(seed, truth=truth, decoy=decoy, rich=rich,
                               edge_action=ea)
    for t in range(STEPS):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = (cls or TerrariumV7)(seed + 1000 + t, truth=truth,
                                       decoy=decoy, rich=rich,
                                       edge_action=ea)
    return ag


print(f"=== regime OFF (truth=off, decoy=on), {NSEED} seeds ===")
rows = []
for seed in range(NSEED):
    ag = run(seed, truth=False, decoy=True)
    caus = [(a, e, v["p"], v["rr"], v["target_yes"], v["target_no"],
             v["ctrl_yes"], v["ctrl_no"], v.get("phase"))
            for (a, e), v in ag.verdicts.items() if v["verdict"] == "CAUSAL"]
    for c in caus:
        print(f"   seed {seed}: {c}")
    rows.append(caus)
tot = sum(len(r) for r in rows)
print(f"   CAUSAL-on-any-effect total: {tot} over {NSEED} runs "
      f"(decoy-only seeds: {sum(1 for r in rows if r)})")

print(f"\n=== regime ON (truth=on, decoy=on), {NSEED} seeds ===")
fp_of = collections.Counter()
fn = 0
for seed in range(NSEED):
    ea = pick_edge_action(seed)
    ag = run(seed, truth=True, decoy=True)
    v = ag.verdicts.get((ea, "hum"))
    if not (v and v["verdict"] == "CAUSAL"):
        fn += 1
    for (a, e), vv in ag.verdicts.items():
        if e == "glow" and vv["verdict"] == "CAUSAL":
            fp_of[seed] += 1
            print(f"   seed {seed}: FP decoy {a}->{e} p={vv['p']} "
                  f"rr={vv['rr']} t={vv['target_yes']}/{vv['target_no']} "
                  f"c={vv['ctrl_yes']}/{vv['ctrl_no']} ph={vv.get('phase')}")
print(f"   true-edge FN: {fn}/{NSEED} ; decoy FP total: {sum(fp_of.values())}")

print("\n=== how large is the seed-8 anomaly relative to the null? ===")
print("   (a deterministic seed whose scored arms differ by >=0.15 in a")
print("    p=0.5 world; counted above as FP)")
