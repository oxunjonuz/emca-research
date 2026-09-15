"""Driver for the V5 matrix: 8 arms x 10 seeds x 16000 steps.
Sequential; each run writes results/matrix_v5/<arm>_<seed>.json.
Existing files are skipped (resumable)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ["v5_believer", "v5_spec", "v5_assoc", "v5_assoc02",
        "v5_rejector", "random", "qlearn", "ngram"]
SEEDS = list(range(1, 11))
STEPS = 16000

for arm in ARMS:
    for seed in SEEDS:
        path = os.path.join(HERE, "results", "matrix_v5",
                            f"{arm}_{seed}.json")
        if os.path.exists(path) and os.path.getsize(path) > 2000:
            print("skip", arm, seed)
            continue
        r = subprocess.run(
            [sys.executable, "run_life_v5.py", arm, str(seed),
             str(STEPS)],
            cwd=HERE, capture_output=True, text=True, timeout=900)
        ok = os.path.exists(path) and os.path.getsize(path) > 2000
        print(arm, seed, "OK" if ok else f"FAIL rc={r.returncode}",
              flush=True)
        if not ok:
            print(r.stdout[-500:], r.stderr[-500:])
