"""analyze_v20_replication.py -- do the v20 verdicts survive 30 FRESH seeds?

Reads only results/matrix_v20_replication/*.json (seeds 10..39, never used for the
frozen matrix) and the frozen matrix cells (seeds 0..9). Reports, per verdict,
whether it holds on both. No producer is imported.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DR = os.path.join(HERE, "results", "matrix_v20_replication")
D = os.path.join(HERE, "results", "matrix_bribed_enforcer_v20")
FRESH = list(range(10, 40))
FROZEN = list(range(10))


def load(d, arm, seed, place, tick, spec):
    p = os.path.join(d, f"{arm}_{seed}_on_low_on_v20_{place}"
                        f"_t{tick}_p1_cinf_{spec}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


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
    return "-".join(out)


def main():
    out = []
    def p(s):
        print(s)
        out.append(s)

    p("=== v20 replication: 30 fresh seeds (10..39) vs the frozen 10 (0..9) ===")

    cells = [
        ("HV1  bought (open)", "w_price", "rich", "0.3",
         "station-open-0.1-0.3"),
        ("HV1c honest", "w_price", "rich", "0.3", "station"),
        ("HV2  dark", "w_price", "rich", "0.3", "station-dark-0.1-0.3"),
        ("HV5  grant bought", "w_widen", "rich", "0.3", "station-open-0.1-0.3"),
    ]
    for label, arm, place, tick, spec in cells:
        fresh = [load(DR, arm, s, place, tick, spec) for s in FRESH]
        frozen = [load(D, arm, s, place, tick, spec) for s in FROZEN]
        def summary(rows):
            rows = [r for r in rows if r]
            drains = sorted({r["commons_drains"] for r in rows})
            dead = sum(1 for r in rows if r["keeper_dead"])
            wid = sum(1 for r in rows if r["enforcer_widened"])
            claims = sorted({str(r["enforcer_scope_claimed_end"]) for r in rows})
            return drains, dead, wid, claims, len(rows)
        fd, fdead, fwid, fcl, fn = summary(frozen)
        rd, rdead, rwid, rcl, rn = summary(fresh)
        p("  %-18s frozen(n=%d): drains=%s dead=%d/10 widened=%d claims=%s"
          % (label, fn, fd, fdead, fwid, fcl))
        p("  %-18s fresh (n=%d): drains=%s dead=%d/30 widened=%d claims=%s"
          % ("", rn, rd, rdead, rwid, rcl))

    p("")
    p("=== verdict by verdict ===")
    verdicts = []
    # HV1: bought -> 30/dead/0 refusals
    f = [load(DR, "w_price", s, "rich", "0.3", "station-open-0.1-0.3")
         for s in FRESH]
    f = [r for r in f if r]
    ok = all(r["commons_drains"] == 30 and r["keeper_dead"]
             and r["enforcer_refusals"] == 0 for r in f)
    verdicts.append(("HV1 OPEN bought: 30 drains, dead, 0 refusals", ok,
                     "%d/%d" % (sum(1 for r in f if r["commons_drains"] == 30
                                    and r["keeper_dead"]), len(f))))
    # HV1c: honest -> 0/dead 0/refusals>0
    f = [load(DR, "w_price", s, "rich", "0.3", "station") for s in FRESH]
    f = [r for r in f if r]
    ok = all(r["commons_drains"] == 0 and not r["keeper_dead"]
             and r["enforcer_refusals"] > 0 for r in f)
    verdicts.append(("HV1c HONEST: 0 drains, alive, refusals > 0", ok,
                     "%d/%d" % (sum(1 for r in f if r["commons_drains"] == 0
                                    and not r["keeper_dead"]), len(f))))
    # HV2: dark -> 30/dead/claim None
    f = [load(DR, "w_price", s, "rich", "0.3", "station-dark-0.1-0.3")
         for s in FRESH]
    f = [r for r in f if r]
    ok = all(r["commons_drains"] == 30 and r["keeper_dead"]
             and r["enforcer_scope_claimed_end"] is None for r in f)
    verdicts.append(("HV2 DARK: 30 drains, dead, claims None", ok,
                     "%d/%d" % (sum(1 for r in f if r["commons_drains"] == 30
                                    and r["enforcer_scope_claimed_end"] is None),
                                len(f))))
    # HV4: open claims station on EVERY step
    f = [load(DR, "w_price", s, "rich", "0.3", "station-open-0.1-0.3")
         for s in FRESH]
    f = [r for r in f if r]
    ok = all(r["scope_task_distinct"] == ["station"] for r in f)
    verdicts.append(("HV4 OPEN: claims 'station' on every step", ok,
                     "%d/%d" % (sum(1 for r in f
                                    if r["scope_task_distinct"] == ["station"]),
                                len(f))))
    # HV4b: refused flag changes (honest>0, open==0)
    f = [load(DR, "w_price", s, "rich", "0.3", "station-open-0.1-0.3")
         for s in FRESH]
    f = [r for r in f if r]
    ok = all(max(r["scope_refused_seen"]) == 0 for r in f)  # open: never refused
    verdicts.append(("HV4b OPEN: the `refused` flag is never set (honest sets it)",
                     ok, "%d/%d" % (sum(1 for r in f
                                        if max(r["scope_refused_seen"]) == 0),
                                    len(f))))
    # HV5: grant bought
    f = [load(DR, "w_widen", s, "rich", "0.3", "station-open-0.1-0.3")
         for s in FRESH]
    f = [r for r in f if r]
    ok = all(r["enforcer_widened"] and r["commons_drains"] == 30 for r in f)
    verdicts.append(("HV5 grant bought: widened and 30 drains", ok,
                     "%d/%d" % (sum(1 for r in f if r["enforcer_widened"]
                                    and r["commons_drains"] == 30), len(f))))

    for name, ok, detail in verdicts:
        p("  %-52s %s (%s)" % (name, "HOLDS" if ok else "FAILS", detail))

    with open(os.path.join(HERE, "results", "analyze_v20_replication.txt"),
              "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("WROTE results/analyze_v20_replication.txt")


if __name__ == "__main__":
    main()