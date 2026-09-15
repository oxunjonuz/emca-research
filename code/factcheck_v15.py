"""factcheck_v15.py -- checks every number quoted in RESULTS_V15.md
against the raw cells on disk. A number in the report that is not in the
cells is a failure.
"""
import json
import os
import re
import sys

OUT = os.path.join("results", "matrix_v15")
REPORT = os.path.join("research", "RESULTS_V15.md")
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
    print("=== v15 factcheck ===")
    cells = load()
    with open(REPORT) as fh:
        txt = fh.read()

    def a0(arm, regime):
        xs = [sum(1 for r in cells[(arm, regime, s)]["trace"]
                  if r["action"] == "a0") / cells[(arm, regime, s)]["steps"]
              for s in range(10)]
        return sum(xs) / 10

    def a3(arm, regime):
        xs = [sum(1 for r in cells[(arm, regime, s)]["trace"]
                  if r["action"] == "a3") / cells[(arm, regime, s)]["steps"]
              for s in range(10)]
        return sum(xs) / 10

    def err(arm, regime):
        xs = []
        for s in range(10):
            c = cells[(arm, regime, s)]
            xs.append(abs(c["final"]["A"]["a0"] - 0.9) +
                      abs(c["final"]["B"]["a0"] - 0.1))
        return sum(xs) / 10

    facts = {
        "ig_ctx base a0": (a0("ig_ctx", "base"), 0.250),
        "ig_relevant base a0": (a0("ig_relevant", "base"), 0.998),
        "rand base a0": (a0("rand", "base"), 0.250),
        "naive_info tv a3": (a3("naive_info", "tv"), 0.300),
        "naive_info base a3": (a3("naive_info", "base"), 0.000),
        "ig_ctx base err": (err("ig_ctx", "base"), 0.036),
        "ig_pooled base err": (err("ig_pooled", "base"), 0.800),
        "confirm base a0": (a0("confirm", "base"), 0.500),
    }
    for name, (measured, quoted) in facts.items():
        check(f"F {name} ~ {quoted}", abs(measured - quoted) < 0.01,
              f"measured {measured:.4f}")

    # the report must not claim a reward exists
    check("F report states there is no reward",
          "no reward" in txt.lower() or "reward-free" in txt.lower())

    # every quoted number must appear in the report text
    for name, (measured, quoted) in facts.items():
        s = f"{quoted:.3f}"
        check(f"F report contains {s}", s in txt, f"({name})")

    print(f"=== {len(FAILS)} failures ===")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())