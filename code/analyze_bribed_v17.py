"""analyze_bribed_v17.py -- the BRIBED-AUDITOR verdicts (turn 152), prereg §5.

Reads only results/matrix_bribed_v17/*.json and the frozen v14 cells. Prints a
machine-readable summary and the HB1-HB7 verdicts. No producer is imported.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_bribed_v17")
D14 = os.path.join(HERE, "results", "matrix_attested_v14")
SEEDS = list(range(10))
PRICE_GRID = (0.0, 0.10, 0.30, 0.60)
BRIBE_GRID = (0.0, 0.10, 0.30, 0.60)


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def norm_auditor_spec(spec):
    """The runner normalises the auditor spec through `fmt`, so the same
    configuration has exactly one filename; mirror that here (declared)."""
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


def load(arm, seed, place, tick, tag, au):
    p = os.path.join(D, f"{arm}_{seed}_on_low_on_v17_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{tag}_wrdef_au"
                        f"{norm_auditor_spec(au)}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


V17_ADDED = ("arm", "world", "auditor", "auditor_price", "auditor_mode",
             "auditor_bribe", "auditor_bribe_received", "auditor_flipped",
             "auditor_flip_step", "first_probe")


def harm(c):
    return {"drains": c["commons_drains"], "keeper_dead": c["keeper_dead"],
            "left": c["commons_left"]}


def main():
    out = []
    def p(s):
        print(s)
        out.append(s)

    # ---------------- HB6: identity with frozen v14 ----------------
    # Enumerate the FROZEN v14 cells on disk and check each one against its v17
    # counterpart where the v17 matrix carries the same configuration AND no second
    # knob is needed. Coverage is reported, so a missing counterpart cannot hide as
    # a pass. The `world_rich_rate` cells of v14 (HA6/HA7) are NOT re-run here --
    # they need a second knob -- and they are counted as skipped, visibly.
    p("=== HB6: v17(honest) vs the frozen v14 cells (by path) ===")
    checked = 0
    nd_total = 0
    skipped = []
    for oldp in sorted(glob.glob(os.path.join(D14, "*.json"))):
        old = json.load(open(oldp))
        arm = old.get("arm")
        if arm not in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
            continue
        if old.get("world") != "v14":
            continue
        if old.get("world_rich_rate") is not None:
            skipped.append(os.path.basename(oldp))
            continue
        au = old.get("auditor")
        if au not in (None, "none", "live"):
            skipped.append(os.path.basename(oldp))
            continue
        tag = old.get("tag", "foreign")
        au_spec = "none" if au in (None, "none") else au
        new = load(arm, old["seed"], old["place"], old["tick"], tag, au_spec)
        if new is None:
            skipped.append(os.path.basename(oldp))
            continue
        checked += 1
        for k in old:
            if k in V17_ADDED:
                continue
            if old[k] != new.get(k):
                nd_total += 1
                p("  DIFF %s: %s %r vs %r" % (os.path.basename(oldp), k,
                                              old[k], new.get(k)))
    p("  %d frozen v14 cells compared; %d field differences total; %d skipped "
      "(no counterpart or a second knob)" % (checked, nd_total, len(skipped)))

    # ---------------- HB1/HB2/HB3: the three modes ----------------
    p("=== HB1/HB2/HB3: the bought auditor (flip and silent) ===")
    p("  %-14s %-13s %-8s %-8s %-8s %-10s" % ("mode", "arm", "left", "drains",
                                              "keeper", "stat@dec"))
    for mode, au in (("honest", "live"), ("flip", "flip:0.10:0.30"),
                     ("silent", "silent:0.10:0.30")):
        for arm in ("a_believe", "a_failclosed"):
            lefts, drains, dead, stats = [], [], 0, []
            for s in SEEDS:
                c = load(arm, s, "rich", 0.30, "world", au)
                lefts.append(c["commons_left"])
                drains.append(c["commons_drains"])
                dead += 1 if c["keeper_dead"] else 0
                stats.append(c["rate_at_first_decision"])
            p("  %-14s %-13s %-8s %-8s %-8s %-10s" %
              (mode, arm, "%s" % (lefts[0] if len(set(lefts)) == 1 else lefts),
               "%s" % (drains[0] if len(set(drains)) == 1 else drains),
               "%d/10" % dead,
               "%s" % (stats[0] if len(set(stats)) == 1 else stats)))

    # ---------------- HB4: the price x bribe grid ----------------
    p("=== HB4: the price x bribe grid (mode flip, a_believe) ===")
    p("  price\\bribe  " + "  ".join("%6s" % b for b in BRIBE_GRID))
    for price in PRICE_GRID:
        row = []
        for bribe in BRIBE_GRID:
            au = "flip:%s:%s" % (price, bribe)
            drains = [load("a_believe", s, "rich", 0.30, "world", au)["commons_drains"]
                      for s in SEEDS]
            flips = [load("a_believe", s, "rich", 0.30, "world", au)["auditor_flipped"]
                     for s in SEEDS]
            row.append("%d/%s" % (drains[0], "F" if flips[0] else "-"))
        p("  %-11s  " % price + "  ".join("%6s" % x for x in row))
    p("  (cell = drains / F if the auditor flipped)")

    # ---------------- HB5: the failure is invisible in the flag ----------------
    p("=== HB5: the attested flag and the honest label ===")
    for mode, au in (("honest", "live"), ("flip", "flip:0.10:0.30"),
                     ("silent", "silent:0.10:0.30")):
        c = load("a_believe", 0, "rich", 0.30, "world", au)
        p("  %-8s live_steps=%s attested_seen=%s attested_rich=%s "
          "unattested_rich=%s" %
          (mode, c["auditor_live_steps"], c["attested_steps_seen"],
           c["attested_rich_steps"], c["unattested_rich_steps"]))
    # flip with the honest label must equal honest
    for arm in ("a_believe", "a_failclosed"):
        nd = 0
        for s in SEEDS:
            a = load(arm, s, "rich", 0.30, "foreign", "flip:0.10:0.30")
            b = load(arm, s, "rich", 0.30, "foreign", "live")
            for k in b:
                if k in ("arm", "world", "auditor", "auditor_price",
                         "auditor_mode", "auditor_bribe", "auditor_bribe_received",
                         "auditor_flipped", "auditor_flip_step", "first_probe"):
                    continue
                if a.get(k) != b[k]:
                    nd += 1
        p("  %s: flip vs honest with tag='foreign': %d field differences" %
          (arm, nd))

    # ---------------- HB7: non-vacuity and the counterfactual ----------------
    p("=== HB7: non-vacuity and the counterfactual ===")
    for au in ("flip:0.10:0.30", "silent:0.10:0.30"):
        c = load("a_believe", 0, "rich", 0.30, "world", au)
        h = load("a_believe", 0, "rich", 0.30, "world", "live")
        p("  %-18s live_steps=%d bribe_received=%.2f flipped=%s "
          "| counterfactual(honest) drains=%d left=%d" %
          (au, c["auditor_live_steps"], c["auditor_bribe_received"],
           c["auditor_flipped"], h["commons_drains"], h["commons_left"]))

    with open(os.path.join(HERE, "results", "analyze_bribed_v17.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("WROTE results/analyze_bribed_v17.txt")


if __name__ == "__main__":
    main()
