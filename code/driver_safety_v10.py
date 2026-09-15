"""driver_safety_v10.py -- the safety matrix (turn 139), prereg §5 + §7.

Batteries -> results/matrix_safety_v10/<arm>_<seed>_<truth>_<rich>_<decoy>_<world>[_c<coupling>].json
  BASE       9 arms x 10 seeds, truth=on rich=low  decoy=on, world=v10, c=0
  CONFLICT   9 arms x 10 seeds, truth=on rich=high decoy=on, world=v10, c=0
  NOAQUIFER  3 arms x 10 seeds, truth=on rich=low  decoy=on, world=v7
  RESPONSIVE 6 arms x 10 seeds x {low,high}, world=v10, coupling=1

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to
results/matrix_v7 (frozen).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000
ARMS = ["s0_nobrake", "s1_gauge_ignored", "s2_given_rule", "s3_victim_keyed",
        "s4_internalized", "s5_world_veto", "s_forager", "s_oldv7", "s_oracle"]
NOAQ_ARMS = ["s0_nobrake", "s1_gauge_ignored", "s_oldv7"]
RESP_ARMS = ["s0_nobrake", "s1_gauge_ignored", "s2_given_rule",
             "s3_victim_keyed", "s4_internalized", "s5_world_veto"]

BATTERIES = []
for arm in ARMS:
    for s in SEEDS:
        BATTERIES.append((arm, s, "on", "low", "on", "v10", 0))
for arm in ARMS:
    for s in SEEDS:
        BATTERIES.append((arm, s, "on", "high", "on", "v10", 0))
for arm in NOAQ_ARMS:
    for s in SEEDS:
        BATTERIES.append((arm, s, "on", "low", "on", "v7", 0))
for arm in RESP_ARMS:
    for rich in ("low", "high"):
        for s in SEEDS:
            BATTERIES.append((arm, s, "on", rich, "on", "v10", 1))


def path_for(arm, seed, truth, rich, decoy, world, coupling):
    ctag = "" if coupling == 0 else f"_c{coupling}"
    return os.path.join(HERE, "results", "matrix_safety_v10",
                        f"{arm}_{seed}_{truth}_{rich}_{decoy}_{world}{ctag}.json")


def main():
    total = len(BATTERIES)
    done = 0
    for arm, seed, truth, rich, decoy, world, coupling in BATTERIES:
        p = path_for(arm, seed, truth, rich, decoy, world, coupling)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        r = subprocess.run(
            [sys.executable, "run_life_v10.py", arm, str(seed), str(STEPS),
             truth, rich, decoy, world, str(coupling)],
            cwd=HERE, capture_output=True, text=True, timeout=1800,
            env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {rich} {world} c={coupling} "
              f"{'OK' if ok else f'FAIL rc={r.returncode}'}", flush=True)
        if not ok:
            print(r.stdout[-500:], r.stderr[-500:], flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()