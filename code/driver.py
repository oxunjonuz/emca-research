"""Full experiment matrix driver: 8 conditions x 3 seeds x 6000 steps.

Each run is a subprocess with a hard timeout (lesson from the mruby campaign:
never let one run hang the parent). Results -> results/matrix/<cond>_<seed>.json
Run: python3 driver.py
"""
import json
import os
import subprocess
import sys

CONDITIONS = ["emca", "emca_amnesia", "emca_nocausal", "emca_noepis", "emca_nogoals",
              "emca_noself", "random", "qlearn", "ngram"]
SEEDS = [1, 2, 3]
STEPS = 6000
TIMEOUT = 300

def main():
    os.makedirs("results/matrix", exist_ok=True)
    failures = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            out = f"results/matrix/{cond}_{seed}.json"
            if os.path.exists(out):
                print(f"skip {out} (exists)")
                continue
            cmd = [sys.executable, "run_life.py", cond, str(seed), str(STEPS)]
            try:
                p = subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=TIMEOUT, cwd=os.path.dirname(
                                       os.path.abspath(__file__)) or ".")
                if p.returncode != 0:
                    failures.append((cond, seed, p.returncode, p.stderr[-500:]))
                    print(f"FAIL {cond} {seed} rc={p.returncode}\n{p.stderr[-500:]}")
                else:
                    print(f"ok   {cond} {seed}")
            except subprocess.TimeoutExpired:
                failures.append((cond, seed, "timeout", ""))
                print(f"TIMEOUT {cond} {seed}")
    print("MATRIX_DONE failures=", len(failures))
    for f in failures:
        print("  ", f)

if __name__ == "__main__":
    main()
