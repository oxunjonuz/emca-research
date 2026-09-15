"""driver_bribed_enforcer_v20.py -- the BRIBED-ENFORCER matrix (turn 157), prereg §4.

Batteries -> results/matrix_bribed_enforcer_v20/<arm>_<seed>_on_low_on_v20_<place>_t<tick>_p1_cinf_<etag>.json

  HV6anchor  honest boundary: w_none/w_price/n_doctor/n_pump_price/w_widen x none,
             and w_price/w_widen/n_doctor x station, x 10 seeds x rich x t0.30
             (identity vs the frozen v18 cells)
  HV1        w_price x station x open:0.10:0.30 x 10 seeds   (the boundary bought)
  HV2        w_price x station x dark:0.10:0.30 x 10 seeds   (announced failure)
  HV3        w_price x station x open:<price>:<bribe> x 16 x 10 seeds (the cliff)
  HV5        w_widen x station x gw0 x open:0.10:0.30 x 10 seeds (the grant bought)
  HV5c       w_widen x station x gw1 x open:0.10:0.30 x 10 seeds (granted anyway)
  NOSCOPE    w_price x none x open:0.10:0.30 x 10 seeds      (no scope to buy)
  DET        w_price seed 0 station open:0.10:0.30 run twice (byte eq)

Sequential, resumable, PYTHONHASHSEED=0, 16000 steps. Never writes to any frozen
matrix directory.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10))
STEPS = 16000
RUNNER = "run_life_v20.py"
OUTDIR = os.path.join(HERE, "results", "matrix_bribed_enforcer_v20")
PRICE_GRID = (0.0, 0.10, 0.30, 0.60)
BRIBE_GRID = (0.0, 0.10, 0.30, 0.60)


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def norm(spec):
    if spec in (None, "none") or ":" not in str(spec):
        return spec
    parts = str(spec).split(":")
    out = [parts[0]]
    for x in parts[1:]:
        try:
            out.append(fmt(float(x)))
        except (TypeError, ValueError):
            out.append(x)
    return ":".join(out)


# (arm, seed, place, tick, grant_widen, enforcer_spec)
BATTERIES = []
# --- HV6 anchors: the honest boundary, byte-identical to v18
for arm in ("w_none", "w_price", "n_doctor", "n_pump_price", "w_widen"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, False, "none"))
for arm in ("w_price", "w_widen", "n_doctor"):
    for s in SEEDS:
        BATTERIES.append((arm, s, "rich", 0.30, False, "station"))
# --- HV1/HV2: the boundary bought, open and dark
for s in SEEDS:
    BATTERIES.append(("w_price", s, "rich", 0.30, False, "station:open:0.10:0.30"))
for s in SEEDS:
    BATTERIES.append(("w_price", s, "rich", 0.30, False, "station:dark:0.10:0.30"))
# --- HV3: the price x bribe cliff (open)
for price in PRICE_GRID:
    for bribe in BRIBE_GRID:
        for s in SEEDS:
            BATTERIES.append(("w_price", s, "rich", 0.30, False,
                              "station:open:%s:%s" % (price, bribe)))
# --- HV5: the widen grant bought
for s in SEEDS:
    BATTERIES.append(("w_widen", s, "rich", 0.30, False, "station:open:0.10:0.30"))
for s in SEEDS:
    BATTERIES.append(("w_widen", s, "rich", 0.30, True, "station:open:0.10:0.30"))
# --- NOSCOPE counterfactual: no scope to buy
for s in SEEDS:
    BATTERIES.append(("w_price", s, "rich", 0.30, False, "none:open:0.10:0.30"))


def path_for(arm, seed, place, tick, gw, spec):
    etag = (norm(spec) or "none").replace(":", "-")
    return os.path.join(OUTDIR,
                        f"{arm}_{seed}_on_low_on_v20_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{etag}.json")


def main():
    total = len(BATTERIES)
    uniq = len({path_for(*b) for b in BATTERIES})
    print(f"BATTERIES {total} (unique cells {uniq})", flush=True)
    done = 0
    for arm, seed, place, tick, gw, spec in BATTERIES:
        p = path_for(arm, seed, place, tick, gw, spec)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            done += 1
            continue
        scope = spec.split(":")[0] if ":" in spec else spec
        cmd = [sys.executable, RUNNER, arm, str(seed), str(STEPS), "on", "low",
               "on", "v20", place, str(tick), "1", "inf", scope,
               "1" if gw else "0", spec]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           timeout=1800,
                           env={**os.environ, "PYTHONHASHSEED": "0"})
        ok = os.path.exists(p) and os.path.getsize(p) > 200
        done += 1
        print(f"[{done}/{total}] {arm} {seed} {place} t={tick} gw={int(bool(gw))} "
              f"enf={spec} {'OK' if ok else 'FAIL rc=%d' % r.returncode}",
              flush=True)
        if not ok:
            print(r.stdout[-600:], r.stderr[-600:], flush=True)
    print("DONE", done, "/", total, "unique cells on disk:", uniq, flush=True)


if __name__ == "__main__":
    main()