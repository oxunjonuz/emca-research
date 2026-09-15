"""Independent analysis of the v3.3 SEED EXTENSION (turn 104, op_b93bea555b7e).

Reads ONLY the JSONs on disk (results/matrix_v33/*.json). No imports
from the runner, the env, or the agents. Fresh process, disk-only.

Question (owner directive): is the causal-vs-associative contrast a
small STABLE effect or pure seed noise? Preregistration:
research/PREREG_SEEDS_V33.md (art_ed2ad562dd71), written BEFORE any
seed-extension run.

Primary contrast:  D_s  = reward(v2.5c, s) - reward(v2.1, s)
Secondary:          D2_s = reward(v2.5c, s) - reward(nocausal, s)
                    D3_s = reward(v2.1, s) - reward(nocausal, s)

Verdicts V1/V2/V3 per the prereg thresholds (|mean D| >= 300 practical
floor, exact sign test p<=0.05, bootstrap 95% CI excluding 0).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "matrix_v33")
SEEDS = list(range(1, 16))  # 1-3 from turn 103, 4-15 new
ARMS = ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
        "prober", "curious_chain"]


def load(arm, seed):
    with open(os.path.join(RES, f"{arm}_{seed}.json")) as f:
        return json.load(f)


def mean(xs):
    return sum(xs) / len(xs)


def sd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def bootstrap_ci(xs, n=20000, seed=777):
    import random
    rng = random.Random(seed)
    n_ = len(xs)
    means = []
    for _ in range(n):
        sample = [xs[rng.randrange(n_)] for _ in range(n_)]
        means.append(mean(sample))
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n)]


def sign_test(xs):
    pos = sum(1 for x in xs if x > 0)
    neg = sum(1 for x in xs if x < 0)
    n = pos + neg
    if n == 0:
        return 1.0, pos, neg
    # exact two-sided binomial, p = 0.5
    from math import comb
    p = sum(comb(n, k) for k in range(0, min(pos, neg) + 1)) / 2 ** n * 2
    return min(1.0, p), pos, neg


def wilcoxon(xs):
    # exact Wilcoxon signed-rank via scipy (secondary statistic)
    from scipy.stats import wilcoxon
    w, p = wilcoxon(xs)
    return w, p


def paired_t(xs):
    m = mean(xs)
    s = sd(xs)
    t = m / (s / math.sqrt(len(xs)))
    return t, m


def median(xs):
    ys = sorted(xs)
    n = len(ys)
    return ys[n // 2] if n % 2 else (ys[n // 2 - 1] + ys[n // 2]) / 2


def mad(xs):
    med = median(xs)
    return median([abs(x - med) for x in xs])


def main():
    print("=== V3.3 SEED EXTENSION: 6 arms x 15 seeds, disk-only ===\n")

    # ---- integrity: every file present, steps=16000 ----
    bad = []
    for arm in ARMS:
        for s in SEEDS:
            d = load(arm, s)
            if d["steps"] != 16000:
                bad.append((arm, s, d["steps"]))
    print(f"steps-audit (90 files): {'CLEAN' if not bad else bad}\n")

    # ---- per-arm means over 15 seeds ----
    print("--- arm means over 15 seeds (reward / deaths / fruits / treasures) ---")
    for arm in ARMS:
        rw = [load(arm, s)["total_reward"] for s in SEEDS]
        de = [load(arm, s)["deaths"] for s in SEEDS]
        fr = [load(arm, s)["tree_fruits"] for s in SEEDS]
        tz = [load(arm, s)["treasures"] for s in SEEDS]
        print(f"{arm:14s} reward={mean(rw):9.1f}+-{sd(rw):6.1f} "
              f"deaths={mean(de):5.1f} fruits={mean(fr):6.1f} "
              f"treasures={mean(tz):5.1f}")
    print()

    # ---- PRIMARY contrast D = v2.5c - v2.1 ----
    D = [load("emca_v25c", s)["total_reward"] - load("emca_v21", s)["total_reward"]
         for s in SEEDS]
    print("--- PRIMARY D_s = reward(v2.5c) - reward(v2.1), per seed ---")
    for s, d in zip(SEEDS, D):
        print(f"  seed {s:2d}: {d:+9.1f}")
    mD = mean(D)
    lo, hi = bootstrap_ci(D)
    p_sign, pos, neg = sign_test(D)
    w, p_w = wilcoxon(D)
    t, _ = paired_t(D)
    print(f"\n  mean D = {mD:+.1f}  sd = {sd(D):.1f}")
    print(f"  bootstrap 95% CI = [{lo:+.1f}, {hi:+.1f}]")
    print(f"  sign test: {pos} pos / {neg} neg, exact p = {p_sign:.4f}")
    print(f"  Wilcoxon (secondary): W={w:.1f}, p = {p_w:.4f}")
    print(f"  paired t (secondary): t = {t:.2f}, df = {len(D)-1}")

    # ---- verdict per prereg ----
    print("\n--- VERDICT (prereg V1/V2/V3) ---")
    stable = (p_sign <= 0.05) and not (lo <= 0 <= hi) and abs(mD) >= 300
    ci_excl_zero = not (lo <= 0 <= hi)
    if stable:
        v = "V1 STABLE SMALL EFFECT"
    elif ci_excl_zero and abs(mD) < 300:
        v = "V2 PURE NOISE (effect, if any, practically negligible)"
    elif not ci_excl_zero:
        upper = abs(hi) if mD >= 0 else abs(lo)
        if upper < 300:
            v = "V2 PURE NOISE (strong form: 95% bound < 300)"
        else:
            v = "V3 UNRESOLVED (CI covers 0 but allows |effect| > 300)"
    else:
        v = "V3 UNRESOLVED (sign test fails though CI excludes 0)"
    print(f"  {v}")
    print(f"  (criteria: sign p={p_sign:.4f}<=0.05: {p_sign<=0.05}; "
          f"CI [{lo:+.0f},{hi:+.0f}] excludes 0: {ci_excl_zero}; "
          f"|mean|={abs(mD):.0f}>=300: {abs(mD)>=300})")

    # ---- seed-3 anomaly check ----
    med = median(D)
    m_ = mad(D)
    print(f"\n--- seed-3 anomaly check (prereg: >2.5 MAD from median) ---")
    print(f"  median D = {med:+.1f}, MAD = {m_:.1f}, "
          f"2.5*MAD = {2.5*m_:.1f}")
    for s, d in zip(SEEDS, D):
        flag = " <== OUTLIER" if abs(d - med) > 2.5 * m_ else ""
        print(f"  seed {s:2d}: |D-med| = {abs(d-med):8.1f}{flag}")

    # ---- fruits-channel decomposition ----
    print("\n--- channel check: fruits gap x 8 vs D_s ---")
    FG = [load("emca_v25c", s)["tree_fruits"] - load("emca_v21", s)["tree_fruits"]
          for s in SEEDS]
    cov = sum((f * 8 - mD) * (d - mD) for f, d in zip(FG, D)) if False else None
    # correlation between fruits-gap*8 and D
    mf = mean([f * 8 for f in FG])
    num = sum((f * 8 - mf) * (d - mD) for f, d in zip(FG, D))
    den = math.sqrt(sum((f * 8 - mf) ** 2 for f in FG) *
                    sum((d - mD) ** 2 for d in D))
    print(f"  corr(fruits_gap*8, D) = {num/den:.3f}")
    print(f"  mean fruits gap x 8 = {mf:+.1f} vs mean D = {mD:+.1f}")

    # ---- secondary contrasts ----
    for name, A, B in [("D2 = v2.5c - nocausal", "emca_v25c", "emca_nocausal"),
                       ("D3 = v2.1 - nocausal", "emca_v21", "emca_nocausal")]:
        xs = [load(A, s)["total_reward"] - load(B, s)["total_reward"]
              for s in SEEDS]
        l2, h2 = bootstrap_ci(xs)
        p2, pos2, neg2 = sign_test(xs)
        print(f"\n--- {name} ---")
        print(f"  mean = {mean(xs):+.1f}, CI [{l2:+.1f}, {h2:+.1f}], "
              f"sign p = {p2:.4f} ({pos2}+/{neg2}-)")

    # ---- identifier control (T5 at 15 seeds) ----
    print("\n--- identifier control ---")
    dec21 = sum(1 for s in SEEDS if load("emca_v21", s)["decoy_in_causal"])
    dec25 = sum(1 for s in SEEDS if load("emca_v25c", s)["decoy_in_causal"])
    true25 = sum(1 for s in SEEDS if all(
        load("emca_v25c", s)["true_in_causal"].values()) for s in SEEDS)
    decassoc = sum(1 for s in SEEDS if load("emca_v25c", s)["decoy_in_assoc"])
    print(f"  decoy in v2.1 causal: {dec21}/15 (prereg floor >=10/12)")
    print(f"  decoy in v2.5c causal: {dec25}/15 (prereg 0)")
    print(f"  decoy in v2.5c assoc: {decassoc}/15 (the trap still baits "
          f"the correlational layer)")
    print(f"  all true edges in v2.5c: {true25}/15")

    # ---- v21 vs v22 identity ----
    print("\n--- v2.1 vs v2.2 identity (was 3/3 identical at turn 103) ---")
    diff = []
    for s in SEEDS:
        a = load("emca_v21", s)
        b = load("emca_v22", s)
        if a["total_reward"] != b["total_reward"]:
            diff.append((s, a["total_reward"] - b["total_reward"]))
    print(f"  seeds where v2.1 != v2.2: {len(diff)}/15 -> {diff}")
    print("  (the turn-103 identity was a seeds-1-3 coincidence, not a law)")

    # ---- prober and chain at 15 seeds ----
    print("\n--- prober / curious_chain at 15 seeds ---")
    causal_count = sum(1 for s in SEEDS
                       if load("prober", s)["altar_edge_in_causal"])
    p_rw = [load("prober", s)["total_reward"] for s in SEEDS]
    off = [load("prober", s)["offerings_paid"] for s in SEEDS]
    print(f"  prober altar CAUSAL: {causal_count}/15; reward "
          f"{mean(p_rw):.1f}; offerings {mean(off):.0f}")
    tz = [load("curious_chain", s)["treasures"] for s in SEEDS]
    de = [load("curious_chain", s)["deaths"] for s in SEEDS]
    print(f"  curious_chain treasures {mean(tz):.1f} "
          f"(range {min(tz):.0f}-{max(tz):.0f}), deaths {mean(de):.1f}")
    other_tz = []
    for arm in ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal", "prober"]:
        other_tz += [load(arm, s)["treasures"] for s in SEEDS]
    print(f"  all other arms treasures: max {max(other_tz):.0f} "
          f"over {len(other_tz)} runs")

    print("\nDONE")


if __name__ == "__main__":
    main()
