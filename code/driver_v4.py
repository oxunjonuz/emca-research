"""Matrix driver for TerrariumV4: 9 conditions x 10 seeds x 16000.
Conditions per PREREG_V4.md. Run: python3 driver_v4.py"""
import os
import subprocess
import sys

CONDITIONS = ["v4_believer", "v4_spec", "v4_assoc", "v4_rejector",
              "v4_curious", "v4_pure", "random", "qlearn", "ngram"]
SEEDS = list(range(1, 11))
STEPS = 16000
TIMEOUT = 3600


def main():
    os.makedirs("results/matrix_v4", exist_ok=True)
    failures = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            out = f"results/matrix_v4/{cond}_{seed}.json"
            if os.path.exists(out):
                print(f"skip {out} (exists)")
                continue
            cmd = [sys.executable, "run_life_v4.py", cond, str(seed),
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
    print("MATRIX_V4_DONE failures=", len(failures))
    for f in failures:
        print("  ", f)


if __name__ == "__main__":
    main()
