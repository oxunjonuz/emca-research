"""driver_scope_v16.py -- the SCOPE matrix (turn 149), prereg §4.

Batteries -> results/matrix_scope_v16/<arm>_<seed>_on_<rich>_on_v12_<place>_t<tick>_p1_cinf.json

  ANCHORS   w_none,w_price,w_given x 10 seeds x none x t0     (H1: v12 identity)
  SEARCH    {w_price, n_pump_price, n_doctor, n_doctor_price}
            x 3 places {station,rich,beacon_field} x 4 ticks {0.24,0.25,0.26,0.30}
            x 10 seeds                                        (H2,H3,H4,H5,H8)
  WIDECONTROL w_none,w_given x 3 places x 4 ticks x 10 seeds  (H7,H8 wide surface)
  NOFORGER  n_pump,n_pump_price,n_doctor,n_doctor_price x 10 seeds x none
            (the scope arms' own baseline, no third party)     (H7)
  DET       n_pump_price seed 0 rich t0.30 run twice for byte equality

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to any frozen
matrix directory.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000
PLACES = ("station", "rich", "beacon_field")
TICKS = (0.24, 0.25, 0.26, 0.30)

BATTERIES = []
for arm in ("w_none", "w_price", "w_given"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "none", 0.0))
for arm in ("w_price", "n_pump_price", "n_doctor", "n_doctor_price"):
    for place in PLACES:
        for tick in TICKS:
            for s in SEEDS:
                BATTERIES.append((arm, s, place, tick))
for arm in ("w_none", "w_given"):
    for place in PLACES:
        for tick in TICKS:
            for s in SEEDS:
                BATTERIES.append((arm, s, place, tick))
for arm in ("n_pump", "n_pump_price", "n_doctor", "n_doctor_price"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "none", 0.0))

RUNNER = "run_life_v16.py"


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def path_for(arm, seed, place, tick):
    return os.path.join(HERE, "results", "matrix_scope_v16",
                        f"{arm}_{seed}_on_low_on_v12_{place}"
                        f"_t{fmt(tick)}_p1_cinf.json")


def main():
    total = len(BATTERIES)
    done = 0
    for arm, seed, place, tick in BATTERIES:
        p = path_for(arm, seed, place, tick)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        cmd = [sys.executable, RUNNER, arm, str(seed), str(STEPS), "on", "low",
               "on", "v12", place, str(tick), "1", "inf"]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           timeout=1800, env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {place} t={tick} "
              f"{'OK' if ok else 'FAIL rc=%d' % r.returncode}", flush=True)
        if not ok:
            print(r.stdout[-600:], r.stderr[-600:], flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()