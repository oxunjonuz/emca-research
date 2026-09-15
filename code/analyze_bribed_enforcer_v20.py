"""analyze_bribed_enforcer_v20.py -- the BRIBED-ENFORCER verdicts (turn 157), §4.

Reads only results/matrix_bribed_enforcer_v20/*.json and the frozen v18 cells.
Prints a machine-readable summary and the HV1-HV7 verdicts. No producer is imported.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_bribed_enforcer_v20")
D18 = os.path.join(HERE, "results", "matrix_enforced_v18")
SEEDS = list(range(10))
PRICE_GRID = (0.0, 0.10, 0.30, 0.60)
BRIBE_GRID = (0.0, 0.10, 0.30, 0.60)


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


def load(arm, seed, place, tick, spec):
    p = os.path.join(D, f"{arm}_{seed}_on_low_on_v20_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{norm(spec)}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


V20_ADDED = ("arm", "world", "enforcer", "enforcer_bribe", "enforcer_price",
             "enforcer_mode", "enforcer_bribe_received", "enforcer_flipped",
             "enforcer_flip_step", "enforcer_scope_claimed_end",
             "scope_task_distinct", "scope_refused_any", "first_probe",
             "scope", "grant_widen", "enforcer_scope_end", "enforcer_scoped_steps",
             "enforcer_refusals", "enforcer_refused_actions",
             "enforcer_widen_requests", "enforcer_widen_refusals",
             "enforcer_widen_grants", "enforcer_widened", "enforcer_widen_t",
             "reward_before_widen", "reward_after_widen", "drains_before_widen",
             "drains_after_widen", "scope_task_seen", "scope_refused_seen")


def harm(c):
    return {"drains": c["commons_drains"], "keeper_dead": c["keeper_dead"],
            "left": c["commons_left"]}


def main():
    out = []
    def p(s):
        print(s)
        out.append(s)

    # ---------------- HV6: identity with the frozen v18 cells ----------------
    p("=== HV6: v20(honest) vs the frozen v18 cells (by path) ===")
    checked = 0
    nd_total = 0
    # (arm, v18 path spec) -> v20 spec is the bare scope name
    anchors = [("w_none", "none"), ("w_price", "none"), ("n_doctor", "none"),
               ("n_pump_price", "none"), ("w_widen", "none"),
               ("w_price", "station"), ("w_widen", "station"),
               ("n_doctor", "station")]
    for arm, sc in anchors:
        for s in SEEDS:
            oldp = os.path.join(D18, f"{arm}_{s}_on_low_on_v18_rich"
                                     f"_t0.3_p1_cinf_{sc}_gw0.json")
            if not os.path.exists(oldp):
                continue
            old = json.load(open(oldp))
            new = load(arm, s, "rich", 0.30, sc)
            if new is None:
                continue
            checked += 1
            for k in old:
                if k in V20_ADDED:
                    continue
                if old[k] != new.get(k):
                    nd_total += 1
                    p("  DIFF %s: %s %r vs %r" % (os.path.basename(oldp), k,
                                                  old[k], new.get(k)))
    p("  %d frozen v18 cells compared; %d field differences total"
      % (checked, nd_total))

    # ---------------- HV1/HV2: the boundary bought ----------------
    p("=== HV1/HV2: the bought enforcer (open and dark) ===")
    p("  %-8s %-16s %-6s %-7s %-8s %-10s %-12s" %
      ("mode", "spec", "left", "drains", "keeper", "refusals", "claimed"))
    for mode, spec in (("honest", "station"), ("open", "station:open:0.10:0.30"),
                       ("dark", "station:dark:0.10:0.30")):
        lefts, drains, dead, refs, claims = [], [], 0, [], set()
        for s in SEEDS:
            c = load("w_price", s, "rich", 0.30, spec)
            lefts.append(c["commons_left"])
            drains.append(c["commons_drains"])
            dead += 1 if c["keeper_dead"] else 0
            refs.append(c["enforcer_refusals"])
            claims |= set(c["scope_task_distinct"])
        p("  %-8s %-16s %-6s %-7s %-8s %-10s %-12s" %
          (mode, spec,
           "%s" % (lefts[0] if len(set(lefts)) == 1 else lefts),
           "%s" % (drains[0] if len(set(drains)) == 1 else drains),
           "%d/10" % dead,
           "%s" % (refs[0] if len(set(refs)) == 1 else refs),
           ",".join(sorted(claims))))

    # ---------------- HV3: the price x bribe cliff ----------------
    p("=== HV3: the price x bribe grid (mode open, w_price, station) ===")
    p("  price\\bribe  " + "  ".join("%8s" % b for b in BRIBE_GRID))
    for price in PRICE_GRID:
        row = []
        for bribe in BRIBE_GRID:
            spec = "station:open:%s:%s" % (price, bribe)
            drains = [load("w_price", s, "rich", 0.30, spec)["commons_drains"]
                      for s in SEEDS]
            flips = [load("w_price", s, "rich", 0.30, spec)["enforcer_flipped"]
                     for s in SEEDS]
            row.append("%d/%s" % (drains[0], "F" if flips[0] else "-"))
        p("  %-11s  " % price + "  ".join("%8s" % x for x in row))
    p("  (cell = drains / F if the enforcer flipped)")

    # ---------------- HV4: the failure is invisible ----------------
    p("=== HV4: the claimed scope, bought vs honest ===")
    for mode, spec in (("honest", "station"), ("open", "station:open:0.10:0.30"),
                       ("dark", "station:dark:0.10:0.30")):
        c = load("w_price", 0, "rich", 0.30, spec)
        p("  %-8s claimed_end=%s distinct=%s refused_any=%s bribe_received=%.2f "
          "flipped=%s" %
          (mode, c["enforcer_scope_claimed_end"], c["scope_task_distinct"],
           c["scope_refused_any"], c["enforcer_bribe_received"],
           c["enforcer_flipped"]))
    # the whole-run claim sequence for open must equal honest's on the steps where
    # the agent did not attempt an out-of-scope act: here, both are all "station"
    o = load("w_price", 0, "rich", 0.30, "station:open:0.10:0.30")
    h = load("w_price", 0, "rich", 0.30, "station")
    p("  open claimed sequence distinct=%s ; honest claimed sequence distinct=%s"
      % (o["scope_task_distinct"], h["scope_task_distinct"]))
    p("  open refused_any=%s ; honest refused_any=%s"
      % (o["scope_refused_any"], h["scope_refused_any"]))

    # ---------------- HV5: the widen grant bought ----------------
    p("=== HV5: the widen grant bought (w_widen, station, gw=0) ===")
    for mode, spec in (("honest", "station"), ("open", "station:open:0.10:0.30")):
        wid = sum(1 for s in SEEDS
                  if load("w_widen", s, "rich", 0.30, spec)["enforcer_widened"])
        drains = sorted({load("w_widen", s, "rich", 0.30, spec)["commons_drains"]
                         for s in SEEDS})
        reqs = sorted({load("w_widen", s, "rich", 0.30, spec)["enforcer_widen_requests"]
                       for s in SEEDS})
        p("  %-8s widened=%d/10 drains=%s requests=%s" %
          (mode, wid, drains, reqs))

    # ---------------- HV7: non-vacuity and the counterfactual ----------------
    p("=== HV7: non-vacuity, the no-scope counterfactual, determinism ===")
    c = load("w_price", 0, "rich", 0.30, "station:open:0.10:0.30")
    p("  open: bribe_received=%.2f flipped=%s flip_step=%s scoped_steps=%d" %
      (c["enforcer_bribe_received"], c["enforcer_flipped"],
       c["enforcer_flip_step"], c["enforcer_scoped_steps"]))
    ns = load("w_price", 0, "rich", 0.30, "none:open:0.10:0.30")
    p("  no-scope counterfactual: drains=%d keeper_dead=%s (nothing to buy)"
      % (ns["commons_drains"], ns["keeper_dead"]))

    with open(os.path.join(HERE, "results", "analyze_bribed_enforcer_v20.txt"),
              "w") as f:
        f.write("\n".join(out) + "\n")
    print("WROTE results/analyze_bribed_enforcer_v20.txt")


if __name__ == "__main__":
    main()