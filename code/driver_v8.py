"""driver_v8.py -- the V8 matrix (PREREG_V8 §4).

Batteries (each run writes results/matrix_v8/<tag>.json):
  C      graded, graded1, threshold, thresholdpool, coin, oracle, rot
         x gaps {0.20,0.10,0.05,0.03} x 8 seeds, q=0, persistence off
  C-tau  graded_t07, graded_t03 at gap 0.10 x 8 seeds
  A      graded, rot x gaps {0.20,0.10} x 8 seeds, persistence ON
  A-null graded, gap 0.10, truth=off, persistence off and on x 10 seeds
  F      f_fresh, f_carry, oracle x q {0,0.25,0.5,0.75,1.0} x 8 seeds,
         gap 0.10

Sequential-resumable; PYTHONHASHSEED pinned to 0 (the turn-115 lesson).
Existing non-trivial files are skipped, so a re-run after a crash resumes.
"""
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = 16000
SEEDS8 = list(range(8))
SEEDS10 = list(range(10))
GAPS = ["0.20", "0.10", "0.05", "0.03"]


def tag(arm, seed, gap, q, persist, truth):
    return (f"{arm}_s{seed}_g{gap}_q{q}_{'p' if persist else 'n'}"
            f"_{'on' if truth else 'off'}")


def build():
    jobs = []
    for arm in ("graded", "graded1", "threshold", "thresholdpool", "coin",
                "oracle", "rot"):
        for gap in GAPS:
            for s in SEEDS8:
                jobs.append((arm, s, gap, 0.0, False, True))
    for arm in ("graded_t07", "graded_t03"):
        for s in SEEDS8:
            jobs.append((arm, s, "0.10", 0.0, False, True))
    for arm in ("graded", "rot"):
        for gap in ("0.20", "0.10"):
            for s in SEEDS8:
                jobs.append((arm, s, gap, 0.0, True, True))
    for persist in (False, True):
        for s in SEEDS10:
            jobs.append(("graded", s, "0.10", 0.0, persist, False))
    for arm in ("f_fresh", "f_carry", "oracle"):
        for q in (0.0, 0.25, 0.5, 0.75, 1.0):
            for s in SEEDS8:
                jobs.append((arm, s, "0.10", q, False, True))
    # de-duplicate (A's persistence-off rows are Block C's rows already)
    seen = set()
    out = []
    for j in jobs:
        k = tag(*j)
        if k in seen:
            continue
        seen.add(k)
        out.append(j)
    return out


def path_for(arm, seed, gap, q, persist, truth):
    return os.path.join(HERE, "results", "matrix_v8",
                        tag(arm, seed, gap, q, persist, truth) + ".json")


def one(job):
    arm, seed, gap, q, persist, truth = job
    p = path_for(*job)
    if os.path.exists(p) and os.path.getsize(p) > 200:
        return (tag(*job), "skip")
    r = subprocess.run(
        [sys.executable, "run_life_v8.py", arm, str(seed), gap, str(q),
         "on" if persist else "off", "on" if truth else "off", str(STEPS)],
        cwd=HERE, capture_output=True, text=True, timeout=900,
        env={**os.environ, "PYTHONHASHSEED": "0"})
    ok = os.path.exists(p) and os.path.getsize(p) > 200
    if not ok:
        return (tag(*job), f"FAIL rc={r.returncode} {r.stderr[-200:]}")
    return (tag(*job), "OK")


def main():
    jobs = build()
    done = 0
    with ProcessPoolExecutor(max_workers=8) as ex:
        for t, st in ex.map(one, jobs):
            done += 1
            if st != "skip":
                print(f"[{done}/{len(jobs)}] {t} {st}", flush=True)
    print(f"DONE {done}/{len(jobs)}", flush=True)


if __name__ == "__main__":
    main()
