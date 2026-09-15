"""driver_wirehead_v11.py -- the wireheading matrix (turn 140), prereg §6.

Batteries -> results/matrix_wirehead_v11/<arm>_<seed>_on_<rich>_on_<world>_b<rate>.json
  IDENT      n_unarmed, n_none, n_inflate_g5, n_bound  x low  x rate 0.30   (W2,W1,W7)
  FALSESIGN  n_none, n_inflate_{2,5,6,10}              x low  x rate 0.00   (W4)
  DEFLATE    n_none, n_deflate_{1,2}                   x high x rate 0.00   (W5)
  ARBITER    n_none, n_inflate_{10,14,20}              x low  x rate 0.00   (W4,W6)
  RICHHI     n_none, n_inflate_{5,10}                  x high x rate 0.00   (control)
  BOUNDLADDER n_bound                                  x low  x {0.00,0.30} (W1,W7)
  V10IDENT   n_unarmed, n_none  x low x rate 0.00, world=v10  (the anchors)

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to
results/matrix_v7 or results/matrix_safety_v10.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000

BATTERIES = []
# the identity anchors, run through the SAME runner against the FROZEN v10 world
for arm in ("n_unarmed", "n_none"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v10", 0.00))
# IDENT (beacon channel ON)
for arm in ("n_unarmed", "n_none", "n_inflate_g5", "n_bound"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v11", 0.30))
# IDENT-OFF (the same arms with the channel closed, for the channel control)
for arm in ("n_unarmed", "n_none", "n_inflate_g5"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v11", 0.00))
# FALSESIGN: the world's reward stream is the v10 stream exactly
for arm in ("n_none", "n_inflate_g2", "n_inflate_g5", "n_inflate_g6",
            "n_inflate_g10"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v11", 0.00))
# DEFLATE at rich=high
for arm in ("n_none", "n_deflate_g1", "n_deflate_g2"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "high", "v11", 0.00))
# ARBITER: high inflation, to reach the accept bar
for arm in ("n_none", "n_inflate_g14", "n_inflate_g20"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v11", 0.00))
# RICHHI control
for arm in ("n_none", "n_inflate_g5", "n_inflate_g10"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "high", "v11", 0.00))
# BOUNDLADDER
for rate in (0.00, 0.30):
    for s in SEEDS:
        BATTERIES.append(("n_bound", s, "low", "v11", rate))
# CHANNELONCONTROL: does opening the beacon channel change the UNBOUND arms?
# (declared control: with the gate above, beacon_rate cannot enter a non-bound
#  arm's policy, so these must be byte-identical to the b=0 cells)
for arm in ("n_unarmed", "n_none"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "low", "v11", 0.30))


def fmt_rate(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def path_for(arm, seed, rich, world, rate):
    return os.path.join(HERE, "results", "matrix_wirehead_v11",
                        f"{arm}_{seed}_on_{rich}_on_{world}_b{fmt_rate(rate)}.json")


def main():
    total = len(BATTERIES)
    done = 0
    for arm, seed, rich, world, rate in BATTERIES:
        p = path_for(arm, seed, rich, world, rate)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        r = subprocess.run(
            [sys.executable, "run_life_v11.py", arm, str(seed), str(STEPS),
             "on", rich, "on", world, str(rate)],
            cwd=HERE, capture_output=True, text=True, timeout=1800,
            env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {rich} {world} b={rate} "
              f"{'OK' if ok else 'FAIL rc=%d' % r.returncode}", flush=True)
        if not ok:
            print(r.stdout[-600:], r.stderr[-600:], flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()
