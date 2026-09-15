"""Matrix driver for TerrariumV32 (separated geometry + altar):
10 conditions x 3 seeds x 16000 steps.

Conditions:
  emca_v21      - pooled identifier + v3.2 goals (BELIEVES the decoy)
  emca_v22      - spec-gated identifier + v3.2 goals (BELIEVES the decoy)
  emca_v25c     - stratified RR identifier + v3.2 goals (REJECTS the decoy)
  emca_nocausal - assoc-only + v3.2 goals (correlation control)
  prober        - v2.5c + do-interventions (gray-zone active experiments)
  curious_pure  - v2.5c + REACHABLE pure novelty (turn-100 correction)
  curious_surv  - v2.5c + novelty + survival arbiter + storm competence
  random / qlearn / ngram - baselines

PRE-REGISTERED MATRIX CRITERIA (before the first matrix run; the toy
W1-W9 passed at 8000 steps on 2026-09-09):

  T1 SIGN INVERSION (task 1, the owner's prediction): v2.5c reward >=
     v2.1 reward per seed in >=2/3 seeds at 16000 steps (turn-100:
     the false belief PAID; the separated geometry should invert)
  T2 PROBER (task 2): the prober reaches a verdict on the altar edge
     (wait, patch_berry) in >=2/3 seeds; verdict CAUSAL in >=2/3 of
     those; the altar edge enters the prober's causal_edges iff the
     verdict is CAUSAL (verdict gating works); passive v2.5c does NOT
     have the altar edge (the passive layer cannot see it -- the
     sprout lands after the wait, alignment broken by the move)
  T3 CURIOUS-SURVIVOR (task 3): curious_surv deaths < curious_pure
     deaths in 3/3 seeds; curious_surv deaths <= 20 in >=2/3 seeds;
     curious_surv novelty_transitions >= 0.5 * curious_pure in 3/3
     (survival without losing most of the exploration)
  T4 TRUE EDGES: press->lever, eat->ate, grasp->tree_gather in v2.5c
     in >=2/3 seeds; the decoy (grasp, bell_rang) in v2.1 causal in
     >=2/3 seeds and NOT in v2.5c in >=2/3 seeds
  T5 baselines: random/qlearn/ngram die more than every planner arm
     (the competence gap survives the harsher world)

Run: python3 driver_v32.py
"""
import os
import subprocess
import sys

CONDITIONS = ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
              "prober", "curious_pure", "curious_surv",
              "random", "qlearn", "ngram"]
SEEDS = [1, 2, 3]
STEPS = 16000
TIMEOUT = 3600


def main():
    os.makedirs("results/matrix_v32", exist_ok=True)
    failures = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            out = f"results/matrix_v32/{cond}_{seed}.json"
            if os.path.exists(out):
                print(f"skip {out} (exists)")
                continue
            cmd = [sys.executable, "run_life_v32.py", cond, str(seed),
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
    print("MATRIX_V32_DONE failures=", len(failures))
    for f in failures:
        print("  ", f)


if __name__ == "__main__":
    main()
