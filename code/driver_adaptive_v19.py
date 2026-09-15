"""driver_adaptive_v19.py -- the ADAPTIVE-PAYER matrix (turn 154), prereg §4.

Batteries -> results/matrix_adaptive_v19/<arm>_<seed>_on_low_on_<world>_<place>_t<tick>_<tag>_au<aud>_<payer>.json

  IDENT19  a_none, a_scalar, a_believe, a_failclosed x 10 seeds x v17 x rich
           x t0.30 x world x au=live                            (HQ1: == frozen v17)
  IDENT19b the same four arms x 10 seeds x v19 x rich x t0.30 x world x au=live
           x payer=none                          (the v19 world with the frozen forger)
  HQ2      a_believe x 10 seeds x v19 x rich x au=none x p_knows:1
  HQ3      a_believe x 10 seeds x v19 x rich x au=none x p_frontload:K:T,
           (K,T) in {(1,1.30),(2,1.30),(1,1.25)}
  HQ4      a_believe x 10 seeds x v19 x rich x au=none x {p_sweep,p_greedy}:B,
           B in BLOCK_GRID
  HQ5a     a_failclosed x 10 seeds x v19 x rich x au=none x {p_greedy:1,
           p_sweep:1,p_knows:1}          (the unpriced defence: no price to find)
  HQ5b     a_believe x 10 seeds x v19 x rich x au=none x p_nofeedback:B,
           B in {1,5,25}                            (the non-vacuity control)
  HQ6      a_believe x 10 seeds x v19 x rich x au=flip:0.1:0.3 x p_knows:1
  DET      one cell run twice (byte equality)

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to any frozen
matrix directory.
"""
import os
import subprocess
import sys

from env_adaptive_v19 import BLOCK_GRID, FRONT_K_GRID, PAYER_ARMS

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000
RUNNER = "run_life_v19.py"
OUTDIR = os.path.join(HERE, "results", "matrix_adaptive_v19")
WORLD = "v19"

# (arm, seed, world, place, tick, tag, auditor, payer)
BATTERIES = []
# --- HQ1: the frozen attacker under the v17 world, by path (identity)
for arm in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "v17", "rich", 0.30, "world", "live", "none"))
# --- IDENT19b: the same four arms in the v19 world with the frozen forger
for arm in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
    for s in SEEDS:
        BATTERIES.append((arm, s, WORLD, "rich", 0.30, "world", "live", "none"))
# --- HQ2: the attacker that KNOWS the rule
for s in SEEDS:
    BATTERIES.append(("a_believe", s, WORLD, "rich", 0.30, "world", "none",
                      "p_knows:1"))
# --- HQ3: the timing attack
for (k, T) in ((1, 1.30), (2, 1.30), (1, 1.25)):
    for s in SEEDS:
        BATTERIES.append(("a_believe", s, WORLD, "rich", 0.30, "world", "none",
                          "p_frontload:%d:%s" % (k, T)))
# --- HQ4: the learning attacker at every declared block size
for b in BLOCK_GRID:
    for arm in ("p_sweep", "p_greedy"):
        for s in SEEDS:
            BATTERIES.append(("a_believe", s, WORLD, "rich", 0.30, "world", "none",
                              "%s:%d" % (arm, b)))
# --- HQ5a: the unpriced defence -- no auditor, so no price to find
for pay in ("p_greedy:1", "p_sweep:1", "p_knows:1"):
    for s in SEEDS:
        BATTERIES.append(("a_failclosed", s, WORLD, "rich", 0.30, "world", "none",
                          pay))
# --- HQ5b: the non-vacuity control
for b in (1, 5, 25):
    for s in SEEDS:
        BATTERIES.append(("a_believe", s, WORLD, "rich", 0.30, "world", "none",
                          "p_nofeedback:%d" % b))
# --- HQ6: the same learner with a BOUGHT auditor (mode flip)
for s in SEEDS:
    BATTERIES.append(("a_believe", s, WORLD, "rich", 0.30, "world",
                      "flip:0.1:0.3", "p_knows:1"))
    BATTERIES.append(("a_believe", s, WORLD, "rich", 0.30, "world",
                      "flip:0.1:0.3", "p_greedy:1"))


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def norm_payer(spec):
    if spec in (None, "none"):
        return "none"
    parts = str(spec).split(":")
    out = [parts[0]]
    for x in parts[1:]:
        try:
            out.append(fmt(float(x)))
        except (TypeError, ValueError):
            out.append(x)
    return ":".join(out)


def path_for(arm, seed, world, place, tick, tag, auditor, payer):
    autag = "none" if auditor in (None, "none") else str(auditor).replace(":", "-")
    return os.path.join(
        OUTDIR,
        f"{arm}_{seed}_on_low_on_{world}_{place}_t{fmt(tick)}_{tag}"
        f"_au{autag}_{norm_payer(payer).replace(':', '-')}.json")


def main():
    total = len(BATTERIES)
    uniq = len({path_for(*b) for b in BATTERIES})
    print(f"BATTERIES {total} (unique cells {uniq})", flush=True)
    done = 0
    for arm, seed, world, place, tick, tag, au, pay in BATTERIES:
        p = path_for(arm, seed, world, place, tick, tag, au, pay)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        cmd = [sys.executable, RUNNER, arm, str(seed), str(STEPS), "on", "low",
               "on", world, place, str(tick), tag, au, pay]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           timeout=1800,
                           env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {world} {place} t={tick} {tag} "
              f"au={au} pay={pay} {'OK' if ok else 'FAIL rc=%d' % r.returncode}",
              flush=True)
        if not ok:
            print(r.stdout[-800:], r.stderr[-800:], flush=True)
    print("DONE", done, "/", total, "unique cells on disk:", uniq, flush=True)


if __name__ == "__main__":
    main()