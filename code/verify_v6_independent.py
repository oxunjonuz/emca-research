"""INDEPENDENT verification of the V6 matrix verdicts: a second pass
with a DIFFERENT code path (no shared functions with analyze_v6.py --
its own bootstrap, its own sign test, its own table walk), reading only
the JSON files from disk. Also recomputes the mechanism decomposition
and the discovery ledger. If this disagrees with analyze_v6.py, the
disagreement is the finding."""
import glob
import json
import os
import random
from statistics import mean, stdev

D = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "results", "matrix_v6")

rows = []
for p in sorted(glob.glob(os.path.join(D, "*.json"))):
    with open(p) as f:
        rows.append(json.load(f))
assert len(rows) == 80, len(rows)
by = {(r["condition"], r["seed"]): r for r in rows}


def rew(arm):
    return {s: by[(arm, s)]["total_reward"] for s in range(1, 11)}


def my_boot(vals, n=20000):
    # a different bootstrap: resample indices, not values
    rng = random.Random(1234)
    idx = list(range(10))
    means = []
    for _ in range(n):
        pick = [idx[rng.randrange(10)] for _ in range(10)]
        means.append(sum(vals[i] for i in pick) / 10)
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n)]


def my_sign(vals):
    # exact binomial, one-sided doubled (same convention as analyze_v6)
    from math import comb
    pos = sum(1 for v in vals if v > 0)
    n = sum(1 for v in vals if v != 0)
    if n == 0:
        return pos, n, 1.0
    tail = sum(comb(n, k) for k in range(pos, n + 1)) / (2 ** n)
    return pos, n, min(2 * tail, 1.0)


def diff(arm_a, arm_b):
    ra, rb = rew(arm_a), rew(arm_b)
    return [ra[s] - rb[s] for s in range(1, 11)]


print("=== G1 (prober - rejector)")
d = diff("v6_prober", "v6_rejector")
lo, hi = my_boot(d)
pos, n, p = my_sign(d)
print(f"mean {mean(d):+.1f} CI [{lo:+.0f},{hi:+.0f}] sign {pos}/{n} p={p:.4f}")
g1 = mean(d) >= 300 and (p <= 0.05 or lo > 0)
print("G1:", "PASS" if g1 else "FAIL")

print("=== G2 (oracle - rejector)")
d2 = diff("v6_oracle", "v6_rejector")
lo2, hi2 = my_boot(d2)
pos2, n2, p2 = my_sign(d2)
print(f"mean {mean(d2):+.1f} CI [{lo2:+.0f},{hi2:+.0f}] sign {pos2}/{n2} "
      f"p={p2:.4f}")
g2 = mean(d2) >= 1000 and (p2 <= 0.05 or lo2 > 0)
print("G2:", "PASS" if g2 else "FAIL")

print("=== G3 (oracle - prober)")
d3 = diff("v6_oracle", "v6_prober")
lo3, hi3 = my_boot(d3)
pos3, n3, p3 = my_sign(d3)
print(f"mean {mean(d3):+.1f} CI [{lo3:+.0f},{hi3:+.0f}] sign {pos3}/{n3} "
      f"p={p3:.4f}")

print("=== G4")
rej_spr = sum(1 for s in range(1, 11)
              if by[("v6_rejector", s)]["spring_in_causal"])
prb = sum(1 for s in range(1, 11)
          if by[("v6_prober", s)]["probe_verdicts"]
          .get("wait->spring_flow", {}).get("verdict") == "CAUSAL")
a02 = sum(1 for s in range(1, 11)
          if by[("v6_assoc02", s)]["spring_in_assoc002"])
print(f"rejector spring {rej_spr}/10, prober CAUSAL {prb}/10, "
      f"assoc02 {a02}/10")
g4 = rej_spr == 0 and prb >= 7 and a02 >= 7
print("G4:", "PASS" if g4 else "FAIL")

print("=== G5")
ass = sum(by[("v6_assoc", s)]["lotus_eaten"] for s in range(1, 11))
rnd = sum(by[("random", s)]["lotus_eaten"] for s in range(1, 11))
print(f"assoc lotuses {ass}, random {rnd}")
g5 = ass <= 2 and rnd == 0
print("G5:", "PASS" if g5 else "FAIL")

print("=== G6")
bd = sum(1 for s in range(1, 11)
         if by[("v6_believer", s)]["decoy_torch_in_causal"])
rd = sum(1 for s in range(1, 11)
         if by[("v6_rejector", s)]["decoy_torch_in_causal"])
pd_ = sum(1 for s in range(1, 11)
          if by[("v6_prober", s)]["decoy_torch_in_causal"])
print(f"believer {bd}/10, rejector {rd}/10, prober {pd_}/10")
g6 = bd >= 8 and rd == 0 and pd_ == 0
print("G6:", "PASS" if g6 else "FAIL")

print("=== G7")
pdd = mean(by[("v6_prober", s)]["deaths"] for s in range(1, 11))
rdd = mean(by[("v6_rejector", s)]["deaths"] for s in range(1, 11))
print(f"prober {pdd:.1f} vs rejector {rdd:.1f}")
g7 = pdd <= rdd + 15
print("G7:", "PASS" if g7 else "FAIL")

print("=== decomposition cross-check (own walk)")
lotus_d = mean(by[("v6_prober", s)]["lotus_eaten"]
               - by[("v6_rejector", s)]["lotus_eaten"]
               for s in range(1, 11))
fruit_d = mean(by[("v6_prober", s)]["tree_fruits"]
               - by[("v6_rejector", s)]["tree_fruits"]
               for s in range(1, 11))
print(f"lotus +{lotus_d:.1f}, fruits {fruit_d:+.1f}")
# correlation, own arithmetic
fg = [by[("v6_prober", s)]["tree_fruits"]
      - by[("v6_rejector", s)]["tree_fruits"] for s in range(1, 11)]
d1 = diff("v6_prober", "v6_rejector")
mf, md = mean(fg), mean(d1)
cov = sum((fg[i] - mf) * (d1[i] - md) for i in range(10))
sd = (sum((x - mf) ** 2 for x in fg)
      * sum((x - md) ** 2 for x in d1)) ** 0.5
print(f"corr(D, fruit_gap) = {cov/sd:.3f}")

print("=== the ledger")
for arm in ("v6_oracle", "v6_prober", "v6_rejector", "v6_assoc02",
            "v6_believer"):
    print(f"{arm:13s} lotus {mean(by[(arm,s)]['lotus_eaten'] for s in range(1,11)):5.1f} "
          f"reward {mean(by[(arm,s)]['total_reward'] for s in range(1,11)):8.0f} "
          f"deaths {mean(by[(arm,s)]['deaths'] for s in range(1,11)):5.1f}")

print()
print("FINAL:", "G1", "PASS" if g1 else "FAIL", "G2",
      "PASS" if g2 else "FAIL", "G4", "PASS" if g4 else "FAIL",
      "G5", "PASS" if g5 else "FAIL", "G6", "PASS" if g6 else "FAIL",
      "G7", "PASS" if g7 else "FAIL")
