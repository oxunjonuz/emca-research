"""Driver for the V7 matrix (PREREG_V7 §4.4).

Batteries (each run writes results/matrix_v7/<arm>_<seed>_<truth>_<rich>_<decoy>.json):
  BASE     -- all 7 arms x 10 seeds, truth=on  rich=low  decoy=on
  CONFLICT -- v7_full, v7_beta0, v7_perm x 10 seeds, truth=on rich=high decoy=on
              (C1: the permitted alternative pays 0.60/step -- does the
               computed arbiter still probe? does beta0 stop?)
  OFF      -- v7_full x 10 seeds, truth=off rich=low decoy=on
              (C2: no nomination off; C3: no false-positive CAUSAL)

Sequential, resumable (existing non-trivial files skipped), PYTHONHASHSEED
pinned to 0 for bit-reproducibility (the turn-115 lesson).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000
BASE_ARMS = ["v7_full", "v7_beta0", "v7_perm", "v7_nogen", "v7_oracle",
             "v7_forager", "v7_random"]

BATTERIES = []
for arm in BASE_ARMS:
    for seed in SEEDS:
        BATTERIES.append((arm, seed, "on", "low", "on"))
for arm in ("v7_full", "v7_beta0", "v7_perm"):
    for seed in SEEDS:
        BATTERIES.append((arm, seed, "on", "high", "on"))
for seed in SEEDS:
    BATTERIES.append(("v7_full", seed, "off", "low", "on"))


def path_for(arm, seed, truth, rich, decoy):
    return os.path.join(HERE, "results", "matrix_v7",
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
            [sys.executable, "run_life_v7.py", arm, str(seed), str(STEPS),
             truth, rich, decoy],
            cwd=HERE, capture_output=True, text=True, timeout=1800,
            env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {truth} {rich} {decoy} "
              f"{'OK' if ok else f'FAIL rc={r.returncode}'}", flush=True)
        if not ok:
            print(r.stdout[-400:], r.stderr[-400:], flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()
