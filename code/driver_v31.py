"""Matrix driver for TerrariumV31 (the actionable-decoy env):
8 conditions x 3 seeds x 16000 steps.

Conditions:
  emca_v21      - pooled identifier + v3.1 goals (BELIEVES the decoy)
  emca_v22      - spec-gated identifier + v3.1 goals (BELIEVES the decoy)
  emca_v25c     - stratified RR identifier + v3.1 goals (REJECTS the decoy)
  emca_nocausal - assoc-only + v3.1 goals (correlation control)
  curious       - stratified RR + novelty generator (direction 3)
  random / qlearn / ngram - baselines

Run: python3 driver_v31.py
"""
import os
import subprocess
import sys

CONDITIONS = ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
              "curious", "random", "qlearn", "ngram"]
SEEDS = [1, 2, 3]
STEPS = 16000
TIMEOUT = 3600


def main():
    os.makedirs("results/matrix_v31", exist_ok=True)
    failures = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            out = f"results/matrix_v31/{cond}_{seed}.json"
            if os.path.exists(out):
                print(f"skip {out} (exists)")
                continue
            cmd = [sys.executable, "run_life_v31.py", cond, str(seed),
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
    print("MATRIX_V31_DONE failures=", len(failures))
    for f in failures:
        print("  ", f)


if __name__ == "__main__":
    main()
