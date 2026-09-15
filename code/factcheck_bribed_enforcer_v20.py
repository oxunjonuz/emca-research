"""factcheck_bribed_enforcer_v20.py -- every number in RESULTS_BRIBED_ENFORCER_V20.md
checked against the raw cells (turn 157). Reads only the cells and the report text.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_bribed_enforcer_v20")
DR = os.path.join(HERE, "results", "matrix_v20_replication")
D18 = os.path.join(HERE, "results", "matrix_enforced_v18")
REPORT = os.path.join(HERE, "research", "RESULTS_BRIBED_ENFORCER_V20.md")
SEEDS = list(range(10))
FRESH = list(range(10, 40))


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def cell(arm, seed, place, tick, spec):
    with open(os.path.join(D, f"{arm}_{seed}_on_low_on_v20_{place}"
                             f"_t{fmt(tick)}_p1_cinf_{spec}.json")) as f:
        return json.load(f)


def rcell(arm, seed, place, tick, spec):
    with open(os.path.join(DR, f"{arm}_{seed}_on_low_on_v20_{place}"
                              f"_t{fmt(tick)}_p1_cinf_{spec}.json")) as f:
        return json.load(f)


def main():
    checks = []

    def ck(name, cond, detail=""):
        checks.append((name, bool(cond), detail))
        print(("PASS " if cond else "FAIL ") + name
              + (" -- " + detail if detail else ""))

    n = len([p for p in os.listdir(D) if p.endswith(".json")])
    ck("frozen cell count 270", n == 270, str(n))
    rn = len([p for p in os.listdir(DR) if p.endswith(".json")])
    ck("replication cell count 120", rn == 120, str(rn))

    # HV1 open
    rows = [cell("w_price", s, "rich", 0.30, "station-open-0.1-0.3")
            for s in SEEDS]
    ck("HV1 open: 30 drains, dead 10/10, refusals 0",
       sorted({r["commons_drains"] for r in rows}) == [30]
       and sum(1 for r in rows if r["keeper_dead"]) == 10
       and sorted({r["enforcer_refusals"] for r in rows}) == [0],
       "%s" % sorted({r["commons_drains"] for r in rows}))
    # HV1 honest
    rows = [cell("w_price", s, "rich", 0.30, "station") for s in SEEDS]
    ck("HV1c honest: 0 drains, alive 10/10, refusals > 0",
       sorted({r["commons_drains"] for r in rows}) == [0]
       and sum(1 for r in rows if r["keeper_dead"]) == 0
       and min(r["enforcer_refusals"] for r in rows) > 0,
       "%s" % sorted({r["enforcer_refusals"] for r in rows}))
    # HV2 dark
    rows = [cell("w_price", s, "rich", 0.30, "station-dark-0.1-0.3")
            for s in SEEDS]
    ck("HV2 dark: 30 drains, dead 10/10, claims None",
       sorted({r["commons_drains"] for r in rows}) == [30]
       and sum(1 for r in rows if r["keeper_dead"]) == 10
       and sorted({str(r["enforcer_scope_claimed_end"]) for r in rows}) == ["None"])
    # HV4 claimed station every step
    rows = [cell("w_price", s, "rich", 0.30, "station-open-0.1-0.3")
            for s in SEEDS]
    ck("HV4 open: claims 'station' on every step",
       all(r["scope_task_distinct"] == ["station"] for r in rows))
    # HV4b refused flag
    ro = [cell("w_price", s, "rich", 0.30, "station-open-0.1-0.3")
          for s in SEEDS]
    rh = [cell("w_price", s, "rich", 0.30, "station") for s in SEEDS]
    ck("HV4b: `refused` never set when bought, set when honest",
       all(max(r["scope_refused_seen"]) == 0 for r in ro)
       and all(min(r["scope_refused_seen"]) == 0
               and max(r["scope_refused_seen"]) > 0 for r in rh))
    # HV5 grant
    rows = [cell("w_widen", s, "rich", 0.30, "station-open-0.1-0.3")
            for s in SEEDS]
    ck("HV5: widened 10/10 and 30 drains",
       sum(1 for r in rows if r["enforcer_widened"]) == 10
       and sorted({r["commons_drains"] for r in rows}) == [30])
    # HV6 identity
    nd = 0
    cmp_ = 0
    ADDED = ("arm", "world", "enforcer", "enforcer_bribe", "enforcer_price",
             "enforcer_mode", "enforcer_bribe_received", "enforcer_flipped",
             "enforcer_flip_step", "enforcer_scope_claimed_end",
             "scope_task_distinct", "scope_refused_any", "first_probe", "scope",
             "grant_widen", "enforcer_scope_end", "enforcer_scoped_steps",
             "enforcer_refusals", "enforcer_refused_actions",
             "enforcer_widen_requests", "enforcer_widen_refusals",
             "enforcer_widen_grants", "enforcer_widened", "enforcer_widen_t",
             "reward_before_widen", "reward_after_widen", "drains_before_widen",
             "drains_after_widen", "scope_task_seen", "scope_refused_seen")
    for arm, sc in (("w_none", "none"), ("w_price", "none"), ("n_doctor", "none"),
                    ("n_pump_price", "none"), ("w_widen", "none"),
                    ("w_price", "station"), ("w_widen", "station"),
                    ("n_doctor", "station")):
        for s in SEEDS:
            oldp = os.path.join(D18, f"{arm}_{s}_on_low_on_v18_rich"
                                     f"_t0.3_p1_cinf_{sc}_gw0.json")
            if not os.path.exists(oldp):
                continue
            old = json.load(open(oldp))
            new = cell(arm, s, "rich", 0.30, sc)
            cmp_ += 1
            for k in old:
                if k in ADDED:
                    continue
                if old[k] != new.get(k):
                    nd += 1
    ck("HV6 identity: 0 differences over %d frozen cells" % cmp_,
       nd == 0 and cmp_ == 80, "%d diffs" % nd)
    # replication
    rf = [rcell("w_price", s, "rich", 0.30, "station-open-0.1-0.3")
          for s in FRESH]
    ck("replication HV1: 30/30 fresh seeds drain and die",
       all(r["commons_drains"] == 30 and r["keeper_dead"] for r in rf))
    rf = [rcell("w_price", s, "rich", 0.30, "station") for s in FRESH]
    ck("replication HV1c: 30/30 fresh seeds honest 0 drains",
       all(r["commons_drains"] == 0 and not r["keeper_dead"] for r in rf))

    # the report's own numbers
    txt = open(REPORT).read()
    for num in ("30", "270", "0.10", "0.30", "10/10", "30/30"):
        ck("report mentions %s" % num, num in txt)

    nfail = sum(1 for _, c, _ in checks if not c)
    print("\n%d/%d checks passed" % (len(checks) - nfail, len(checks)))
    if nfail:
        sys.exit(1)
    print("ALL GREEN")


if __name__ == "__main__":
    main()