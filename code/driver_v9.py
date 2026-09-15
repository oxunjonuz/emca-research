"""Driver for the V9 matrix (PREREG_V9 §2).

Batteries (each run writes
results/matrix_v9/<arm>_<seed>_<truth>_<rich>_<decoy>.json):
  BASE     -- 9 arms x 10 seeds, truth=on  rich=low  decoy=on
  CONFLICT -- 6 arms x 10 seeds, truth=on  rich=high decoy=on
  OFF      -- 3 arms x 10 seeds, truth=off rich=low  decoy=on

Sequential, resumable, PYTHONHASHSEED pinned to 0 (the turn-115 lesson).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000
BASE_ARMS = ["v9_union", "v9_stop", "v9_noexp", "v9_noctx", "v9_fixed",
             "v9_old", "v9_oracle", "v9_forager", "v9_random"]
CONFLICT_ARMS = ["v9_union", "v9_stop", "v9_noexp", "v9_noctx", "v9_fixed",
                 "v9_old"]
OFF_ARMS = ["v9_union", "v9_fixed", "v9_old"]

BATTERIES = []
for arm in BASE_ARMS:
    for seed in SEEDS:
        BATTERIES.append((arm, seed, "on", "low", "on"))
for arm in CONFLICT_ARMS:
    for seed in SEEDS:
        BATTERIES.append((arm, seed, "on", "high", "on"))
for arm in OFF_ARMS:
    for seed in SEEDS:
        BATTERIES.append((arm, seed, "off", "low", "on"))


def path_for(arm, seed, truth, rich, decoy):
    return os.path.join(HERE, "results", "matrix_v9",
                        f"{arm}_{seed}_{truth}_{rich}_{decoy}.json")


def main():
    total = len(BATTERIES)
    done = 0
    for arm, seed, truth, rich, decoy in BATTERIES:
        p = path_for(arm, seed, truth, rich, decoy)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            print(f"skip {arm} {seed} {truth} {rich} {decoy}", flush=True)
            continue
        r = subprocess.run(
            [sys.executable, "run_life_v9.py", arm, str(seed), str(STEPS),
             truth, rich, decoy],
            cwd=HERE, capture_output=True, text=True, timeout=1800,
            env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {truth} {rich} {decoy} "
              f"{'OK' if ok else 'FAIL rc=%s' % r.returncode}", flush=True)
        if not ok:
            print(r.stdout[-400:], r.stderr[-400:], flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()
