"""Full experiment matrix driver v2: 10 conditions x 3 seeds x 6000 steps.

Conditions (identifier version explicit, TZ.md rule):
  emca           - EMCA v2.2 (spec-gated contrast)
  emca_v21       - EMCA with spec gate OFF (v2.1 pooled contrast) -- the
                   identifier A/B arm on the SAME environment
  emca_amnesia / emca_nocausal / emca_noepis / emca_nogoals / emca_noself
  random / qlearn / ngram

Each run is a subprocess with a hard timeout. Results -> results/matrix_v2/
Run: python3 driver_v2.py
"""
import os
import subprocess
import sys

CONDITIONS = ["emca", "emca_v21", "emca_amnesia", "emca_nocausal", "emca_noepis",
              "emca_nogoals", "emca_noself", "random", "qlearn", "ngram"]
SEEDS = [1, 2, 3]
STEPS = 6000
TIMEOUT = 600

def main():
    os.makedirs("results/matrix_v2", exist_ok=True)
    failures = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            out = f"results/matrix_v2/{cond}_{seed}.json"
            if os.path.exists(out):
                print(f"skip {out} (exists)")
                continue
            cmd = [sys.executable, "run_life_v2.py", cond, str(seed), str(STEPS)]
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
    print("MATRIX_V2_DONE failures=", len(failures))
    for f in failures:
        print("  ", f)

if __name__ == "__main__":
    main()
