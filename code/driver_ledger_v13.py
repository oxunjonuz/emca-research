"""driver_ledger_v13.py -- the LEDGER matrix (turn 143), prereg §5.

Batteries -> results/matrix_ledger_v13/<arm>_<seed>_on_<rich>_on_<world>_<place>_t<tick>_p<period>_c<cap>_<tag>_wr<wr>.json

  IDENTV13    l_none, l_scalar, l_ledger   x low x v13 x none                    (H8)
  IDENTV13B   l_none, l_scalar, l_ledger   x low x v12 x none                    (H8)
  IDENTV13C   l_none, l_scalar             x low x v10 x none                    (H8)
  TAGNOOP     l_ledger                     x low x v13 x rich x tick 0.0         (H8)
  BRIBE13     l_scalar, l_ledger, l_infer, l_infer_min x low x v13 x rich x 0.30 x 1 x foreign (H1,H1b,H4)
  HONEST      l_scalar, l_ledger           x low x v13 x none x wr 0.35          (H2,H3)
  LYINGTAG    l_ledger                     x low x v13 x rich x 0.30 x 1 x world (H5)
  CROSSING13  l_scalar, l_ledger           x low x v13 x rich x {0.24,0.25,0.26,0.30} x 1 x foreign (H9)
  STATION13   l_ledger                     x low x v13 x station x 0.30 x 1 x foreign (H7)
  RICHHIGH13  l_ledger                     x low x v13 x none x 0.30 x 1 x foreign (H6)
  RICHHIGH13B l_ledger                     x high x v13 x {none,rich} x 0.30 x 1 x foreign (H6)
  DET         l_ledger x low x v13 x rich x 0.30 x 1 x foreign seed 0, run twice

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
# --- identity anchors, three worlds
for arm in ("l_none", "l_scalar", "l_ledger"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v13", "none", 0.0, 1, None, "foreign", None))
for arm in ("l_none", "l_scalar", "l_ledger"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v12", "none", 0.0, 1, None, "foreign", None))
for arm in ("l_none", "l_scalar"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v10", "none", 0.0, 1, None, "foreign", None))
# --- the tag is a no-op when the forger pays nothing (H8)
for s in SEEDS:
    BATTERIES.append(("l_ledger", s, "low", "v13", "rich", 0.0, 1, None, "foreign", None))
# --- H1/H1b/H4: the commission on the harmful act, tagged honestly
for arm in ("l_scalar", "l_ledger", "l_infer", "l_infer_min"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v13", "rich", 0.30, 1, None, "foreign", None))
# --- H2/H3: the honest raise (the world pays more, no third party)
for arm in ("l_scalar", "l_ledger"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v13", "none", 0.0, 1, None, "foreign", 0.35))
# --- H5: the lying tag
for s in SEEDS:
    BATTERIES.append(("l_ledger", s, "low", "v13", "rich", 0.30, 1, None, "world", None))
# --- H9: the crossing, flat under the ledger
for arm in ("l_scalar", "l_ledger"):
    for tick in (0.24, 0.25, 0.26, 0.30):
        for s in SEEDS:
            BATTERIES.append((arm, s, "low", "v13", "rich", tick, 1, None,
                              "foreign", None))
# --- H7: money off the channel
for s in SEEDS:
    BATTERIES.append(("l_ledger", s, "low", "v13", "station", 0.30, 1, None,
                      "foreign", None))
# --- H6: harm the world itself makes profitable
for s in SEEDS:
    BATTERIES.append(("l_ledger", s, "low", "v13", "none", 0.30, 1, None,
                      "foreign", None))
for arm in ("l_ledger",):
    for place in ("none", "rich"):
        for s in SEEDS:
            BATTERIES.append((arm, s, "high", "v13", place, 0.30, 1, None,
                              "foreign", None))

RUNNER = "run_life_v13.py"


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def path_for(arm, seed, rich, world, place, tick, period, cap, tag, wr):
    ctag = "inf" if cap is None else str(int(cap))
    wtag = "def" if wr is None else fmt(wr)
    return os.path.join(HERE, "results", "matrix_ledger_v13",
                        f"{arm}_{seed}_on_{rich}_on_{world}_{place}"
                        f"_t{fmt(tick)}_p{int(period)}_c{ctag}_{tag}_wr{wtag}.json")


def main():
    total = len(BATTERIES)
    done = 0
    for arm, seed, rich, world, place, tick, period, cap, tag, wr in BATTERIES:
        p = path_for(arm, seed, rich, world, place, tick, period, cap, tag, wr)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        cmd = [sys.executable, RUNNER, arm, str(seed), str(STEPS), "on", rich,
               "on", world, place, str(tick), str(period),
               "inf" if cap is None else str(cap), tag,
               "def" if wr is None else str(wr)]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           timeout=1800, env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {rich} {world} {place} "
              f"t={tick} p={period} c={cap} {tag} wr={wr} "
              f"{'OK' if ok else 'FAIL rc=%d' % r.returncode}", flush=True)
        if not ok:
            print(r.stdout[-600:], r.stderr[-600:], flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()
