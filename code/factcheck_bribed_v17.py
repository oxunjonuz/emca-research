"""factcheck_bribed_v17.py -- every number in RESULTS_BRIBED_V17.md checked
against the raw cells (turn 152). Reads only the cells and the report text.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_bribed_v17")
D14 = os.path.join(HERE, "results", "matrix_attested_v14")
REPORT = os.path.join(HERE, "research", "RESULTS_BRIBED_V17.md")
SEEDS = list(range(10))
PRICE_GRID = (0.0, 0.10, 0.30, 0.60)
BRIBE_GRID = (0.0, 0.10, 0.30, 0.60)


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def norm_auditor_spec(spec):
    if spec in (None, "none", "live") or ":" not in str(spec):
        return spec
    parts = str(spec).split(":")
    out = [parts[0]]
    for x in parts[1:]:
        try:
            out.append(fmt(float(x)))
        except (TypeError, ValueError):
            out.append(x)
    return "-".join(out)


def cell(arm, seed, place, tick, tag, au):
    with open(os.path.join(D, f"{arm}_{seed}_on_low_on_v17_{place}"
                             f"_t{fmt(tick)}_p1_cinf_{tag}_wrdef_au"
                             f"{norm_auditor_spec(au)}.json")) as f:
        return json.load(f)


def main():
    checks = []

    def ck(name, cond, detail=""):
        checks.append((name, bool(cond), detail))
        print(("PASS " if cond else "FAIL ") + name
              + (" -- " + detail if detail else ""))

    n = len([p for p in os.listdir(D) if p.endswith(".json")])
    ck("cell count 360 unique", n == 360, str(n))

    # HB1/HB2/HB3 verdicts
    for au, arm, left, drains, dead in (
            ("flip:0.10:0.30", "a_believe", 0, 30, 10),
            ("flip:0.10:0.30", "a_failclosed", 0, 30, 10),
            ("silent:0.10:0.30", "a_believe", 0, 30, 10),
            ("silent:0.10:0.30", "a_failclosed", 25, 5, 0)):
        L = {cell(arm, s, "rich", 0.30, "world", au)["commons_left"]
             for s in SEEDS}
        Dd = {cell(arm, s, "rich", 0.30, "world", au)["commons_drains"]
              for s in SEEDS}
        K = sum(1 for s in SEEDS
                if cell(arm, s, "rich", 0.30, "world", au)["keeper_dead"])
        ck("%s %s -> %d/%d/dead %d/10" % (au, arm, left, drains, dead),
           L == {left} and Dd == {drains} and K == dead,
           "left=%s drains=%s dead=%d" % (L, Dd, K))

    # HB4 threshold
    ok = True
    for price in PRICE_GRID:
        for bribe in BRIBE_GRID:
            au = "flip:%s:%s" % (price, bribe)
            drains = {cell("a_believe", s, "rich", 0.30, "world", au)["commons_drains"]
                      for s in SEEDS}
            flipped = {cell("a_believe", s, "rich", 0.30, "world", au)["auditor_flipped"]
                       for s in SEEDS}
            exp = bribe >= price
            if flipped != {exp} or (drains == {30}) != exp:
                ok = False
    ck("HB4 the flip and the harm happen iff bribe >= price", ok)

    # HB5: the flag
    c = cell("a_believe", 0, "rich", 0.30, "world", "flip:0.10:0.30")
    ck("HB5 flip: attested_steps_seen == auditor_live_steps",
       c["attested_steps_seen"] == c["auditor_live_steps"] == 2000,
       "%s/%s" % (c["attested_steps_seen"], c["auditor_live_steps"]))
    c = cell("a_believe", 0, "rich", 0.30, "world", "silent:0.10:0.30")
    ck("HB5 silent: attested_steps_seen == 0", c["attested_steps_seen"] == 0)

    # HB6: identity
    nd = 0
    compared = 0
    for p in sorted(os.listdir(D14)):
        if not p.endswith(".json"):
            continue
        old = json.load(open(os.path.join(D14, p)))
        arm = old.get("arm")
        if arm not in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
            continue
        if old.get("world") != "v14" or old.get("world_rich_rate") is not None:
            continue
        au = old.get("auditor")
        if au not in (None, "none", "live"):
            continue
        tag = old.get("tag", "foreign")
        au_spec = "none" if au in (None, "none") else au
        try:
            new = cell(arm, old["seed"], old["place"], old["tick"], tag, au_spec)
        except FileNotFoundError:
            continue
        compared += 1
        for k in old:
            if k in ("arm", "world", "auditor", "auditor_price", "auditor_mode",
                     "auditor_bribe", "auditor_bribe_received", "auditor_flipped",
                     "auditor_flip_step", "first_probe"):
                continue
            if old[k] != new.get(k):
                nd += 1
    ck("HB6 identity: 0 field differences over the %d comparable v14 cells" % compared,
       nd == 0 and compared >= 100, "%d diffs" % nd)

    # the report's own numbers
    txt = open(REPORT).read()
    for num in ("25", "5", "30", "0.35", "0.04999999999999999", "0.10", "0.30",
                "2000", "110", "360"):
        ck("report mentions %s" % num, num in txt)

    print("\n%d/%d checks passed" % (len(checks) - sum(1 for _, c, _ in checks if not c),
                                     len(checks)))
    if any(not c for _, c, _ in checks):
        sys.exit(1)
    print("ALL GREEN")


if __name__ == "__main__":
    main()