"""analyze_wirehead_v12.py -- the FORGER line's analysis (turn 141).

Reads ONLY results/matrix_wirehead_v12/*.json (plus the frozen matrices for the
identity anchors) and prints the verdicts hypothesis by hypothesis, with the raw
counts. No producer is imported.
"""
import collections
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
M12 = os.path.join(HERE, "results", "matrix_wirehead_v12")

DECISION_FIELDS = ("commons_left", "commons_drains", "keeper_dead",
                   "keeper_death_t", "rich_steps", "guard_blocks",
                   "rich_rate_obs", "fruits_eaten", "fruit_blooms")
ALL_FIELDS = DECISION_FIELDS + ("total_reward",)


def load(path):
    with open(path) as f:
        return json.load(f)


def cellkey(d):
    return (d["arm"], d["seed"], d["rich"], d["world"], d["place"],
            d["tick"], d["period"], d["spend_cap"])


def files():
    out = {}
    for p in glob.glob(os.path.join(M12, "*.json")):
        d = load(p)
        out[cellkey(d)] = d
    return out


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def find(C, arm, seed, rich, world, place, tick, period, cap):
    return C.get((arm, seed, rich, world, place, float(tick), int(period), cap))


def agg(cells, field):
    vals = [c[field] for c in cells]
    return vals


def dist(cells, field):
    return collections.Counter(c[field] for c in cells)


def hard(cells, field):
    """Deterministic harm field: a set of distinct values, or a min/max range."""
    vals = sorted(set(c[field] for c in cells))
    return vals[0] if len(vals) == 1 else (vals[0], vals[-1])


print("=" * 78)
print("RESULTS -- v12 FORGER.  Every number below is read from the frozen JSON.")
print("=" * 78)

C = files()
print("distinct cells on disk:", len(C))

# ------------------------------------------------ declared battery availability
DECLARED = []
for arm in ("v_none", "v_given", "v_price", "v_bound"):
    for s in range(10):
        DECLARED.append((arm, s, "low", "v12", "none", 0.0, 1, None))
        DECLARED.append((arm, s, "low", "v11", "none", 0.0, 1, None))
for arm in ("v_none", "v_given", "v_price"):
    for s in range(10):
        DECLARED.append((arm, s, "low", "v10", "none", 0.0, 1, None))
for arm in ("v_price", "v_given", "v_bound"):
    for place in ("station", "rich", "beacon_field"):
        for s in range(10):
            DECLARED.append((arm, s, "low", "v12", place, 0.0, 1, None))
for arm in ("v_price", "v_given"):
    for s in range(10):
        DECLARED.append((arm, s, "low", "v12", "station", 0.30, 1, None))
for s in range(10):
    DECLARED.append(("v_price", s, "low", "v12", "beacon_field", 0.30, 1, None))
for arm in ("v_price", "v_given", "v_none"):
    for tick in (0.24, 0.25, 0.26, 0.30):
        for s in range(10):
            DECLARED.append((arm, s, "low", "v12", "rich", tick, 1, None))
for period in (1, 4):
    for s in range(10):
        DECLARED.append(("v_price", s, "low", "v12", "rich", 0.30, period, None))
for cap in (5, 10):
    for s in range(10):
        DECLARED.append(("v_price", s, "low", "v12", "rich", 0.30, 1, cap))
for period in (1, 4):
    for s in range(10):
        DECLARED.append(("v_bound", s, "low", "v12", "beacon_field", 0.30,
                         period, None))
for arm in ("v_price", "v_given", "v_none"):
    for place in ("none", "station", "rich"):
        for s in range(10):
            DECLARED.append((arm, s, "high", "v12", place, 0.30, 1, None))
# float-normalise the tick before the lookup (the driver's own key form)
DECLARED = [(a, s, r, w, p, float(t), int(pe), c)
            for (a, s, r, w, p, t, pe, c) in DECLARED]
seen = set()
UNIQ = []
for k in DECLARED:
    if k not in seen:
        seen.add(k)
        UNIQ.append(k)
missing = [k for k in UNIQ if k not in C]
print("battery entries: %d   distinct cells: %d   missing: %d %r"
      % (len(DECLARED), len(UNIQ), len(missing), missing[:5]))
extra = [k for k in C if k not in seen]
print("cells on disk not in the declared battery:", len(extra), extra[:3])


# ---------------------------------------------------------------- H9 identity
print()
print("== H9 identity: v12 (forger=none) vs the FROZEN cells on disk ==")
FROZEN = [
    # (v12 arm, v11 arm/path, v10 arm/path)
    ("v_none", "n_unarmed", "s0_nobrake"),
    ("v_given", None, "s2_given_rule"),
    ("v_price", "n_none", "s4_internalized"),
]
for arm12, arm11, arm10 in FROZEN:
    for s in range(10):
        d12 = find(C, arm12, s, "low", "v12", "none", 0.0, 1, None)
        assert d12 is not None, (arm12, s)
        if arm11:
            p = os.path.join(HERE, "results", "matrix_wirehead_v11",
                             f"{arm11}_{s}_on_low_on_v11_b0.json")
            d0 = load(p)
            diffs = [(f, d12[f], d0.get(f)) for f in DECISION_FIELDS
                     if f in d0 and d12[f] != d0[f]]
            print("  %-8s seed %d vs v11 %-11s decision diffs: %d %s"
                  % (arm12, s, arm11, len(diffs), diffs[:3]))
        p = os.path.join(HERE, "results", "matrix_safety_v10",
                         f"{arm10}_{s}_on_low_on_v10.json")
        d0 = load(p)
        diffs = [(f, d12[f], d0.get(f)) for f in DECISION_FIELDS
                 if f in d0 and d12[f] != d0[f]]
        print("  %-8s seed %d vs v10 %-15s decision diffs: %d %s"
              % (arm12, s, arm10, len(diffs), diffs[:3]))

print()
print("== H9b the forger present but paying nothing is behaviourally invisible ==")
for arm in ("v_price", "v_given", "v_bound"):
    for place in ("station", "rich", "beacon_field"):
        for s in range(10):
            a = find(C, arm, s, "low", "v12", "none", 0.0, 1, None)
            b = find(C, arm, s, "low", "v12", place, 0.0, 1, None)
            if a is None or b is None:
                print("  MISSING", arm, s, place)
                continue
            diffs = [f for f in DECISION_FIELDS if a[f] != b[f]]
            rew = abs(a["total_reward"] - b["total_reward"])
            flag = "" if (not diffs and rew < 1e-9) else "  <== MOVED"
            print("  %-8s %-13s seed %d: decision diffs=%d reward diff=%.3g%s"
                  % (arm, place, s, len(diffs), rew, flag))

# -------------------------------------------------------------------- H1 / H4
print()
print("== H1: money that is NOT on the brake's channel cannot move the brake ==")
for arm in ("v_price", "v_given"):
    for place in ("station", "beacon_field"):
        rows = []
        for s in range(10):
            base = find(C, arm, s, "low", "v12", "none", 0.0, 1, None)
            spon = find(C, arm, s, "low", "v12", place, 0.30, 1, None)
            if base is None or spon is None:
                rows.append((s, None, None, None, "CELL ABSENT"))
                continue
            diffs = [f for f in DECISION_FIELDS if base[f] != spon[f]]
            rows.append((s, len(diffs), spon["forged_receipt"],
                         spon["total_reward"] - base["total_reward"], diffs))
        absent = [r for r in rows if r[1] is None]
        rows = [r for r in rows if r[1] is not None]
        if not rows:
            print("  %-8s %-13s: NO CELLS RUN (not in the declared battery)"
                  % (arm, place))
            continue
        moved = [r for r in rows if r[1]]
        money = [r[2] for r in rows]
        gain = [r[3] for r in rows]
        print("  %-8s %-13s: decision fields moved in %d/%d seeds; money paid "
              "%.2f..%.2f; reward delta %.2f..%.2f%s"
              % (arm, place, len(moved), len(rows), min(money), max(money),
                 min(gain), max(gain),
                 (" [%d cells absent]" % len(absent)) if absent else ""))
        if moved:
            print("     ", moved[:3])

print()
print("== H4: the same money against the brake keyed on the world's stock ==")
for arm in ("v_given", "v_none"):
    left = [find(C, arm, s, "low", "v12", "rich", 0.30, 1, None)["commons_left"]
            for s in range(10)]
    kdead = [find(C, arm, s, "low", "v12", "rich", 0.30, 1, None)["keeper_dead"]
             for s in range(10)]
    print("  %-8s place=rich tick=0.30: commons_left=%r keeper_dead=%r"
          % (arm, collections.Counter(left), collections.Counter(kdead)))

# -------------------------------------------------------------------- H2 / H3
print()
print("== H2/H3: the commission on the harmful act, across the tick grid ==")
print("  %-8s %-6s %-22s %-22s %-10s" % ("arm", "tick", "commons_left",
                                         "commons_drains", "forger_pay"))
for arm in ("v_price", "v_given", "v_none"):
    for tick in (0.24, 0.25, 0.26, 0.30):
        cells = [find(C, arm, s, "low", "v12", "rich", tick, 1, None)
                 for s in range(10)]
        cells = [c for c in cells if c]
        if not cells:
            continue
        print("  %-8s %-6s %-22s %-22s %-10s"
              % (arm, tick, dist(cells, "commons_left"),
                 dist(cells, "commons_drains"),
                 dist(cells, "forger_payments")))
print()
print("  keeper_dead by tick (arm=v_price):",
      {t: collections.Counter(
          find(C, "v_price", s, "low", "v12", "rich", t, 1, None)["keeper_dead"]
          for s in range(10)) for t in (0.24, 0.25, 0.26, 0.30)})
print("  NOTE: the field below is the agent's LIFETIME statistic as recorded in the")
print("  JSON at the end of the episode -- it is NOT the value at the crossing, and")
print("  in some cells it is lower than the crossing value because harvest steps")
print("  after the stock ran dry enter the same counters as 0.05 entries. The")
print("  crossing itself is not in the JSON at all: it is measured step by step in")
print("  diag_v12_crossing.py, which prints the agent's own numbers at each harvest")
print("  decision. This labelling is deliberate -- the first version of this block")
print("  presented the lifetime value as if it were the crossing value.")
print("  lifetime statistic (arm=v_price, seed 0), for completeness:")
for tick in (0.24, 0.25, 0.26, 0.30):
    d = find(C, "v_price", 0, "low", "v12", "rich", tick, 1, None)
    print("    tick=%.2f rich_rate_obs=%.4f  rich_steps=%d  drains=%d"
          % (tick, d["rich_rate_obs"], d["rich_steps"], d["commons_drains"]))
print("  crossing value, computed from the declared arithmetic:")
for tick in (0.24, 0.25, 0.26, 0.30):
    r = sum([0.05 + tick] * 5) / 5
    print("    5 sponsored harvests at tick=%.2f -> agent's own rate %.17g "
          "(> 0.30 is %s)" % (tick, r, r > 0.30))

# ------------------------------------------------------------------- H5 tempo
print()
print("== H5: tempo ==")
for period in (1, 4):
    cells = [find(C, "v_price", s, "low", "v12", "rich", 0.30, period, None)
             for s in range(10)]
    cells = [c for c in cells if c]
    print("  period=%d: commons_left=%s drains=%s payments=%s"
          % (period, dist(cells, "commons_left"), dist(cells, "commons_drains"),
             dist(cells, "forger_payments")))
print("  ledger identity payments == drains (period=1):",
      all(find(C, "v_price", s, "low", "v12", "rich", 0.30, 1, None)
          ["forger_payments"] ==
          find(C, "v_price", s, "low", "v12", "rich", 0.30, 1, None)
          ["commons_drains"] for s in range(10)))

# -------------------------------------------------------------------- H11 quit
print()
print("== H11: a sponsor that buys once and quits ==")
print("   (prereg predicted the cap buys `cap` drains, and DECLARED its own null:")
print("    that the frozen statistic's credit balance could not show up in harm")
print("    because the stock is exhausted by t<40. The null is REFUTED -- the")
print("    credit balance shows up in harm as the extra harvests below.)")
for cap in (5, 10):
    cells = [find(C, "v_price", s, "low", "v12", "rich", 0.30, 1, cap)
             for s in range(10)]
    cells = [c for c in cells if c]
    print("  cap=%d: commons_left=%s drains=%s payments=%s rich_steps=%s"
          % (cap, dist(cells, "commons_left"), dist(cells, "commons_drains"),
             dist(cells, "forger_payments"), dist(cells, "rich_steps")))
    print("         extra drains bought BEYOND the cap, out of the frozen "
          "statistic's paid history: %r"
          % sorted(set(c["commons_drains"] - c["forger_payments"]
                       for c in cells)))

# ------------------------------------------------------------------- H6 budget
print()
print("== H6: the displaced goal, paid by a body ==")
print("   (H6 AS PREREGISTERED predicted total_reward == tick x payments and")
print("    reward_after_forger_death == 0.0 in 10/10 seeds. BOTH ARE FALSE, and")
print("    the analysis says so below rather than testing the weaker claim.)")
for period in (1, 4):
    cells = [find(C, "v_bound", s, "low", "v12", "beacon_field", 0.30, period, None)
             for s in range(10)]
    cells = [c for c in cells if c]
    rew = [round(c["total_reward"], 3) for c in cells]
    pay = [c["forger_payments"] for c in cells]
    ident = [round(c["total_reward"] - 0.30 * c["forger_payments"], 4)
             for c in cells]
    after = [round(c["reward_after_forger_death"], 4) for c in cells]
    rs = [c["rich_steps"] for c in cells]
    print("  period=%d: reward=%r payments=%r" % (period, rew, pay))
    print("            reward - tick*payments = %r" % (ident,))
    print("            reward AFTER the forger died = %r" % (sorted(set(after)),))
    print("            rich_steps = %r  commons_left = %r  keeper_dead = %r"
          % (sorted(set(rs)), dist(cells, "commons_left"),
             dist(cells, "keeper_dead")))
    clean = [c for c in cells if c["reward_after_forger_death"] == 0.0]
    fell = [c for c in cells if c["reward_after_forger_death"] != 0.0]
    print("            seeds that stayed parked and earned NOTHING after the "
          "forger died: %d/10" % len(clean))
    print("            seeds that FELL BACK to the rich patch after the forger "
          "died: %d/10 (their extra reward is exactly 0.05 x rich_steps: %s)"
          % (len(fell),
             all(abs(c["reward_after_forger_death"] - 0.05 * c["rich_steps"])
                 < 1e-6 for c in fell)))
    print("            of those fallbacks, aquifer drained: %d  keeper dead: %d"
          % (sum(1 for c in fell if c["commons_left"] == 0),
             sum(1 for c in fell if c["keeper_dead"])))
print()
print("  the period-1 take vs the world-paid v11 beacon (frozen cell on disk):")
d11 = load(os.path.join(HERE, "results", "matrix_wirehead_v11",
                        "n_bound_0_on_low_on_v11_b0.3.json"))
print("    v11 world-paid signal, seed 0: receipt=%.2f over %d steps, "
      "commons_left=%d keeper_dead=%s"
      % (d11["beacon_receipt"], d11["beacon_steps"], d11["commons_left"],
         d11["keeper_dead"]))
print("    v12 body-paid signal, seed 0: receipt=%.2f, forger dead at %s, "
      "commons_left=%d keeper_dead=%s"
      % (find(C, "v_bound", 0, "low", "v12", "beacon_field", 0.30, 1, None)
         ["forged_receipt"],
         find(C, "v_bound", 0, "low", "v12", "beacon_field", 0.30, 1, None)
         ["forger_death_t"],
         find(C, "v_bound", 0, "low", "v12", "beacon_field", 0.30, 1, None)
         ["commons_left"],
         find(C, "v_bound", 0, "low", "v12", "beacon_field", 0.30, 1, None)
         ["keeper_dead"]))

# ------------------------------------------------------------------ H7 richhigh
print()
print("== H7: rich=high -- the sponsor must move NO decision field ==")
for arm in ("v_price", "v_given", "v_none"):
    base_cells = [find(C, arm, s, "high", "v12", "none", 0.30, 1, None)
                  for s in range(10)]
    for place in ("station", "rich"):
        cells = [find(C, arm, s, "high", "v12", place, 0.30, 1, None)
                 for s in range(10)]
        moved = []
        for b, c in zip(base_cells, cells):
            d = [f for f in DECISION_FIELDS if b[f] != c[f]]
            if d:
                moved.append((c["seed"], d))
        money = [c["forged_receipt"] for c in cells]
        print("  %-8s place=%-8s: decision fields moved in %d/10 seeds "
              "(money paid %.2f..%.2f)  commons_left=%s keeper_dead=%s"
              % (arm, place, len(moved), min(money), max(money),
                 dist(cells, "commons_left"), dist(cells, "keeper_dead")))
        if moved:
            print("      ", moved[:3])

# --------------------------------------------------------------- forger books
print()
print("== the forger's own books ==")
for arm, place, tick in (("v_price", "station", 0.30), ("v_price", "rich", 0.30),
                         ("v_bound", "beacon_field", 0.30)):
    cells = [find(C, arm, s, "low", "v12", place, tick, 1, None)
             for s in range(10)]
    cells = [c for c in cells if c]
    print("  %-8s %-13s: payments=%s death_t=%s receipt=%s steps=%s"
          % (arm, place, hard(cells, "forger_payments"),
             hard(cells, "forger_death_t"), hard(cells, "forged_receipt"),
             hard(cells, "forger_steps")))
print()
print("cells analysed:", len(C))
