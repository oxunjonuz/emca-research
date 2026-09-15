"""driver_enforced_v18.py -- the ENFORCED-SCOPE matrix (turn 152), prereg §4.

Batteries -> results/matrix_enforced_v18/<arm>_<seed>_on_low_on_v18_<place>_t<tick>_p1_cinf_<scope>_gw<gw>.json

  HE2anchor  w_none, w_price, n_doctor, n_pump_price x 10 seeds x rich x t0.30
             x scope=none                                  (identity vs v16/v12)
  HE1        w_price x 10 seeds x rich x t0.30 x scope=station x gw0   (refused)
  HE1c       w_widen x 10 seeds x rich x t0.30 x scope=station x gw0   (refused)
  HE1b       n_doctor x 10 seeds x rich x t0.30 x scope=station x gw0  (capability)
  HE3        n_pump_price x 10 seeds x rich x t0.30 x scope=rich x gw0 (inside)
  HE4        w_widen x 10 seeds x rich x t0.30 x scope=station x gw1   (granted)
  HE6        n_doctor x 10 seeds x none x t0.0  x scope=station x gw0  (no forger)
  NOSCOPE    w_widen x 10 seeds x rich x t0.30 x scope=none x gw0      (HE1 counter)
  DET        w_widen seed 0 rich t0.30 station gw0 run twice (byte eq)

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to any frozen
matrix directory.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000
RUNNER = "run_life_v18.py"
OUTDIR = os.path.join(HERE, "results", "matrix_enforced_v18")

# (arm, seed, place, tick, scope, grant_widen)
BATTERIES = []
# --- the no-enforcement anchors (identity against the frozen v16/v12 cells)
for arm in ("w_none", "w_price", "n_doctor", "n_pump_price", "w_widen"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "none", False))
# --- HE1: the world refuses the harm the agent wants
for arm in ("w_price", "w_widen"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "station", False))
# --- HE1b: the doctor (capability, not boundary)
for s in SEEDS:
    BATTERIES.append(("n_doctor", s, "rich", 0.30, "station", False))
# --- HE3: the harm INSIDE the granted scope
for s in SEEDS:
    BATTERIES.append(("n_pump_price", s, "rich", 0.30, "rich", False))
# --- HE4/HE5: the widening request, refused and granted
for arm in ("w_widen", "w_price"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "station", True))
# --- HE6: no forger, no reason to try
for s in SEEDS:
    BATTERIES.append(("n_doctor", s, "none", 0.0, "station", False))
for s in SEEDS:
    BATTERIES.append(("w_widen", s, "none", 0.0, "station", False))


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def path_for(arm, seed, place, tick, scope, gw):
    return os.path.join(OUTDIR,
                        f"{arm}_{seed}_on_low_on_v18_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{scope}_gw{int(bool(gw))}.json")


def main():
    total = len(BATTERIES)
    uniq = len({path_for(*b) for b in BATTERIES})
    print(f"BATTERIES {total} (unique cells {uniq})", flush=True)
    done = 0
    seen = set()
    for arm, seed, place, tick, scope, gw in BATTERIES:
        p = path_for(arm, seed, place, tick, scope, gw)
        seen.add(p)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        cmd = [sys.executable, RUNNER, arm, str(seed), str(STEPS), "on", "low",
               "on", "v18", place, str(tick), "1", "inf", scope, "1" if gw else "0"]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           timeout=1800,
                           env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {place} t={tick} scope={scope} "
              f"gw={int(bool(gw))} {'OK' if ok else 'FAIL rc=%d' % r.returncode}",
              flush=True)
        if not ok:
            print(r.stdout[-600:], r.stderr[-600:], flush=True)
    print("DONE", done, "/", total, "unique cells on disk:", len(seen), flush=True)


if __name__ == "__main__":
    main()