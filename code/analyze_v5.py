"""Independent analysis of the V5 matrix, read ONLY from the JSON
files on disk (fresh process, no shared state with the driver)."""
import glob
import json
import os
from statistics import mean, stdev

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_v5")
ARMS = ["v5_believer", "v5_spec", "v5_assoc", "v5_assoc02",
        "v5_rejector", "random", "qlearn", "ngram"]

logs = {}
for p in sorted(glob.glob(os.path.join(D, "*.json"))):
    with open(p) as f:
        d = json.load(f)
    assert d["steps"] == 16000, (p, d["steps"])
    logs[(d["condition"], d["seed"])] = d

print(f"loaded {len(logs)} runs; steps-audit clean")

def col(arm, key):
    return [logs[(arm, s)][key] for s in range(1, 11)
            if (arm, s) in logs]

# ---- per-arm table ----
print(f"\n{'arm':13s} {'reward':>8s} {'deaths':>7s} {'fruits':>7s} "
      f"{'lotus':>6s} {'fills':>6s} {'waits':>6s} {'aura':>6s} "
      f"{'sprC':>5s} {'sprA':>5s} {'spr02':>5s}")
for arm in ARMS:
    r = col(arm, "total_reward")
    if not r:
        continue
    print(f"{arm:13s} {mean(r):8.0f} {mean(col(arm,'deaths')):7.1f} "
          f"{mean(col(arm,'tree_fruits')):7.0f} "
          f"{mean(col(arm,'lotus_eaten')):6.1f} "
          f"{mean(col(arm,'pool_fills')):6.1f} "
          f"{mean(col(arm,'waits_in_aura')):6.0f} "
          f"{mean(col(arm,'aura_steps')):6.0f} "
          f"{sum(1 for x in col(arm,'spring_in_causal') if x):5d}/10 "
          f"{sum(1 for x in col(arm,'spring_in_assoc') if x):5d}/10 "
          f"{sum(1 for x in col(arm,'spring_in_assoc002') if x):5d}/10")

# ---- V1 CAPABILITY ----
rej_lotus_seeds = sum(1 for s in range(1, 11)
                      if logs[("v5_rejector", s)]["lotus_eaten"] >= 1)
ass_lotus_seeds = sum(1 for s in range(1, 11)
                      if logs[("v5_assoc", s)]["lotus_eaten"] >= 1)
ass_lotus_total = sum(logs[("v5_assoc", s)]["lotus_eaten"]
                      for s in range(1, 11))
print(f"\nV1 CAPABILITY: rejector lotus>=1 in {rej_lotus_seeds}/10 "
      f"(need >=8); assoc(0.5) lotus-seeds {ass_lotus_seeds}/10, "
      f"total lotuses {ass_lotus_total} (need <=2 total)")
v1 = rej_lotus_seeds >= 8 and ass_lotus_total <= 2
print("V1:", "PASS" if v1 else "FAIL")

# ---- V2 SELECTIVITY: rejector vs assoc02 ----
d = [logs[("v5_rejector", s)]["total_reward"]
     - logs[("v5_assoc02", s)]["total_reward"] for s in range(1, 11)]
import random
rng = random.Random(7)
boots = []
for _ in range(10000):
    boots.append(mean(rng.choices(d, k=len(d))))
boots.sort()
lo, hi = boots[249], boots[9749]
pos = sum(1 for x in d if x > 0)
# exact sign test
from math import comb
n = sum(1 for x in d if x != 0)
p_sign = sum(comb(n, k) for k in range(pos, n + 1)) / 2 ** n * 2
print(f"\nV2 SELECTIVITY D=rej-assoc02: mean {mean(d):+.0f} "
      f"sd {stdev(d):.0f} CI [{lo:+.0f},{hi:+.0f}] "
      f"sign {pos}+/{n-pos}- p={min(p_sign,1):.3f}")
v2 = mean(d) >= 300 and (p_sign <= 0.05 or lo > 0)
print("V2:", "PASS" if v2 else "FAIL")

# ---- V3 CAPABILITY->REWARD ----
d2 = [logs[("v5_rejector", s)]["total_reward"]
      - logs[("v5_assoc", s)]["total_reward"] for s in range(1, 11)]
print(f"\nV3 D2=rej-assoc: mean {mean(d2):+.0f} "
      f"(expected small -- lotus ~tens vs fruit channel ~thousands)")

# ---- V4 epistemic controls ----
rej_spr = sum(1 for s in range(1, 11)
              if logs[("v5_rejector", s)]["spring_in_causal"])
ass_spr = sum(1 for s in range(1, 11)
              if logs[("v5_assoc", s)]["spring_in_assoc"])
ass02_spr = sum(1 for s in range(1, 11)
                if logs[("v5_assoc02", s)]["spring_in_assoc002"])
bel_decoy = sum(1 for s in range(1, 11)
                if logs[("v5_believer", s)]["decoy_torch_in_causal"])
rej_decoy = sum(1 for s in range(1, 11)
                if logs[("v5_rejector", s)]["decoy_torch_in_causal"])
rej_true = sum(1 for s in range(1, 11)
               if logs[("v5_rejector", s)]["true_in_causal"].get("eat->ate")
               and logs[("v5_rejector", s)]["true_in_causal"].get(
                   "grasp->tree_gather"))
print(f"\nV4: spring in rejector causal {rej_spr}/10 (>=8); "
      f"in assoc(0.5) {ass_spr}/10 (0); in assoc02 {ass02_spr}/10 (>=8); "
      f"decoy in believer {bel_decoy}/10 (>=8); "
      f"decoy in rejector {rej_decoy}/10 (0); "
      f"true edges in rejector {rej_true}/10 (>=8)")
v4 = (rej_spr >= 8 and ass_spr == 0 and ass02_spr >= 8
      and bel_decoy >= 8 and rej_decoy == 0 and rej_true >= 8)
print("V4:", "PASS" if v4 else "FAIL")

# ---- V5 mechanism ----
rw = [logs[("v5_rejector", s)]["waits_in_aura"] for s in range(1, 11)]
aw = [logs[("v5_assoc", s)]["waits_in_aura"] for s in range(1, 11)]
bw = [logs[("v5_believer", s)]["waits_in_aura"] for s in range(1, 11)]
print(f"\nV5 mechanism: waits_in_aura rejector {mean(rw):.0f} vs "
      f"assoc {mean(aw):.0f} believer {mean(bw):.0f}")

# informative columns
for arm in ("v5_believer", "v5_spec"):
    verd = sum(1 for s in range(1, 11)
               if logs[(arm, s)]["spring_in_causal"])
    print(f"informative: {arm} spring-in-causal {verd}/10")
