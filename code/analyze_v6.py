"""Independent analysis of the V6 matrix, read ONLY from the JSON files
on disk (fresh process, no shared state with the driver). Verdicts G1-G8
exactly as pre-registered in research/PREREG_V6.md -- thresholds are
NOT moved."""
import glob
import json
import os
import random
from math import comb
from statistics import mean, stdev

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_v6")
ARMS = ["v6_prober", "v6_oracle", "v6_rejector", "v6_assoc02",
        "v6_assoc", "v6_believer", "v6_nocausal", "random"]

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


def boot_ci(d, reps=10000, seed=7):
    rng = random.Random(seed)
    boots = sorted(mean(rng.choices(d, k=len(d))) for _ in range(reps))
    return boots[249], boots[9749]


def sign_test(d):
    pos = sum(1 for x in d if x > 0)
    n = sum(1 for x in d if x != 0)
    if n == 0:
        return pos, n, 1.0
    p = sum(comb(n, k) for k in range(pos, n + 1)) / 2 ** n * 2
    return pos, n, min(p, 1.0)


def contrast(a, b, label, gate_mean=None, gate_sign=None):
    d = [logs[(a, s)]["total_reward"] - logs[(b, s)]["total_reward"]
         for s in range(1, 11)]
    lo, hi = boot_ci(d)
    pos, n, p = sign_test(d)
    print(f"\n{label}: mean {mean(d):+.0f} sd {stdev(d):.0f} "
          f"CI [{lo:+.0f},{hi:+.0f}] sign {pos}+/{n-pos}- p={p:.3f}")
    ok = True
    if gate_mean is not None:
        ok = ok and mean(d) >= gate_mean
    if gate_sign is not None:
        ok = ok and (p <= gate_sign or lo > 0)
    if gate_mean is not None or gate_sign is not None:
        print(f"  gate: mean>={gate_mean} AND (sign p<={gate_sign} OR "
              f"CI>0) -> {'PASS' if ok else 'FAIL'}")
    return d, ok


# ---- per-arm table ----
print(f"\n{'arm':13s} {'reward':>8s} {'deaths':>7s} {'fruits':>7s} "
      f"{'lotus':>6s} {'waits':>6s} {'aura':>6s} {'probe':>6s} "
      f"{'sprC':>5s} {'sprA02':>6s}")
for arm in ARMS:
    r = col(arm, "total_reward")
    if not r:
        continue
    print(f"{arm:13s} {mean(r):8.0f} {mean(col(arm,'deaths')):7.1f} "
          f"{mean(col(arm,'tree_fruits')):7.0f} "
          f"{mean(col(arm,'lotus_eaten')):6.1f} "
          f"{mean(col(arm,'waits_in_aura')):6.0f} "
          f"{mean(col(arm,'aura_steps')):6.0f} "
          f"{mean(col(arm,'probe_steps')):6.0f} "
          f"{sum(1 for x in col(arm,'spring_in_causal') if x):5d}/10 "
          f"{sum(1 for x in col(arm,'spring_in_assoc002') if x):6d}/10")

# ---- G1 DISCOVERY-NET (primary) ----
d1, g1 = contrast("v6_prober", "v6_rejector",
                  "G1 DISCOVERY-NET D(prober-rejector)",
                  gate_mean=300, gate_sign=0.05)

# ---- G2 DISCOVERY-GROSS ----
d2, g2 = contrast("v6_oracle", "v6_rejector",
                  "G2 DISCOVERY-GROSS D(oracle-rejector)",
                  gate_mean=1000, gate_sign=0.05)

# ---- G3 DISCOVERY-COST ----
d3, _ = contrast("v6_oracle", "v6_prober", "G3 DISCOVERY-COST "
                 "D(oracle-prober)")

# ---- G4 grey blindness/resolution ----
rej_spr = sum(1 for x in col("v6_rejector", "spring_in_causal") if x)
prb_cau = sum(1 for s in range(1, 11)
               if (logs.get(("v6_prober", s), {}).get("probe_verdicts")
                   or {}).get("wait->spring_flow", {}).get("verdict")
               == "CAUSAL")
ass02_spr = sum(1 for x in col("v6_assoc02", "spring_in_assoc002") if x)
print(f"\nG4: spring in rejector causal {rej_spr}/10 (need 0); "
      f"prober CAUSAL {prb_cau}/10 (need >=7); "
      f"assoc02 possession {ass02_spr}/10 (need >=7)")
g4 = rej_spr == 0 and prb_cau >= 7 and ass02_spr >= 7
print("G4:", "PASS" if g4 else "FAIL")
# verdict breakdown (informative)
verd = {}
for s in range(1, 11):
    v = (logs.get(("v6_prober", s), {}).get("probe_verdicts")
         or {}).get("wait->spring_flow", {}).get("verdict", "-")
    verd[v] = verd.get(v, 0) + 1
print(f"  prober verdicts: {verd}")

# ---- G5 anti-illusion ----
ass_lotus_total = sum(logs[("v6_assoc", s)]["lotus_eaten"]
                      for s in range(1, 11))
rnd_lotus_total = sum(logs[("random", s)]["lotus_eaten"]
                      for s in range(1, 11))
print(f"\nG5: assoc(0.5) lotuses {ass_lotus_total} (need <=2); "
      f"random {rnd_lotus_total} (need 0)")
g5 = ass_lotus_total <= 2 and rnd_lotus_total == 0
print("G5:", "PASS" if g5 else "FAIL")

# ---- G6 decoy hygiene ----
bel_decoy = sum(1 for x in col("v6_believer", "decoy_torch_in_causal")
                if x)
rej_decoy = sum(1 for x in col("v6_rejector", "decoy_torch_in_causal")
                if x)
prb_decoy = sum(1 for x in col("v6_prober", "decoy_torch_in_causal")
                if x)
prb_decoy_verd = (logs.get(("v6_prober", s), {}).get("probe_verdicts")
                  or {}).get("grasp->torch_lit", {})
print(f"\nG6: decoy in believer {bel_decoy}/10 (>=8); rejector "
      f"{rej_decoy}/10 (0); prober {prb_decoy}/10 (0)")
g6 = bel_decoy >= 8 and rej_decoy == 0 and prb_decoy == 0
print("G6:", "PASS" if g6 else "FAIL")

# ---- G7 survival ----
prb_deaths = mean(col("v6_prober", "deaths"))
rej_deaths = mean(col("v6_rejector", "deaths"))
print(f"\nG7: prober deaths {prb_deaths:.1f} vs rejector {rej_deaths:.1f} "
      f"(need <= +15)")
g7 = prb_deaths <= rej_deaths + 15
print("G7:", "PASS" if g7 else "FAIL")

# ---- mechanism decomposition (G1's anatomy) ----
print("\n---- mechanism decomposition (per-seed diffs, prober-rejector)")
for key in ("lotus_eaten", "tree_fruits", "berries_eaten", "deaths",
            "scorch_paid", "grasp_costs_paid", "waits_in_aura",
            "aura_steps", "lotus_goal_steps", "probe_steps",
            "chimes_collected", "treasury_eaten"):
    dd = [logs[("v6_prober", s)][key] - logs[("v6_rejector", s)][key]
          for s in range(1, 11)]
    print(f"  {key:18s} mean {mean(dd):+9.1f}")
# the fruit-weather confounder check (the turn-104/114 lesson)
fg = [logs[("v6_prober", s)]["tree_fruits"]
      - logs[("v6_rejector", s)]["tree_fruits"] for s in range(1, 11)]
num = sum((fg[i] - mean(fg)) * (d1[i] - mean(d1)) for i in range(10))
den = (sum((x - mean(fg)) ** 2 for x in fg)
       * sum((x - mean(d1)) ** 2 for x in d1)) ** 0.5
print(f"  corr(D, fruit_gap) = {num/den if den else 0:.3f} "
      f"(the weather-noise channel)")

# ---- oracle decomposition: gross value split ----
print("\n---- the discovery ledger (oracle-prober-rejector)")
for arm in ("v6_oracle", "v6_prober", "v6_rejector"):
    print(f"  {arm:13s} lotus {mean(col(arm,'lotus_eaten')):5.1f} "
          f"reward {mean(col(arm,'total_reward')):8.0f} "
          f"deaths {mean(col(arm,'deaths')):5.1f}")

print("\nVERDICTS: G1", "PASS" if g1 else "FAIL",
      "| G2", "PASS" if g2 else "FAIL",
      "| G3 (no gate)", "| G4", "PASS" if g4 else "FAIL",
      "| G5", "PASS" if g5 else "FAIL",
      "| G6", "PASS" if g6 else "FAIL",
      "| G7", "PASS" if g7 else "FAIL")
