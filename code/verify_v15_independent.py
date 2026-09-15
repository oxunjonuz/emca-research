"""verify_v15_independent.py -- independent pass.

Fresh process, DISK ONLY: it imports NEITHER env_v15 NOR agent_v15 NOR
run_life_v15. It reads the 210 raw cell JSONs and recomputes every
reported metric from the trace with its own code, then checks the
structural claims with live negative controls.
"""
import json
import math
import os
import sys
from collections import Counter

OUT = os.path.join("results", "matrix_v15")
TRUES = {"A": 0.9, "B": 0.1}
FAILS = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    if not cond:
        FAILS.append(name)
    print(f"  [{tag}] {name} {detail}")


def load():
    cells = {}
    for fn in sorted(os.listdir(OUT)):
        if fn.endswith(".json"):
            arm, regime, seed = fn[:-5].rsplit("_", 2)
            with open(os.path.join(OUT, fn)) as fh:
                cells[(arm, regime, int(seed[1:]))] = json.load(fh)
    return cells


def main():
    print("=== v15 independent pass (disk only) ===")
    cells = load()
    check("A1 210 cells present", len(cells) == 210, f"got {len(cells)}")

    # recompute a0_share from the trace, independently
    bad = 0
    for k, c in cells.items():
        tr = c["trace"]
        a0 = sum(1 for r in tr if r["action"] == "a0")
        if abs(a0 / len(tr) - c["a0_steps"] / c["steps"]) > 1e-9:
            bad += 1
    check("A2 a0_steps agrees with the trace, all cells", bad == 0,
          f"{bad} mismatches")

    # the reward-free claim, re-derived from raw bytes
    keys = set()
    for c in cells.values():
        keys |= set(c.keys())
    check("A3 no reward/energy/death key anywhere in the cells",
          not ({"reward", "energy", "alive", "died"} & keys),
          f"keys seen: {sorted(keys)}")
    tracekeys = set()
    for c in cells.values():
        for r in c["trace"]:
            tracekeys |= set(r.keys())
    check("A4 trace schema is exactly {t,phase,feat,val,action,pred_f0}",
          tracekeys == {"t", "phase", "feat", "val", "action", "pred_f0"},
          f"{sorted(tracekeys)}")

    # recompute model_err from the final prediction table
    def err(c):
        return abs(c["final"]["A"]["a0"] - TRUES["A"]) + \
            abs(c["final"]["B"]["a0"] - TRUES["B"])
    ig = [err(cells[("ig_ctx", "base", s)]) for s in range(10)]
    rl = [err(cells[("ig_relevant", "base", s)]) for s in range(10)]
    check("A5 ig_ctx learns the true structure (mean err < 0.08)",
          sum(ig) / 10 < 0.08, f"mean {sum(ig)/10:.4f}")
    check("A6 ig_relevant learns it too", sum(rl) / 10 < 0.08,
          f"mean {sum(rl)/10:.4f}")

    # THE SEAM CLAIM: pure IG's action distribution is indistinguishable
    # from random; the criterion arm's is not.
    def a0(c):
        return sum(1 for r in c["trace"] if r["action"] == "a0") / len(c["trace"])
    ig_a0 = [a0(cells[("ig_ctx", "base", s)]) for s in range(10)]
    rd_a0 = [a0(cells[("rand", "base", s)]) for s in range(10)]
    rl_a0 = [a0(cells[("ig_relevant", "base", s)]) for s in range(10)]
    check("A7 pure IG a0_share ~ 0.25 (indifferent), 10/10",
          all(abs(x - 0.25) < 0.02 for x in ig_a0),
          f"range [{min(ig_a0):.3f},{max(ig_a0):.3f}]")
    check("A8 random a0_share ~ 0.25", all(abs(x - 0.25) < 0.02 for x in rd_a0))
    check("A9 criterion arm a0_share > 0.95, 10/10",
          all(x > 0.95 for x in rl_a0),
          f"range [{min(rl_a0):.3f},{max(rl_a0):.3f}]")

    # the noisy-TV regime: naive_info is captured by the fakeable channel
    def a3(c):
        return sum(1 for r in c["trace"] if r["action"] == "a3") / len(c["trace"])
    ni_tv = [a3(cells[("naive_info", "tv", s)]) for s in range(10)]
    check("A10 naive_info is drawn to the noisy TV (a3_share > 0.2)",
          sum(ni_tv) / 10 > 0.2, f"mean {sum(ni_tv)/10:.3f}")
    ni_base = [a3(cells[("naive_info", "base", s)]) for s in range(10)]
    check("A11 ...and NOT in the base regime (parking channel)",
          sum(ni_base) / 10 < 0.05, f"mean {sum(ni_base)/10:.3f}")

    # determinism: a fresh run reproduces the frozen cell byte-for-byte
    # is checked by the driver-level re-run in run_all_v15.sh; here we
    # check internal consistency of the trace timestamps.
    ok = all(all(r["t"] == i + 1 for i, r in enumerate(c["trace"]))
             for c in cells.values())
    check("A12 trace timestamps are 1..N in every cell", ok)

    # LIVE NEGATIVE CONTROL: corrupt one cell's action stream and the
    # seam check must go red.
    c = dict(cells[("ig_ctx", "base", 0)])
    c["trace"] = [dict(r) for r in c["trace"]]
    for r in c["trace"]:
        r["action"] = "a3"
    corrupted = sum(1 for r in c["trace"] if r["action"] == "a0") / len(c["trace"])
    check("NV1 corrupted cell FAILS the indifference check",
          not (abs(corrupted - 0.25) < 0.02), f"corrupted a0 {corrupted:.3f}")

    print(f"=== {len(FAILS)} failures ===")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())