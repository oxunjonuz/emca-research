"""analyze_enforced_v18.py -- the ENFORCED-SCOPE verdicts (turn 152), prereg §4.

Reads only results/matrix_enforced_v18/*.json and the frozen v16/v12 cells. Prints a
machine-readable summary and the HE1-HE7 verdicts. No producer is imported.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_enforced_v18")
D16 = os.path.join(HERE, "results", "matrix_scope_v16")
SEEDS = list(range(10))


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def load(arm, seed, place, tick, scope, gw):
    p = os.path.join(D, f"{arm}_{seed}_on_low_on_v18_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{scope}_gw{int(bool(gw))}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def v16_path(arm, seed, place, tick):
    return os.path.join(D16, f"{arm}_{seed}_on_low_on_v12_{place}"
                             f"_t{fmt(tick)}_p1_cinf.json")


def main():
    out = []
    def p(s):
        print(s)
        out.append(s)

    def verdicts(arm, place, tick, scope, gw):
        rows = [load(arm, s, place, tick, scope, gw) for s in SEEDS]
        return {
            "drains": {r["commons_drains"] for r in rows},
            "left": {r["commons_left"] for r in rows},
            "dead": sum(1 for r in rows if r["keeper_dead"]),
            "refusals": {r["enforcer_refusals"] for r in rows},
            "widen_req": {r["enforcer_widen_requests"] for r in rows},
            "widen_ref": {r["enforcer_widen_refusals"] for r in rows},
            "widened": sum(1 for r in rows if r["enforcer_widened"]),
        }

    # ---------------- HE2 anchor: no enforcement == the frozen cells ----------------
    # `w_widen` is new, so it has no v16 counterpart; with scope=none the widening
    # request is not affordable, so the arm reduces to the frozen base and must equal
    # the FROZEN v12 `v_none` cell.
    p("=== HE2 anchor: scope=none must reproduce the frozen v16/v12 cells ===")
    anchors = [("w_none", "w_none", D16), ("w_price", "w_price", D16),
               ("n_doctor", "n_doctor", D16),
               ("n_pump_price", "n_pump_price", D16),
               ("w_widen", "v_none", os.path.join(HERE, "results",
                                                  "matrix_wirehead_v12"))]
    for arm, oldarm, olddir in anchors:
        nd = 0
        cmp_ = 0
        for s in SEEDS:
            new = load(arm, s, "rich", 0.30, "none", False)
            oldp = os.path.join(olddir, f"{oldarm}_{s}_on_low_on_"
                                        f"{'v12' if olddir == D16 else 'v12'}_rich"
                                        f"_t0.3_p1_cinf.json")
            if olddir == D16:
                oldp = v16_path(oldarm, s, "rich", 0.30)
            else:
                oldp = os.path.join(olddir, f"{oldarm}_{s}_on_low_on_v12_rich"
                                            f"_t0.3_p1_cinf.json")
            if not os.path.exists(oldp):
                continue
            old = json.load(open(oldp))
            cmp_ += 1
            for k in old:
                if k in ("arm", "world", "scope", "grant_widen", "first_probe",
                         "enforcer_scope_end", "enforcer_scoped_steps",
                         "enforcer_refusals", "enforcer_refused_actions",
                         "enforcer_widen_requests", "enforcer_widen_refusals",
                         "enforcer_widen_grants", "enforcer_widened",
                         "enforcer_widen_t", "reward_before_widen",
                         "reward_after_widen", "drains_before_widen",
                         "drains_after_widen"):
                    continue
                if old[k] != new.get(k):
                    nd += 1
                    p("  DIFF %s s%d %s: %r vs %r" % (arm, s, k, old[k],
                                                      new.get(k)))
        p("  %-14s vs frozen %-14s (scope=none): %d cells, %d field differences"
          % (arm, oldarm, cmp_, nd))

    # ---------------- the verdict table ----------------
    p("=== HE1/HE1b/HE3/HE4/HE5: the boundary, per arm and scope ===")
    p("  %-14s %-8s %-3s | %-6s %-6s %-6s %-8s %-9s %-9s %-7s" %
      ("arm", "scope", "gw", "drains", "left", "dead", "refusals", "widen_req",
       "widen_ref", "widened"))
    cases = [
        ("w_price", "station", False), ("w_widen", "station", False),
        ("n_doctor", "station", False), ("n_pump_price", "rich", False),
        ("w_widen", "station", True), ("w_price", "station", True),
        ("w_none", "none", False), ("w_price", "none", False),
        ("w_widen", "none", False),
    ]
    for arm, scope, gw in cases:
        v = verdicts(arm, "rich", 0.30, scope, gw)
        def sh(x):
            return str(x) if len(x) == 1 else str(sorted(x))
        p("  %-14s %-8s %-3s | %-6s %-6s %-6s %-8s %-9s %-9s %-7s" %
          (arm, scope, int(gw), sh(v["drains"]), sh(v["left"]), "%d/10" % v["dead"],
           sh(v["refusals"]), sh(v["widen_req"]), sh(v["widen_ref"]),
           "%d/10" % v["widened"]))

    # ---------------- HE6: no forger, no reason to try ----------------
    # REFUTED for the w_widen arm, and reported as refuted: its escape policy fires
    # on the harmful TILE, not on a payment, so with no forger it still asks 30+ times
    # (and the world still refuses, harmlessly). Only the doctor, whose harm comes
    # from capability, never asks. Kept because a preregistration that is never wrong
    # was not written before the run.
    p("=== HE6: with no forger, does the agent still ask? (REFUTED for w_widen) ===")
    for arm in ("n_doctor", "w_widen"):
        v = verdicts(arm, "none", 0.0, "station", False)
        p("  %-12s place=none: drains=%s left=%s refusals=%s widen_req=%s widened=%d"
          % (arm, v["drains"], v["left"], v["refusals"], v["widen_req"],
             v["widened"]))

    # ---------------- HE5: harm before/after the grant ----------------
    p("=== HE5: the harm before and after a GRANTED widening ===")
    for s in SEEDS[:3]:
        c = load("w_widen", s, "rich", 0.30, "station", True)
        p("  seed %d: widen_t=%s drains_before=%d drains_after=%d widened=%s"
          % (s, c["enforcer_widen_t"], c["drains_before_widen"],
             c["drains_after_widen"], c["enforcer_widened"]))

    with open(os.path.join(HERE, "results", "analyze_enforced_v18.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("WROTE results/analyze_enforced_v18.txt")


if __name__ == "__main__":
    main()