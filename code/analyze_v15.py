"""analyze_v15.py -- recomputes every reported number from the raw cell
JSON, using the trace, not the agent's own summary fields.

Metrics per cell (all from the trace, so an independent verifier can
recompute them without importing agent_v15):
  a0_share        fraction of steps whose action is a0 (the true channel)
  a3_share        fraction of steps whose action is a3 (parking/decoy)
  unmotivated     fraction of steps the agent declared unmotivated
  model_err       |pred_A(a0)-0.9| + |pred_B(a0)-0.1| from the final model
  reward          DOES NOT EXIST -- asserted absent
"""
import json
import os
import sys
from collections import defaultdict

OUT = os.path.join("results", "matrix_v15")
TRUES = {"A": 0.9, "B": 0.1}


def metrics(cell):
    tr = cell["trace"]
    n = len(tr)
    a0 = sum(1 for r in tr if r["action"] == "a0") / n
    a3 = sum(1 for r in tr if r["action"] == "a3") / n
    unm = cell["unmotivated_steps"] / n
    err = abs(cell["final"]["A"]["a0"] - TRUES["A"]) + \
        abs(cell["final"]["B"]["a0"] - TRUES["B"])
    return {"a0_share": a0, "a3_share": a3, "unmotivated": unm,
            "model_err": err}


def load_all():
    cells = {}
    for fn in sorted(os.listdir(OUT)):
        if not fn.endswith(".json"):
            continue
        arm, regime, seed = fn[:-5].rsplit("_", 2)
        with open(os.path.join(OUT, fn)) as fh:
            cells[(arm, regime, int(seed[1:]))] = json.load(fh)
    return cells


def mean(xs):
    return sum(xs) / len(xs)


def ci95(xs):
    n = len(xs)
    m = mean(xs)
    if n < 2:
        return (m, m)
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = (var / n) ** 0.5
    return (m - 1.96 * se, m + 1.96 * se)


def main():
    cells = load_all()
    arms = sorted({k[0] for k in cells})
    regimes = sorted({k[1] for k in cells})
    print("=== v15 analysis (reward-free) ===")
    print(f"cells: {len(cells)}; arms: {arms}; regimes: {regimes}")

    # assert no reward anywhere
    for k, c in cells.items():
        assert not ({"reward", "energy", "alive", "died"} & set(c.keys())), k
        for r in c["trace"]:
            assert set(r.keys()) == {"t", "phase", "feat", "val", "action",
                                     "pred_f0"}, k
    print("  [PASS] no reward/energy/death field in any of "
          f"{len(cells)} cells; trace schema exact")

    table = {}
    for regime in regimes:
        print(f"\n--- regime {regime} ---")
        for arm in arms:
            ms = [metrics(cells[(arm, regime, s)]) for s in range(10)
                  if (arm, regime, s) in cells]
            if not ms:
                continue
            row = {k: mean([m[k] for m in ms]) for k in ms[0]}
            table[(arm, regime)] = row
            print(f"  {arm:14s} a0={row['a0_share']:.3f} "
                  f"a3={row['a3_share']:.3f} unmot={row['unmotivated']:.3f} "
                  f"model_err={row['model_err']:.4f}")

    # paired contrasts vs ig_ctx on a0_share
    print("\n--- paired contrasts on a0_share (vs ig_ctx) ---")
    contrasts = {}
    for regime in regimes:
        base = [metrics(cells[("ig_ctx", regime, s)])["a0_share"]
                for s in range(10) if ("ig_ctx", regime, s) in cells]
        for arm in arms:
            if arm == "ig_ctx":
                continue
            other = [metrics(cells[(arm, regime, s)])["a0_share"]
                     for s in range(10) if (arm, regime, s) in cells]
            diffs = [b - o for b, o in zip(base, other)]
            lo, hi = ci95(diffs)
            wins = sum(1 for d in diffs if d > 0)
            contrasts[(arm, regime)] = (mean(diffs), lo, hi, wins)
            print(f"  [{regime}] ig_ctx - {arm:14s} = {mean(diffs):+.4f} "
                  f"CI[{lo:+.4f},{hi:+.4f}] seeds {wins}/10")

    with open(os.path.join("results", "analyze_v15.json"), "w") as fh:
        json.dump({"table": {f"{k[0]}|{k[1]}": v for k, v in table.items()},
                   "contrasts": {f"{k[0]}|{k[1]}": v
                                 for k, v in contrasts.items()}}, fh,
                  indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())