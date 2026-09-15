"""driver_v20_replication.py -- v20 decisive cells on 30 FRESH seeds (10..39).

Owner msg_00157 flags n=10 as thin for absolute statements, and the line has already
refuted one of its own absolute claims this way (v16's "never drains"). So the
decisive v20 cells are re-run on 30 seeds that were NOT used for the frozen matrix,
and any verdict that does not survive is reported as not surviving.

Decisive cells (arm, place, tick, gw, enforcer_spec):
  HV1  w_price  rich t0.30 gw0 station:open:0.10:0.30   (the boundary bought)
  HV1c w_price  rich t0.30 gw0 station                 (honest counterpart)
  HV2  w_price  rich t0.30 gw0 station:dark:0.10:0.30  (announced failure)
  HV5  w_widen  rich t0.30 gw0 station:open:0.10:0.30  (the grant bought)

Writes results/matrix_v20_replication/. Never touches the frozen matrix.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(10, 40))
STEPS = 16000
RUNNER = "run_life_v20.py"
OUTDIR = os.path.join(HERE, "results", "matrix_v20_replication")

CELLS = [
    ("w_price", "rich", 0.30, False, "station:open:0.10:0.30"),
    ("w_price", "rich", 0.30, False, "station"),
    ("w_price", "rich", 0.30, False, "station:dark:0.10:0.30"),
    ("w_widen", "rich", 0.30, False, "station:open:0.10:0.30"),
]


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


def path_for(arm, seed, place, tick, gw, spec):
    etag = (norm(spec) or "none").replace(":", "-")
    return os.path.join(OUTDIR,
                        f"{arm}_{seed}_on_low_on_v20_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{etag}.json")


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    total = len(CELLS) * len(SEEDS)
    print(f"REPLICATION cells {total} on seeds {SEEDS[0]}..{SEEDS[-1]}", flush=True)
    done = 0
    for arm, place, tick, gw, spec in CELLS:
        for seed in SEEDS:
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
                               env={**os.environ, "PYTHONHASHSEED": "0",
                                    "V20_OUTDIR": OUTDIR})
            ok = os.path.exists(p) and os.path.getsize(p) > 200
            done += 1
            if not ok or done % 20 == 0:
                print(f"[{done}/{total}] {arm} {seed} {spec} "
                      f"{'OK' if ok else 'FAIL rc=%d' % r.returncode}", flush=True)
    print("DONE", done, "/", total, flush=True)


if __name__ == "__main__":
    main()