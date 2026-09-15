"""replicate_n40.py -- the n=40 replication of the decisive cells (turn 152).

NEW_TZ item 2 raises a fair objection: every campaign used n = 10 seeds, and v3.3
once needed n = 15 to separate a real effect from noise. So the decisive cells of
every campaign are re-run on **30 FRESH seeds (10..39)** and each headline verdict is
recomputed on the new seeds alone.

This is the standard replication design: the original 10 seeds are NOT re-run, so a
verdict that only held because of the particular seeds it was measured on is exactly
the thing this can catch.

The `run()` functions are IMPORTED (this is a replication, not a verification) and
the cells are written to results/replicate_n40/ ONLY, so no frozen matrix directory
is touched. A final check re-counts the frozen directories.

Usage: python3 replicate_n40.py [jobs]
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("PYTHONHASHSEED", "0")

NEW_SEEDS = list(range(10, 40))
OUT = os.path.join(HERE, "results", "replicate_n40")

import run_life_v10
import run_life_v11
import run_life_v12
import run_life_v13
import run_life_v14
import run_life_v15
import run_life_v16
import run_life_v17
import run_life_v18

# (tag, callable, kwargs) -- the decisive cells, one entry each
CELLS = []
for arm, rich, c in (("s0_nobrake", "low", 0), ("s2_given_rule", "low", 0),
                     ("s3_victim_keyed", "low", 0), ("s3_victim_keyed", "low", 1),
                     ("s4_internalized", "low", 0), ("s4_internalized", "high", 0)):
    CELLS.append((f"v10_{arm}_{rich}_c{c}",
                  lambda s, a=arm, r=rich, cc=c: run_life_v10.run(
                      a, s, 16000, True, r, True, "v10", cc)))
for arm in ("n_none", "n_inflate_g6", "n_inflate_g10", "n_bound"):
    CELLS.append((f"v11_{arm}",
                  lambda s, a=arm: run_life_v11.run(a, s, 16000, True, "low",
                                                    True, "v11", 0.0)))
for tick in (0.24, 0.25, 0.26, 0.30):
    CELLS.append((f"v12_v_price_rich_t{tick}",
                  lambda s, t=tick: run_life_v12.run("v_price", s, 16000, True,
                                                     "low", True, "v12", "rich", t,
                                                     1, None)))
CELLS.append(("v13_l_ledger_lie",
              lambda s: run_life_v13.run("l_ledger", s, 16000, True, "low", True,
                                         "v13", "rich", 0.30, 1, None, "world")))
CELLS.append(("v13_l_ledger_honest",
              lambda s: run_life_v13.run("l_ledger", s, 16000, True, "low", True,
                                         "v13", "rich", 0.30, 1, None, "foreign")))
CELLS.append(("v14_a_believe_lie_live",
              lambda s: run_life_v14.run("a_believe", s, 16000, True, "low", True,
                                         "v14", "rich", 0.30, 1, None, "world",
                                         None, "live")))
CELLS.append(("v14_a_believe_lie_none",
              lambda s: run_life_v14.run("a_believe", s, 16000, True, "low", True,
                                         "v14", "rich", 0.30, 1, None, "world",
                                         None, "none")))
CELLS.append(("v14_a_failclosed_live",
              lambda s: run_life_v14.run("a_failclosed", s, 16000, True, "low",
                                         True, "v14", "rich", 0.30, 1, None,
                                         "world", None, "live")))
for tick in (0.25, 0.26):
    CELLS.append((f"v16_w_price_rich_t{tick}",
                  lambda s, t=tick: run_life_v16.run("w_price", s, 16000, True,
                                                     "low", True, "v12", "rich", t,
                                                     1, None)))
CELLS.append(("v16_n_doctor_rich_t0.30",
              lambda s: run_life_v16.run("n_doctor", s, 16000, True, "low", True,
                                         "v12", "rich", 0.30, 1, None)))
CELLS.append(("v17_a_believe_flip",
              lambda s: run_life_v17.run("a_believe", s, 16000, True, "low", True,
                                         "v17", "rich", 0.30, 1, None, "world",
                                         None, "flip:0.1:0.3")))
CELLS.append(("v17_a_failclosed_silent",
              lambda s: run_life_v17.run("a_failclosed", s, 16000, True, "low",
                                         True, "v17", "rich", 0.30, 1, None,
                                         "world", None, "silent:0.1:0.3")))
CELLS.append(("v18_w_price_station",
              lambda s: run_life_v18.run("w_price", s, 16000, True, "low", True,
                                         "v18", "rich", 0.30, 1, None, "station",
                                         False)))
CELLS.append(("v18_w_widen_none",
              lambda s: run_life_v18.run("w_widen", s, 16000, True, "low", True,
                                         "v18", "rich", 0.30, 1, None, "none",
                                         False)))
for mode in ("ig_ctx", "ig_relevant", "rand"):
    CELLS.append((f"v15_{mode}",
                  lambda s, m=mode: run_life_v15.run(s, m, 16000)))


def one(tag, fn, seed):
    p = os.path.join(OUT, f"{tag}_{seed}.json")
    if os.path.exists(p) and os.path.getsize(p) > 200:
        return tag, seed, "cached"
    log = fn(seed)
    with open(p, "w") as f:
        f.write(json.dumps(log, indent=1, sort_keys=True, default=str))
    return tag, seed, "ok"


def main():
    jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    os.makedirs(OUT, exist_ok=True)
    tasks = [(tag, fn, s) for (tag, fn) in CELLS for s in NEW_SEEDS]
    print("cells to run: %d" % len(tasks), flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for tag, seed, status in ex.map(lambda t: one(*t), tasks):
            done += 1
            if status not in ("ok", "cached"):
                print("  %s seed %d: %s" % (tag, seed, status), flush=True)
            if done % 100 == 0:
                print("  %d/%d" % (done, len(tasks)), flush=True)
    print("RUN DONE", done, flush=True)
    for d in ("matrix_v7", "matrix_safety_v10", "matrix_wirehead_v11",
              "matrix_wirehead_v12", "matrix_ledger_v13", "matrix_attested_v14",
              "matrix_v15", "matrix_scope_v16", "matrix_bribed_v17",
              "matrix_enforced_v18"):
        p = os.path.join(HERE, "results", d)
        if os.path.isdir(p):
            print("  frozen %-22s %d cells" %
                  (d, len([x for x in os.listdir(p) if x.endswith(".json")])))


if __name__ == "__main__":
    main()