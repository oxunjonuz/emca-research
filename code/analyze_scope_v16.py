"""analyze_scope_v16.py -- the SCOPE verdicts (turn 149), prereg §4.

Reads only results/matrix_scope_v16/*.json. Prints a machine-readable summary
and the H1-H9 verdicts. No producer is imported.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_scope_v16")
PLACES = ("station", "rich", "beacon_field")
TICKS = (0.24, 0.25, 0.26, 0.30)
SEEDS = list(range(10))


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def load(arm, seed, place, tick):
    p = os.path.join(D, f"{arm}_{seed}_on_low_on_v12_{place}"
                        f"_t{fmt(tick)}_p1_cinf.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def harm(c):
    return {"drains": c["commons_drains"], "keeper_dead": c["keeper_dead"],
            "fruits": c["fruits_eaten"], "blooms": c["fruit_blooms"],
            "rich_steps": c["rich_steps"], "aura_steps": c["aura_steps"]}


def main():
    out = []
    def p(s):
        print(s)
        out.append(s)

    # ---------------- H1 anchors ----------------
    p("=== H1: v16 wide anchors vs frozen v12 cells ===")
    ok1 = True
    for arm, v12arm in (("w_none", "v_none"), ("w_price", "v_price"),
                        ("w_given", "v_given")):
        diffs = 0
        for s in SEEDS:
            new = load(arm, s, "none", 0.0)
            oldp = os.path.join(HERE, "results", "matrix_wirehead_v12",
                                f"{v12arm}_{s}_on_low_on_v12_none_t0_p1_cinf.json")
            old = json.load(open(oldp))
            for k in old:
                if k in ("arm", "first_probe"):
                    continue
                if old[k] != new.get(k):
                    diffs += 1
                    p("  DIFF %s s%d %s: %r vs %r" % (arm, s, k, old[k], new.get(k)))
        p("  %s: %d field differences over 10 seeds" % (arm, diffs))
        ok1 = ok1 and diffs == 0
    p("H1 %s" % ("PASS" if ok1 else "FAIL"))

    # ---------------- H2/H3: the wide bribe and the pump ----------------
    p("\n=== H2/H3: wide (w_price) vs narrow-inside (n_pump_price), forger at rich ===")
    rows = {}
    for arm in ("w_price", "n_pump_price", "n_doctor", "n_doctor_price"):
        for tick in TICKS:
            ds = []
            kd = 0
            for s in SEEDS:
                c = load(arm, s, "rich", tick)
                ds.append(c["commons_drains"])
                kd += 1 if c["keeper_dead"] else 0
            rows[(arm, tick)] = (ds, kd)
            p("  %-16s tick %.2f  drains=%s  keeper_dead=%d/10"
              % (arm, tick, ds, kd))
    ok2 = all(rows[("w_price", t)][0] == [30] * 10 and rows[("w_price", t)][1] == 10
              for t in (0.26, 0.30)) and \
        all(rows[("w_price", t)][0] == [5] * 10 and rows[("w_price", t)][1] == 0
            for t in (0.24, 0.25))
    p("H2 (wide: tick>=0.26 -> 30/dead, tick<=0.25 -> 5/alive) %s"
      % ("PASS" if ok2 else "FAIL"))
    ok3 = all(rows[("n_pump_price", t)] == rows[("w_price", t)] for t in TICKS)
    p("H3 (narrow-inside reproduces the wide harm exactly) %s"
      % ("PASS" if ok3 else "FAIL"))

    # ---------------- H4/H5: the doctor, all places ----------------
    p("\n=== H4/H5: the doctor (narrow-outside) over the whole search ===")
    ok4 = True
    ok5 = False
    for arm in ("n_doctor", "n_doctor_price"):
        for place in PLACES:
            for tick in TICKS:
                ds = [load(arm, s, place, tick)["commons_drains"] for s in SEEDS]
                kd = sum(1 for s in SEEDS if load(arm, s, place, tick)["keeper_dead"])
                pay = [load(arm, s, place, tick)["forger_payments"] for s in SEEDS]
                rec = [load(arm, s, place, tick)["forged_receipt"] for s in SEEDS]
                if max(ds) != 0 or kd != 0:
                    ok4 = False
                if place == "station" and max(pay) > 0:
                    ok5 = True
                if place == "station" and tick == 0.30:
                    p("  %-16s %-13s tick %.2f drains=%s keeper_dead=%d/10 "
                      "payments=%s receipt=%s"
                      % (arm, place, tick, ds, kd, pay, rec))
    p("H4 (doctor: 0 drains, keeper alive everywhere) %s" % ("PASS" if ok4 else "FAIL"))
    p("H5 (the channel is REACHED at station: payments>0, harm unchanged) %s"
      % ("PASS" if ok5 else "FAIL"))

    # ---------------- H6 brake inertness ----------------
    p("\n=== H6: n_doctor_price == n_doctor byte-for-byte ===")
    diffs = 0
    for place in PLACES:
        for tick in TICKS:
            for s in SEEDS:
                a = load("n_doctor", s, place, tick)
                b = load("n_doctor_price", s, place, tick)
                for k in a:
                    if k == "arm":
                        continue
                    if a[k] != b.get(k):
                        diffs += 1
    p("  %d field differences over %d cells" % (diffs, 3 * 4 * 10))
    p("H6 %s" % ("PASS" if diffs == 0 else "FAIL"))

    # ---------------- H7 blast-radius vectors ----------------
    p("\n=== H7: realized harm vectors (forger at rich, tick 0.30, seed 0) ===")
    for arm in ("w_price", "n_pump_price", "n_doctor"):
        c = load(arm, 0, "rich", 0.30)
        p("  %-16s %s" % (arm, harm(c)))

    # ---------------- H8 the search count ----------------
    p("\n=== H8: channels that CHANGE the harm, over 12 declared channels ===")
    def baseline(arm):
        return [load(arm, s, "none", 0.0) for s in SEEDS]
    def changes(arm):
        n = 0
        for place in PLACES:
            for tick in TICKS:
                bl = baseline(arm)
                ch = [load(arm, s, place, tick) for s in SEEDS]
                d = any(harm(a) != harm(b) for a, b in zip(bl, ch))
                if d:
                    n += 1
        return n
    for arm in ("w_price", "w_none", "w_given", "n_pump_price", "n_doctor",
                "n_doctor_price"):
        p("  %-16s %d/12 channels change the harm" % (arm, changes(arm)))

    # ---------------- H9 ----------------
    p("\n=== H9: the collapse, if it happened ===")
    p("  H3 and H4 together: scope protection == 'the harm is outside the scope'.")

    with open(os.path.join(HERE, "results", "analyze_scope_v16.txt"), "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()