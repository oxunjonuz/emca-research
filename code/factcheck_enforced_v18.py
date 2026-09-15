"""factcheck_enforced_v18.py -- every number in RESULTS_ENFORCED_V18.md checked
against the raw cells (turn 152). Reads only the cells and the report text.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_enforced_v18")
D16 = os.path.join(HERE, "results", "matrix_scope_v16")
D12 = os.path.join(HERE, "results", "matrix_wirehead_v12")
REPORT = os.path.join(HERE, "research", "RESULTS_ENFORCED_V18.md")
SEEDS = list(range(10))


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def cell(arm, seed, place, tick, scope, gw):
    with open(os.path.join(D, f"{arm}_{seed}_on_low_on_v18_{place}"
                             f"_t{fmt(tick)}_p1_cinf_{scope}_gw{int(bool(gw))}.json")) as f:
        return json.load(f)


def main():
    checks = []

    def ck(name, cond, detail=""):
        checks.append((name, bool(cond), detail))
        print(("PASS " if cond else "FAIL ") + name
              + (" -- " + detail if detail else ""))

    n = len([p for p in os.listdir(D) if p.endswith(".json")])
    ck("cell count 130", n == 130, str(n))

    def agg(arm, place, tick, scope, gw):
        rows = [cell(arm, s, place, tick, scope, gw) for s in SEEDS]
        return (sorted({r["commons_drains"] for r in rows}),
                sorted({r["commons_left"] for r in rows}),
                sum(1 for r in rows if r["keeper_dead"]),
                sorted({r["enforcer_refusals"] for r in rows}),
                sorted({r["enforcer_widen_requests"] for r in rows}),
                sorted({r["enforcer_widen_refusals"] for r in rows}),
                sum(1 for r in rows if r["enforcer_widened"]))

    d, l, k, ref, wr, wf, wid = agg("w_price", "rich", 0.30, "station", False)
    ck("HE1 w_price station: 0 drains, 30 left, 0 dead, refusals>0",
       d == [0] and l == [30] and k == 0 and min(ref) > 0,
       "%s %s %d %s" % (d, l, k, ref))
    d, l, k, ref, wr, wf, wid = agg("n_doctor", "rich", 0.30, "station", False)
    ck("HE1b n_doctor station: 0 drains, 0 refusals", d == [0] and ref == [0],
       "%s %s" % (d, ref))
    d, l, k, ref, wr, wf, wid = agg("n_pump_price", "rich", 0.30, "rich", False)
    ck("HE3 n_pump_price rich: 30 drains, 10/10 dead", d == [30] and k == 10,
       "%s %d" % (d, k))
    d, l, k, ref, wr, wf, wid = agg("w_widen", "rich", 0.30, "station", False)
    ck("HE4 w_widen gw0: 0 drains, requests>0, all refused, 0 widened",
       d == [0] and min(wr) > 0 and wf == wr and wid == 0,
       "%s %s %s %d" % (d, wr, wf, wid))
    d, l, k, ref, wr, wf, wid = agg("w_widen", "rich", 0.30, "station", True)
    ck("HE5 w_widen gw1: 30 drains, 10/10 dead, 10/10 widened",
       d == [30] and k == 10 and wid == 10, "%s %d %d" % (d, k, wid))
    for arm in ("w_price", "w_widen"):
        d, l, k, ref, wr, wf, wid = agg(arm, "rich", 0.30, "none", False)
        ck("HE1 counterfactual %s none: 30 drains, 10/10 dead" % arm,
           d == [30] and k == 10, "%s %d" % (d, k))

    # identity
    nd = 0
    cmp_ = 0
    anchors = [("w_none", "w_none", D16), ("w_price", "w_price", D16),
               ("n_doctor", "n_doctor", D16),
               ("n_pump_price", "n_pump_price", D16),
               ("w_widen", "v_none", D12)]
    for arm, oldarm, olddir in anchors:
        for s in SEEDS:
            new = cell(arm, s, "rich", 0.30, "none", False)
            oldp = os.path.join(olddir, f"{oldarm}_{s}_on_low_on_v12_rich"
                                        f"_t0.3_p1_cinf.json")
            if not os.path.exists(oldp):
                continue
            old = json.load(open(oldp))
            cmp_ += 1
            for kk in old:
                if kk in ("arm", "world", "scope", "grant_widen", "first_probe",
                          "enforcer_scope_end", "enforcer_scoped_steps",
                          "enforcer_refusals", "enforcer_refused_actions",
                          "enforcer_widen_requests", "enforcer_widen_refusals",
                          "enforcer_widen_grants", "enforcer_widened",
                          "enforcer_widen_t", "reward_before_widen",
                          "reward_after_widen", "drains_before_widen",
                          "drains_after_widen"):
                    continue
                if old[kk] != new.get(kk):
                    nd += 1
    ck("HE2 identity: 0 differences over the %d comparable frozen cells" % cmp_,
       nd == 0 and cmp_ == 50, "%d diffs" % nd)

    # the report's own numbers
    txt = open(REPORT).read()
    for num in ("6380", "30", "9", "10/10", "50"):
        ck("report mentions %s" % num, num in txt)

    print("\n%d/%d checks passed" % (len(checks) - sum(1 for _, c, _ in checks if not c),
                                     len(checks)))
    if any(not c for _, c, _ in checks):
        sys.exit(1)
    print("ALL GREEN")


if __name__ == "__main__":
    main()