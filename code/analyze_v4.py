"""Independent analysis of the v4 matrix -- disk only, fresh process,
no imports from the runner/env/agents. Frozen to
results/matrix_v4_analysis.txt."""
import json
import glob
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load_all():
    rows = {}
    for path in glob.glob(os.path.join(HERE, "results/matrix_v4/*.json")):
        d = json.load(open(path))
        rows[(d["condition"], d["seed"])] = d
    return rows


def sign_test_p(pos, neg, zero):
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    # exact two-sided binomial p = 2*sum_{i<=k} C(n,i)/2^n
    s = sum(math.comb(n, i) for i in range(0, k + 1))
    p = min(1.0, 2 * s / 2 ** n)
    return p


def boot_ci(ds, iters=10000, seed=0):
    import random
    rng = random.Random(seed)
    n = len(ds)
    means = []
    for _ in range(iters):
        s = [ds[rng.randrange(n)] for _ in range(n)]
        means.append(sum(s) / n)
    means.sort()
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def main():
    rows = load_all()
    out = []
    P = out.append
    conds = ["v4_believer", "v4_spec", "v4_assoc", "v4_rejector",
             "v4_curious", "v4_pure", "random", "qlearn", "ngram"]
    seeds = list(range(1, 11))

    # steps audit
    bad = [(c, s) for c in conds for s in seeds
           if rows.get((c, s), {}).get("steps") != 16000]
    P(f"steps-audit: {len(rows)} files, bad={bad}")

    # per-arm summary
    P(f"\n{'arm':14s} {'reward':>8s} {'deaths':>7s} {'fruits':>7s} "
      f"{'torch':>6s} {'treas':>6s} {'scorch':>8s} {'gnt':>6s} "
      f"{'torGoal':>8s} decoy_c")
    for c in conds:
        rs = [rows[(c, s)] for s in seeds if (c, s) in rows]
        if not rs:
            continue
        dec = sum(1 for r in rs if r.get("decoy_torch_in_causal")) \
            if rs[0].get("decoy_torch_in_causal") is not None else "-"
        P(f"{c:14s} {sum(r['total_reward'] for r in rs)/len(rs):8.0f} "
          f"{sum(r['deaths'] for r in rs)/len(rs):7.1f} "
          f"{sum(r['tree_fruits'] for r in rs)/len(rs):7.1f} "
          f"{sum(r['torches_collected'] for r in rs)/len(rs):6.1f} "
          f"{sum(r['treasury_eaten'] for r in rs)/len(rs):6.1f} "
          f"{sum(r['scorch_paid'] for r in rs)/len(rs):8.1f} "
          f"{sum(r['grasps_near_torch'] for r in rs)/len(rs):6.0f} "
          f"{sum(r.get('torch_goal_steps',0) for r in rs)/len(rs):8.0f} "
          f"{dec}")

    # primary contrasts, paired per seed
    def paired(a, b, name):
        ds = [rows[(a, s)]["total_reward"] - rows[(b, s)]["total_reward"]
              for s in seeds if (a, s) in rows and (b, s) in rows]
        pos = sum(1 for d in ds if d > 0)
        neg = sum(1 for d in ds if d < 0)
        zero = sum(1 for d in ds if d == 0)
        mean = sum(ds) / len(ds)
        lo, hi = boot_ci(ds)
        p = sign_test_p(pos, neg, zero)
        P(f"\n{name}: per-seed D = {[round(d) for d in ds]}")
        P(f"  mean={mean:+.0f} sd={math.sqrt(sum((d-mean)**2 for d in ds)/len(ds)):.0f} "
          f"CI95=[{lo:+.0f},{hi:+.0f}] sign {pos}+/{neg}-/{zero}0 p={p:.3f}")
        return ds, mean, p

    paired("v4_rejector", "v4_believer", "PRIMARY D(rej - believer)")
    paired("v4_rejector", "v4_assoc", "D2(rej - assoc)")
    paired("v4_rejector", "v4_spec", "D3(rej - spec)")
    paired("v4_curious", "v4_rejector", "D4(curious - rej)")

    # T1 identifier stability
    dec_bel = sum(1 for s in seeds
                  if rows[("v4_believer", s)]["decoy_torch_in_causal"])
    dec_rej = sum(1 for s in seeds
                  if rows[("v4_rejector", s)]["decoy_torch_in_causal"])
    true_rej = sum(1 for s in seeds
                   if rows[("v4_rejector", s)]["true_in_causal"].get("eat->ate")
                   and rows[("v4_rejector", s)]["true_in_causal"]
                   .get("grasp->tree_gather"))
    dec_assoc = sum(1 for s in seeds
                    if rows[("v4_assoc", s)]["decoy_torch_in_causal"])
    P(f"\nT1 identifier: decoy in believer causal {dec_bel}/10; "
      f"in rejector {dec_rej}/10; in assoc {dec_assoc}/10; "
      f"true edges rejector {true_rej}/10")

    # T2 belief tax
    gnt_b = sum(rows[("v4_believer", s)]["grasps_near_torch"] for s in seeds)
    gnt_r = sum(rows[("v4_rejector", s)]["grasps_near_torch"] for s in seeds)
    win = sum(1 for s in seeds
              if rows[("v4_believer", s)]["grasps_near_torch"]
              > rows[("v4_rejector", s)]["grasps_near_torch"])
    tg_b = sum(rows[("v4_believer", s)]["torch_goal_steps"] for s in seeds)
    tg_r = sum(rows[("v4_rejector", s)]["torch_goal_steps"] for s in seeds)
    P(f"T2 belief tax: pocket-grasps believer {gnt_b} vs rejector {gnt_r} "
      f"(believer > rejector in {win}/10); torch-goal steps "
      f"{tg_b} vs {tg_r}")

    # T3 chain: treasury meals per arm
    for c in conds[:6]:
        te = [rows[(c, s)]["treasury_eaten"] for s in seeds]
        P(f"T3 {c:13s} treasury meals per seed {te} "
          f"(seeds with >=1: {sum(1 for x in te if x >= 1)})")

    # T4 curiosity bitter
    w5a = sum(1 for s in seeds
              if rows[("v4_pure", s)]["deaths"] > max(
                  rows[(a, s)]["deaths"] for a in
                  ("v4_believer", "v4_spec", "v4_assoc", "v4_rejector",
                   "v4_curious")))
    w5b = sum(1 for s in seeds
              if rows[("v4_curious", s)]["deaths"]
              >= rows[("v4_rejector", s)]["deaths"])
    P(f"T4 bitter curiosity: pure dies hardest {w5a}/10; "
      f"curious deaths >= rejector {w5b}/10")

    # T5 baselines
    w6 = all(rows[("random", s)]["deaths"] > max(
        rows[(a, s)]["deaths"] for a in
        ("v4_believer", "v4_spec", "v4_assoc", "v4_rejector", "v4_curious"))
        for s in seeds)
    P(f"T5 random dies most in all seeds: {w6}")

    text = "\n".join(out)
    print(text)
    with open(os.path.join(HERE, "results/matrix_v4_analysis.txt"), "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
