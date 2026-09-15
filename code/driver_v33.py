"""Matrix driver for TerrariumV33 (scarcity + dynamic costs + chain):
11 conditions x 3 seeds x 16000 steps.

Conditions:
  emca_v21      - pooled identifier + v3.3 scarcity goals (BELIEVES)
  emca_v22      - spec-gated identifier + v3.3 scarcity goals (BELIEVES)
  emca_v25c     - stratified RR identifier + v3.3 scarcity goals (REJECTS)
  emca_nocausal - assoc-only + v3.3 scarcity goals (correlation control)
  prober        - v2.5c + do-interventions (offering-priced)
  curious_pure  - v2.5c + REACHABLE pure novelty (scarcity ablation)
  curious_surv  - v2.5c + novelty + survival arbiter (scarcity test)
  curious_chain - v2.5c + object-directed novelty (the chain arm)
  random / qlearn / ngram - baselines

PRE-REGISTERED MATRIX CRITERIA (before the first matrix run; the toy
W1-W8 ran at 8000 steps on 2026-09-10: W1/W3/W4/W6/W7/W8 PASS,
W2/W5 honest FAIL-as-prediction -- the belief still paid 2/3 seeds
because its grasps are competent, and curious_surv's dominance was
partial. The matrix criteria below are written to MEASURE, not to
wish: where the toy failed a prediction, the criterion asks the
question neutrally at the full scale.)

  T1 SCARCITY BITES (task 1, neutral): per-seed v2.5c deaths at 16000
     steps <= 45 in >=2/3 seeds (survivable but harder than v3.2's 22);
     AND the deficit is real: v3.3 v2.5c fruits < v3.2 v2.5c fruits
     (means: 2508 -> expected lower under the 60-fruit cap and 18/fruit)
  T2 THE PRICE OF THE FALSE BELIEF (task 1, the honest question):
     report per-seed v2.1 - v2.5c reward; the criterion is NOT a sign
     (the toy showed the sign is geometry-dependent) but a DECOMPOSITION:
     the believer's grasp@bell_no_tree count and grasp_costs_paid must
     be measured and reported; PASS if the decomposition attributes the
     gap to measured channels (fruit harvest difference), not to noise.
  T3 PROBER UNDER THE OFFERING (task 1): prober reaches a verdict on
     the altar edge in >=2/3 seeds; verdict CAUSAL in >=2/3 of those
     (the v3.2 limit was power ~55%; the offering prices trials now --
     if the verdict rate collapses, the experiment became unaffordable);
     prober deaths <= 45 in >=2/3 seeds (the offering must not kill it)
  T4 CHAIN FROM CURIOSITY (task 2): curious_chain treasures >= 1 in
     >=2/3 seeds at 16000 steps (the toy: 9/5/10 at 8000); AND
     curious_chain treasures > every other arm's treasures (the goal
     arms' chain machinery must not beat object-directed novelty);
     AND curious_chain deaths <= 40 in >=2/3 (novelty must not starve)
  T5 IDENTIFIER STABILITY (control): decoy in v2.1 causal >=2/3, NOT
     in v2.5c >=2/3; true edges in v2.5c >=2/3
  T6 BASELINES (control): random/qlearn/ngram die more than every
     planner/curious arm
  Determinism: fresh re-runs bit-identical for 3 conditions.

Run: python3 driver_v33.py
"""
import os
import subprocess
import sys

CONDITIONS = ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
              "prober", "curious_pure", "curious_surv", "curious_chain",
              "random", "qlearn", "ngram"]
SEEDS = [1, 2, 3]
STEPS = 16000
TIMEOUT = 3600


def main():
    os.makedirs("results/matrix_v33", exist_ok=True)
    failures = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            out = f"results/matrix_v33/{cond}_{seed}.json"
            if os.path.exists(out):
                print(f"skip {out} (exists)")
                continue
            cmd = [sys.executable, "run_life_v33.py", cond, str(seed),
                   str(STEPS)]
            try:
                p = subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=TIMEOUT,
                                   cwd=os.path.dirname(
                                       os.path.abspath(__file__)) or ".")
                if p.returncode != 0:
                    failures.append((cond, seed, p.returncode, p.stderr[-500:]))
                    print(f"FAIL {cond} {seed} rc={p.returncode}\n"
                          f"{p.stderr[-500:]}")
                else:
                    print(f"ok   {cond} {seed}")
            except subprocess.TimeoutExpired:
                failures.append((cond, seed, "timeout", ""))
                print(f"TIMEOUT {cond} {seed}")
    print("MATRIX_V33_DONE failures=", len(failures))
    for f in failures:
        print("  ", f)


if __name__ == "__main__":
    main()
