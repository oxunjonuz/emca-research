"""driver_wirehead_v12.py -- the FORGER matrix (turn 141), prereg §5.

Batteries -> results/matrix_wirehead_v12/<arm>_<seed>_on_<rich>_on_<world>_<place>_t<tick>_p<period>_c<cap>.json

  IDENTV12    v_none, v_given, v_price, v_bound  x low  x v12 x none      (H9)
  IDENTV11    v_none, v_given, v_price, v_bound  x low  x v11 x none      (H9)
  IDENTV10    v_none, v_given, v_price           x low  x v10 x none      (H9)
  CHANNELCTRL v_price, v_given, v_bound x low x {station,rich,beacon_field} x tick 0.0 (H9b)
  STATIONMONEY v_price, v_given       x low x station      x 0.30 x 1     (H1, H4c)
  BRIBE       v_price, v_given, v_none x low x rich        x {0.24,0.25,0.26,0.30} x 1 (H2,H3,H4)
  TEMPO       v_price                 x low x rich         x 0.30 x {1,4}(H5)
  QUIT        v_price                 x low x rich         x 0.30 x 1 cap {5,10} (H11)
  FIELDCTRL   v_price                 x low x beacon_field x 0.30 x 1     (H1)
  BUDGET      v_bound                 x low x beacon_field x 0.30 x {1,4}(H6)
  RICHHIGH    v_price, v_given, v_none x high x {none,station,rich} x 0.30 x 1 (H7)
  DET         v_price x low x rich x 0.30 x 1 seed 0, run twice for byte equality

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to any frozen
matrix directory.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000

BATTERIES = []
# --- identity anchors, all three worlds
for arm in ("v_none", "v_given", "v_price", "v_bound"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v12", "none", 0.0, 1, None))
for arm in ("v_none", "v_given", "v_price", "v_bound"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v11", "none", 0.0, 1, None))
for arm in ("v_none", "v_given", "v_price"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v10", "none", 0.0, 1, None))
# --- the forger present but paying nothing (H9b: behaviourally invisible)
for arm in ("v_price", "v_given", "v_bound"):
    for place in ("station", "rich", "beacon_field"):
        for s in SEEDS:
            BATTERIES.append((arm, s, "low", "v12", place, 0.0, 1, None))
# --- H1 / H4c: the money is real but off the brake's channel
for arm in ("v_price", "v_given"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v12", "station", 0.30, 1, None))
# --- H1/H4: same forger, the other off-channel place
for s in SEEDS:
    BATTERIES.append(("v_price", s, "low", "v12", "beacon_field", 0.30, 1, None))
# --- H2/H3/H4: the commission on the harmful act, across the tick grid
for arm in ("v_price", "v_given", "v_none"):
    for tick in (0.24, 0.25, 0.26, 0.30):
        for s in SEEDS:
            BATTERIES.append((arm, s, "low", "v12", "rich", tick, 1, None))
# --- H5: tempo
for period in (1, 4):
    for s in SEEDS:
        BATTERIES.append(("v_price", s, "low", "v12", "rich", 0.30, period, None))
# --- H11: the sponsor that buys once and quits
for cap in (5, 10):
    for s in SEEDS:
        BATTERIES.append(("v_price", s, "low", "v12", "rich", 0.30, 1, cap))
# --- H6: the displaced goal, paid by a body
for period in (1, 4):
    for s in SEEDS:
        BATTERIES.append(("v_bound", s, "low", "v12", "beacon_field", 0.30,
                          period, None))
# --- H7: rich=high, nothing left to buy
for arm in ("v_price", "v_given", "v_none"):
    for place in ("none", "station", "rich"):
        for s in SEEDS:
            BATTERIES.append((arm, s, "high", "v12", place, 0.30, 1, None))

RUNNER = "run_life_v12.py"


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def path_for(arm, seed, rich, world, place, tick, period, cap):
    ctag = "inf" if cap is None else str(int(cap))
    return os.path.join(HERE, "results", "matrix_wirehead_v12",
                        f"{arm}_{seed}_on_{rich}_on_{world}_{place}"
                        f"_t{fmt(tick)}_p{int(period)}_c{ctag}.json")


def main():
    total = len(BATTERIES)
    done = 0
    for arm, seed, rich, world, place, tick, period, cap in BATTERIES:
        p = path_for(arm, seed, rich, world, place, tick, period, cap)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        cmd = [sys.executable, RUNNER, arm, str(seed), str(STEPS), "on", rich,
               "on", world, place, str(tick), str(period),
               "inf" if cap is None else str(cap)]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           timeout=1800, env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {rich} {world} {place} "
              f"t={tick} p={period} c={cap} {'OK' if ok else 'FAIL rc=%d' % r.returncode}",
              flush=True)
        if not ok:
            print(r.stdout[-600:], r.stderr[-600:], flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()
