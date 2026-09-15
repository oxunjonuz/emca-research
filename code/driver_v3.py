"""Matrix driver for the COMPLEX env (TerrariumV3): 7 conditions x 3 seeds
x 16000 steps. The linger trap embedded in the full world (chain, rare
events, survival, regime flip). Same conditions and scale as the simple
env's matrix (driver_linger.py) so the two are directly comparable.

Run: python3 driver_v3.py
"""
import os
import subprocess
import sys

CONDITIONS = ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
              "random", "qlearn", "ngram"]
SEEDS = [1, 2, 3]
STEPS = 16000
TIMEOUT = 1800


def main():
    os.makedirs("results/matrix_v3", exist_ok=True)
    failures = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            out = f"results/matrix_v3/{cond}_{seed}.json"
            if os.path.exists(out):
                print(f"skip {out} (exists)")
                continue
            cmd = [sys.executable, "run_life_v3.py", cond, str(seed),
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
    print("MATRIX_V3_DONE failures=", len(failures))
    for f in failures:
        print("  ", f)


if __name__ == "__main__":
    main()