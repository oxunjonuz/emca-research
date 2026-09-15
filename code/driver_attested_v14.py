"""driver_attested_v14.py -- the ATTESTED matrix (turn 145), prereg §5.

Batteries -> results/matrix_attested_v14/<arm>_<seed>_on_<rich>_on_<world>_<place>_t<tick>_p<period>_c<cap>_<tag>_wr<wr>_au<aud>.json

  IDENT14     a_none, a_scalar, a_believe   x low x v10/v13/v14 x none        (HA5)
  TAGA5       a_failclosed                  x low x v14 x none x au none      (HA5)
  HA1         a_believe                     x low x v14 x rich x 0.30 x world x au live
  HA2         a_believe, a_failclosed       x low x v14 x rich x 0.30 x foreign x au live
  HA3         a_believe, a_failclosed       x low x v14 x rich x 0.30 x world x au none
  HA4         a_believe                     x low x v14 x rich x 0.30 x world x au <LAG_GRID>
  HA5b        a_believe, a_failclosed, a_scalar x low x v14 x none x 0.0 x foreign x au none
  HA6         a_believe                     x low x v14 x none x 0.0 x foreign x wr 0.35 x au live/none
  HA7         a_failclosed                  x low x v14 x none x 0.0 x foreign x wr 0.35 x au none/live
  HA9vacuity  re-run of HA3's counterfactual (a_believe rich world none) is implicit
  DET         a_believe x low x v14 x rich x 0.30 x world x au live seed 0, run twice

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to any frozen
matrix directory.
"""
import os
import subprocess
import sys

from env_attested_v14 import LAG_GRID
from run_life_v14 import path_for, STEPS

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
RUNNER = "run_life_v14.py"
OUTDIR = os.path.join(HERE, "results", "matrix_attested_v14")

# (arm, seed, rich, world, place, tick, period, cap, tag, wr, auditor)
BATTERIES = []
# --- identity anchors in three worlds (HA5)
for arm in ("a_none", "a_scalar", "a_believe"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v14", "none", 0.0, 1, None, "foreign", None, "none"))
for arm in ("a_none", "a_scalar", "a_believe"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v13", "none", 0.0, 1, None, "foreign", None, "none"))
for arm in ("a_none", "a_scalar"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v10", "none", 0.0, 1, None, "foreign", None, "none"))
# --- a_failclosed with no attestation anywhere is the same reading as l_ledger (HA5)
for s in SEEDS:
    BATTERIES.append(("a_failclosed", s, "low", "v14", "none", 0.0, 1, None, "foreign", None, "none"))
# --- HA1: the LIE, with the auditor live
for s in SEEDS:
    BATTERIES.append(("a_believe", s, "low", "v14", "rich", 0.30, 1, None, "world", None, "live"))
# --- HA2: the honest label, auditor live
for arm in ("a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v14", "rich", 0.30, 1, None, "foreign", None, "live"))
# --- HA3: the LIE with no auditor at all (the frozen v13 hole)
for arm in ("a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v14", "rich", 0.30, 1, None, "world", None, "none"))
# --- HA4: the timeliness sweep
for lag in LAG_GRID:
    for s in SEEDS:
        BATTERIES.append(("a_believe", s, "low", "v14", "rich", 0.30, 1, None, "world", None, str(lag)))
# --- HA5b: no forger at all, so the tag is a no-op
for arm in ("a_scalar", "a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v14", "rich", 0.0, 1, None, "foreign", None, "none"))
# --- HA6: the world pays for harm itself; attestation has no lie to catch
for au in ("live", "none"):
    for s in SEEDS:
        BATTERIES.append(("a_believe", s, "low", "v14", "none", 0.0, 1, None, "foreign", 0.35, au))
# --- HA7: the cautious reading, honest raise, with and without an auditor
for au in ("none", "live"):
    for s in SEEDS:
        BATTERIES.append(("a_failclosed", s, "low", "v14", "none", 0.0, 1, None, "foreign", 0.35, au))


def main():
    total = len(BATTERIES)
    done = 0
    for arm, seed, rich, world, place, tick, period, cap, tag, wr, au in BATTERIES:
        p = path_for(arm, seed, True, rich, True, world, place, tick, period,
                     cap, tag, wr, au, OUTDIR)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        cmd = [sys.executable, RUNNER, arm, str(seed), str(STEPS), "on", rich,
               "on", world, place, str(tick), str(period),
               "inf" if cap is None else str(cap), tag,
               "def" if wr is None else str(wr), au]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           timeout=1800,
                           env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {rich} {world} {place} "
              f"t={tick} p={period} c={cap} {tag} wr={wr} au={au} "
              f"{'OK' if ok else 'FAIL rc=%d' % r.returncode}", flush=True)
        if not ok:
            print(r.stdout[-600:], r.stderr[-600:], flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()
