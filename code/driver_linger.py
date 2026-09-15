"""Matrix driver for the SIMPLE linger env: 7 conditions x 3 seeds x 16000.

Conditions (identifier version explicit, TZ.md rule):
  emca_v21      - pooled contrast (spec OFF) -- the OLD way
  emca_v22      - pooled + specificity gate -- the v2-matrix way
  emca_v25c     - stratified + RR>=2 + door_gone data fix -- the NEW way
  emca_nocausal - assoc-only control
  random / qlearn / ngram - baselines
Run: python3 driver_linger.py
"""
import os
import subprocess
import sys

CONDITIONS = ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
              "random", "qlearn", "ngram"]
SEEDS = [1, 2, 3]
STEPS = 16000
TIMEOUT = 900


def main():
    os.makedirs("results/matrix_linger", exist_ok=True)
    failures = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            out = f"results/matrix_linger/{cond}_{seed}.json"
            if os.path.exists(out):
                print(f"skip {out} (exists)")
                continue
            cmd = [sys.executable, "run_life_linger.py", cond, str(seed),
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
    print("MATRIX_LINGER_DONE failures=", len(failures))
    for f in failures:
        print("  ", f)


if __name__ == "__main__":
    main()
