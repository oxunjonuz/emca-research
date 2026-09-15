"""Driver for the V6 matrix: 8 arms x 10 seeds x 16000 steps.
Sequential; each run writes results/matrix_v6/<arm>_<seed>.json.
Existing files are skipped (resumable). PYTHONHASHSEED is pinned (the
turn-115 determinism find: the campaign's _scent_step_smart broke ties
by string-hash order; the fix makes runs hash-stable, and the pin makes
them bit-reproducible)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ["v6_prober", "v6_oracle", "v6_rejector", "v6_assoc02",
        "v6_assoc", "v6_believer", "v6_nocausal", "random"]
SEEDS = list(range(1, 11))
STEPS = 16000

for arm in ARMS:
    for seed in SEEDS:
        path = os.path.join(HERE, "results", "matrix_v6",
                            f"{arm}_{seed}.json")
        if os.path.exists(path) and os.path.getsize(path) > 2000:
            print("skip", arm, seed)
            continue
        r = subprocess.run(
            [sys.executable, "run_life_v6.py", arm, str(seed),
             str(STEPS)],
            cwd=HERE, capture_output=True, text=True, timeout=1800,
            env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(path) and os.path.getsize(path) > 2000
        print(arm, seed, "OK" if ok else f"FAIL rc={r.returncode}",
              flush=True)
        if not ok:
            print(r.stdout[-500:], r.stderr[-500:])
