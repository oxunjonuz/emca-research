"""Independent verification of the V5 matrix -- FRESH code, reads ONLY
the JSON files on disk (no imports from analyze_v5.py; recomputes
every preregistered verdict and the decomposition from raw fields).
Written after the analysis; any disagreement is a red flag on the
analysis, not on this file."""
import glob
import json
import os
import random
from math import comb
from statistics import mean, stdev

D = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "results", "matrix_v5")
logs = {}
for p in sorted(glob.glob(os.path.join(D, "*.json"))):
    with open(p) as f:
        d = json.load(f)
    assert d["steps"] == 16000, p
    logs[(d["condition"], d["seed"])] = d
assert len(logs) == 80, len(logs)
print(f"IV: 80/80 runs loaded, steps-audit clean")

def C(arm, key):
    return [logs[(arm, s)][key] for s in range(1, 11)]

# ---- V1 CAPABILITY ----
rej_seeds = sum(1 for x in C("v5_rejector", "lotus_eaten") if x >= 1)
ass_total = sum(C("v5_assoc", "lotus_eaten"))
ass_seeds = sum(1 for x in C("v5_assoc", "lotus_eaten") if x >= 1)
print(f"IV V1: rejector lotus>=1 in {rej_seeds}/10 (gate >=8) -> "
      f"{'PASS' if rej_seeds >= 8 else 'FAIL'}; "
      f"assoc(0.5) lotuses {ass_total} in {ass_seeds} seeds (gate <=2) -> "
      f"{'PASS' if ass_total <= 2 else 'FAIL'}")
print(f"IV V1 detail: rejector per-seed {C('v5_rejector','lotus_eaten')}")
print(f"IV V1 detail: assoc(0.5) per-seed {C('v5_assoc','lotus_eaten')}")

# ---- V2 SELECTIVITY ----
d = [C("v5_rejector", "total_reward")[i] - C("v5_assoc02", "total_reward")[i]
     for i in range(10)]
rng = random.Random(11)
boots = sorted(mean(rng.choices(d, k=10)) for _ in range(20000))
lo, hi = boots[499], boots[19499]
pos = sum(1 for x in d if x > 0)
n = sum(1 for x in d if x != 0)
p_sign = min(1.0, 2 * sum(comb(n, k) for k in range(pos, n + 1)) / 2 ** n)
print(f"IV V2: D mean {mean(d):+.0f} sd {stdev(d):.0f} "
      f"CI [{lo:+.0f},{hi:+.0f}] sign {pos}+/{n-pos}- p={p_sign:.3f} -> "
      f"{'PASS' if (mean(d) >= 300 and (p_sign <= 0.05 or lo > 0)) else 'FAIL'}")

# ---- V3 ----
d2 = [C("v5_rejector", "total_reward")[i] - C("v5_assoc", "total_reward")[i]
      for i in range(10)]
print(f"IV V3: D2 mean {mean(d2):+.0f} (no gate; lotus channel vs fruit channel)")

# ---- V4 epistemic controls ----
rej_spr = sum(1 for x in C("v5_rejector", "spring_in_causal") if x)
ass_spr = sum(1 for x in C("v5_assoc", "spring_in_assoc") if x)
ass02_spr = sum(1 for x in C("v5_assoc02", "spring_in_assoc002") if x)
bel_decoy = sum(1 for x in C("v5_believer", "decoy_torch_in_causal") if x)
rej_decoy = sum(1 for x in C("v5_rejector", "decoy_torch_in_causal") if x)
rej_true = sum(1 for s in range(1, 11)
               if logs[("v5_rejector", s)]["true_in_causal"].get("eat->ate")
               and logs[("v5_rejector", s)]["true_in_causal"].get("grasp->tree_gather"))
print(f"IV V4: spring rejector {rej_spr}/10 (>=8), assoc(0.5) {ass_spr}/10 (==0), "
      f"assoc02 {ass02_spr}/10 (>=8); decoy believer {bel_decoy}/10 (>=8), "
      f"rejector {rej_decoy}/10 (==0); true edges rejector {rej_true}/10 (>=8)")
v4 = (rej_spr >= 8 and ass_spr == 0 and ass02_spr >= 8
      and bel_decoy >= 8 and rej_decoy == 0 and rej_true >= 8)
print(f"IV V4 -> {'PASS' if v4 else 'FAIL'}")

# ---- V5 mechanism ----
print(f"IV V5: waits_in_aura rejector {mean(C('v5_rejector','waits_in_aura')):.0f} "
      f"vs assoc(0.5) {mean(C('v5_assoc','waits_in_aura')):.0f} "
      f"vs assoc02 {mean(C('v5_assoc02','waits_in_aura')):.0f} "
      f"vs believer {mean(C('v5_believer','waits_in_aura')):.0f}")

# ---- the decomposition (independent recompute) ----
print("\nIV decomposition D(rej - assoc02), totals over 10 seeds:")
for name, fn in (("fruits*8", lambda d: d["tree_fruits"] * 8),
                 ("berries*1", lambda d: d["berries_eaten"]),
                 ("lotus*8", lambda d: d["lotus_eaten"] * 8),
                 ("treasury*1", lambda d: d["treasury_eaten"]),
                 ("deaths*-5", lambda d: -d["deaths"] * 5),
                 ("scorch*-1", lambda d: -d["scorch_paid"])):
    rv = sum(fn(logs[("v5_rejector", s)]) for s in range(1, 11))
    av = sum(fn(logs[("v5_assoc02", s)]) for s in range(1, 11))
    print(f"  {name:12s} rej {rv:9.0f}  a02 {av:9.0f}  D {rv-av:+9.0f}")
tot_r = sum(C("v5_rejector", "total_reward"))
tot_a = sum(C("v5_assoc02", "total_reward"))
print(f"  {'TOTAL':12s} rej {tot_r:9.0f}  a02 {tot_a:9.0f}  D {tot_r-tot_a:+9.0f}")

# corr(D, fruit_gap) -- the weather-noise check from turn 104
fg = [C("v5_rejector", "tree_fruits")[i] - C("v5_assoc02", "tree_fruits")[i]
      for i in range(10)]
fg8 = [x * 8 for x in fg]
c = sum((d[i] - mean(d)) * (fg8[i] - mean(fg8)) for i in range(10)) / \
    (stdev(d) * stdev(fg8) * 9)
print(f"IV corr(D, fruit_gap*8) = {c:.3f} (turn-104 weather noise analogue)")

# baseline sanity
for arm in ("random", "qlearn", "ngram"):
    print(f"IV baseline {arm}: reward {mean(C(arm,'total_reward')):.0f} "
          f"deaths {mean(C(arm,'deaths')):.1f} lotus {sum(C(arm,'lotus_eaten'))}")
print("\nIV: all numbers recomputed from disk, fresh code.")
