"""driver_bribed_v17.py -- the BRIBED-AUDITOR matrix (turn 152), prereg §5.

Batteries -> results/matrix_bribed_v17/<arm>_<seed>_on_low_on_v17_<place>_t<tick>_p1_cinf_<tag>_wrdef_au<aud>.json

  IDENT17  a_none, a_scalar, a_believe, a_failclosed x 10 seeds x rich x t0.30
           x tag=world x auditor=live                      (HB6: == frozen v14)
  HB1      a_believe, a_failclosed x 10 seeds x rich x t0.30 x world
           x auditor=flip:0.10:0.30                        (HB1, HB2)
  HB3      a_believe, a_failclosed x 10 seeds x rich x t0.30 x world
           x auditor=silent:0.10:0.30                      (HB3)
  HB4      a_believe x 10 seeds x rich x t0.30 x world x {price x bribe} grid
           x mode flip                                     (HB4)
  HB5a     a_believe, a_failclosed x 10 seeds x rich x t0.30 x tag=foreign
           x auditor=flip:0.10:0.30                        (HB5: == honest)
  HB5b     a_believe x 10 seeds x rich x t0.30 x tag=world x auditor=honest:0.10
           (a priced but unbought auditor is v14)          (HB5)
  DET      a_believe seed 0 rich t0.30 world flip:0.10:0.30 run twice (byte eq)

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to any frozen
matrix directory.
"""
import os
import subprocess
import sys

from env_bribed_v17 import PRICE_GRID, BRIBE_GRID, MODES

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000
RUNNER = "run_life_v17.py"
OUTDIR = os.path.join(HERE, "results", "matrix_bribed_v17")


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"

# (arm, seed, place, tick, tag, auditor)
BATTERIES = []
# --- HB6 identity: mode "honest" must reproduce the frozen v14 cells
for arm in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "world", "live"))
# --- HB6b: the no-forger identity anchors (all four arms, no auditor)
for arm in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "none", 0.0, "foreign", "none"))
# --- HB6c: every other frozen-v14 configuration that has a v17 counterpart, so
#     the identity claim is checked on all of them and not only on the anchors.
#     (The world_rich_rate cells of v14 are NOT re-run here: they need a second
#     knob, and the coverage count the analyzer prints makes the omission visible
#     rather than silent.)
for arm in ("a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "world", "none"))     # HA3 (the lie)
        BATTERIES.append((arm, s, "rich", 0.0, "foreign", "none"))    # HA5b
# --- HB1/HB2: the bought auditor attests the payer's claim
for arm in ("a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "world", "flip:0.1:0.3"))
# --- HB3: the bought auditor goes dark
for arm in ("a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "world", "silent:0.1:0.3"))
# --- HB4: the price x bribe grid, mode flip
for price in PRICE_GRID:
    for bribe in BRIBE_GRID:
        for s in SEEDS:
            BATTERIES.append(("a_believe", s, "rich", 0.30, "world",
                              "flip:%s:%s" % (fmt(price), fmt(bribe))))
# --- HB5a: with the honest label the bought auditor is invisible
for arm in ("a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "foreign", "flip:0.1:0.3"))
# --- HB5a control: the same cells with an honest auditor and the honest label
for arm in ("a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, "foreign", "live"))
# --- HB5b: a priced but unbought auditor is v14
for s in SEEDS:
    BATTERIES.append(("a_believe", s, "rich", 0.30, "world", "honest:0.1"))


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def main():
    total = len(BATTERIES)
    uniq = len({path_for(*b) for b in BATTERIES})
    print(f"BATTERIES {total} (unique cells {uniq})", flush=True)
    done = 0
    seen = set()
    for arm, seed, place, tick, tag, au in BATTERIES:
        p = path_for(arm, seed, place, tick, tag, au)
        seen.add(p)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        cmd = [sys.executable, RUNNER, arm, str(seed), str(STEPS), "on", "low",
               "on", "v17", place, str(tick), "1", "inf", tag, "def", au]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           timeout=1800,
                           env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {place} t={tick} {tag} au={au} "
              f"{'OK' if ok else 'FAIL rc=%d' % r.returncode}", flush=True)
        if not ok:
            print(r.stdout[-600:], r.stderr[-600:], flush=True)
    print("DONE", done, "/", total, "unique cells on disk:", len(seen),
          flush=True)


def path_for(arm, seed, place, tick, tag, au):
    return os.path.join(OUTDIR,
                        f"{arm}_{seed}_on_low_on_v17_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{tag}_wrdef_au"
                        f"{str(au).replace(':', '-')}.json")


if __name__ == "__main__":
    main()
