"""factcheck_v8_report.py -- verify the numbers PRINTED IN RESULTS_V8.md
against the frozen matrix on disk, independently of analyze_v8.py.

Every assertion is a claim the report makes. A failure here means the
report is wrong, not the data. Prints PASS/FAIL and exits 1 on any FAIL.
"""
import glob
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_v8")
fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        fails.append(name)


def L(t):
    try:
        with open(os.path.join(D, t + ".json")) as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None


def mean_reward(arm, gap, q=0.0, n=8, persist=False, truth=True):
    v = [L(f"{arm}_s{s}_g{gap}_q{q}_{'p' if persist else 'n'}_"
           f"{'on' if truth else 'off'}") for s in range(n)]
    v = [x for x in v if x]
    return statistics.mean(x["total_reward"] for x in v), v


def mean_gather(arm, gap, q=0.0, n=8, persist=False, truth=True):
    v = [L(f"{arm}_s{s}_g{gap}_q{q}_{'p' if persist else 'n'}_"
           f"{'on' if truth else 'off'}") for s in range(n)]
    v = [x for x in v if x]
    return statistics.mean(x["steps_gathering"] for x in v)


def paired(armA, armB, gap, q=0.0, n=8, persistA=False, persistB=False,
           truth=True):
    d = []
    for s in range(n):
        a = L(f"{armA}_s{s}_g{gap}_q{q}_{'p' if persistA else 'n'}_"
              f"{'on' if truth else 'off'}")
        b = L(f"{armB}_s{s}_g{gap}_q{q}_{'p' if persistB else 'n'}_"
              f"{'on' if truth else 'off'}")
        if a and b:
            d.append(a["total_reward"] - b["total_reward"])
    return statistics.mean(d), sum(1 for x in d if x > 0), len(d)


def main():
    print("=== REPORT FACT-CHECK (RESULTS_V8.md vs the frozen matrix) ===")
    print("\n C1/C2/C3 paired differences, as printed in the report")
    table = {"0.20": dict(C1=7288, C2=203350, C3=196062),
             "0.10": dict(C1=28150, C2=86275, C3=58125),
             "0.05": dict(C1=15488, C2=26312, C3=10825),
             "0.03": dict(C1=7550, C2=7738, C3=188)}
    for gap, row in table.items():
        c1, k1, n1 = paired("graded", "threshold", gap)
        c2, k2, _ = paired("graded", "coin", gap)
        c3, k3, _ = paired("threshold", "coin", gap)
        for lbl, got, want in (("C1", c1, row["C1"]), ("C2", c2, row["C2"]),
                               ("C3", c3, row["C3"])):
            check(f"  gap {gap} {lbl} = {want}", abs(got - want) < 1.0,
                  f"(measured {got:.0f})")
    print("\n C4 effort shares, as printed")
    for gap, g, t in (("0.20", 0.045, 0.083), ("0.10", 0.104, 0.409),
                      ("0.05", 0.249, 0.705), ("0.03", 0.268, 0.796)):
        gv = [L(f"graded_s{s}_g{gap}_q0.0_n_on") for s in range(8)]
        tv = [L(f"threshold_s{s}_g{gap}_q0.0_n_on") for s in range(8)]
        gs = statistics.mean(x["steps_gathering"] / x["steps"] for x in gv)
        ts = statistics.mean(x["steps_gathering"] / x["steps"] for x in tv)
        check(f"  gap {gap} graded share {g}", abs(gs - g) < 0.002,
              f"(measured {gs:.3f})")
        check(f"  gap {gap} threshold share {t}", abs(ts - t) < 0.002,
              f"(measured {ts:.3f})")
    print("\n C5 gamma ordering, as printed (means)")
    from agent_emca_v8 import two_prop_z, gamma_of
    for gap, gt_w, gf_w in (("0.20", 0.9967, 0.0000), ("0.10", 0.9868, 0.0002),
                            ("0.05", 0.8132, 0.0383), ("0.03", 0.5664, 0.1244)):
        gt, gf = [], []
        for s in range(8):
            r = L(f"graded_s{s}_g{gap}_q0.0_n_on")
            if not r:
                continue
            for k, row in enumerate(r["epoch_log"]):
                if k >= len(r["epoch_actions_true"]) or row.get("n", 0) == 0:
                    continue
                ta = r["epoch_actions_true"][k]
                c = row["counts"]
                h, n = c[ta]
                oh = sum(v[0] for a, v in c.items() if a != ta)
                on = sum(v[1] for a, v in c.items() if a != ta)
                if n and on:
                    gt.append(gamma_of(two_prop_z(h, n, oh, on)))
                for a in ("wait", "press", "grasp"):
                    if a == ta:
                        continue
                    ha, na = c[a]
                    oh2 = sum(v[0] for b, v in c.items() if b != a)
                    on2 = sum(v[1] for b, v in c.items() if b != a)
                    if na and on2:
                        gf.append(gamma_of(two_prop_z(ha, na, oh2, on2)))
        check(f"  gap {gap} gamma true {gt_w}", abs(statistics.mean(gt) - gt_w) < 0.0005,
              f"(measured {statistics.mean(gt):.4f})")
        check(f"  gap {gap} gamma false {gf_w}", abs(statistics.mean(gf) - gf_w) < 0.0005,
              f"(measured {statistics.mean(gf):.4f})")

    print("\n A1 persistence contrasts, as printed")
    def obs_gap(gap, arm, persist):
        vals = []
        for s in range(8):
            r = L(f"{arm}_s{s}_g{gap}_q0.0_{'p' if persist else 'n'}_on")
            if not r:
                continue
            for k, row in enumerate(r["epoch_log"]):
                if k >= len(r["epoch_actions_true"]) or row.get("n", 0) == 0:
                    continue
                ta = r["epoch_actions_true"][k]
                c = row["counts"]
                h, n = c[ta]
                oh = sum(v[0] for a, v in c.items() if a != ta)
                on = sum(v[1] for a, v in c.items() if a != ta)
                if n and on:
                    vals.append(h / n - oh / on)
        return statistics.mean(vals)
    for gap, arm, persist, want in (("0.20", "graded", False, 0.2130),
                                    ("0.20", "graded", True, 0.3273),
                                    ("0.20", "rot", True, 0.1967),
                                    ("0.10", "graded", True, 0.1868),
                                    ("0.10", "rot", True, 0.0994)):
        got = obs_gap(gap, arm, persist)
        check(f"  gap {gap} {arm} persist={'on' if persist else 'off'} "
              f"= {want}", abs(got - want) < 0.0005, f"(measured {got:.4f})")

    print("\n A2 contrasts, as printed")
    a, k, n = paired("graded", "graded", "0.20", persistA=True)
    check("  graded(on)-graded(off) gap 0.20 = +199663",
          abs(a - 199663) < 1.0, f"(measured {a:+.0f})")
    a, k, n = paired("graded", "graded", "0.10", persistA=True)
    check("  graded(on)-graded(off) gap 0.10 = +152775",
          abs(a - 152775) < 1.0, f"(measured {a:+.0f})")
    # the exact identity the report states
    x, _, _ = paired("graded", "graded", "0.20", persistA=True)
    y, _, _ = paired("graded", "rot", "0.20", persistA=True, persistB=True)
    z, _, _ = paired("graded", "rot", "0.20")
    check("  identity: (graded-rot|pon) - (graded-rot|poff) == "
          "graded(pon)-graded(poff) exactly", abs((y - z) - x) < 1e-6,
          f"({y:.0f} - {z:.0f} = {y-z:.0f} vs {x:.0f})")
    a, k, n = paired("graded", "rot", "0.20", persistA=True, persistB=True)
    check("  graded(pon)-rot(pon) gap 0.20 = +403588",
          abs(a - 403588) < 1.0, f"(measured {a:+.0f})")
    a, k, n = paired("graded", "rot", "0.20")
    check("  graded(poff)-rot(poff) gap 0.20 = +203925",
          abs(a - 203925) < 1.0, f"(measured {a:+.0f})")
    a, k, n = paired("graded", "rot", "0.10", persistA=True, persistB=True)
    check("  graded(pon)-rot(pon) gap 0.10 = +243538",
          abs(a - 243538) < 1.0, f"(measured {a:+.0f})")
    a, k, n = paired("graded", "rot", "0.10")
    check("  graded(poff)-rot(poff) gap 0.10 = +90762",
          abs(a - 90762) < 1.0, f"(measured {a:+.0f})")

    print("\n F curve, as printed")
    for q, want in ((0.0, -48162), (0.25, -36688), (0.5, -25762),
                    (0.75, -10125), (1.0, 11838)):
        a, k, n = paired("f_carry", "f_fresh", "0.10", q=q)
        check(f"  q={q} carry-fresh = {want}", abs(a - want) < 1.0,
              f"(measured {a:+.0f}, {k}/{n} positive)")
    print("\n F2 / F3, as printed")
    for q, want in ((1.0, 0.449), (0.75, 0.896), (0.0, 2.064)):
        cg = mean_gather("f_carry", "0.10", q=q)
        fg = mean_gather("f_fresh", "0.10", q=q)
        check(f"  q={q} carry/fresh gathering = {want}",
              abs(cg / fg - want) < 0.005, f"(measured {cg/fg:.3f})")
    a, k, n = paired("f_carry", "oracle", "0.10", q=1.0)
    carry, _ = mean_reward("f_carry", "0.10", q=1.0)
    orac, _ = mean_reward("oracle", "0.10", q=1.0)
    check("  q=1 carry reaches 99.2% of oracle",
          abs(100 * carry / orac - 99.2) < 0.1,
          f"(measured {100*carry/orac:.1f}%, carry {carry:.0f}, "
          f"oracle {orac:.0f})")

    print("\n C6 tau dose, as printed")
    for arm, want in (("graded", 704275), ("graded_t07", 677750),
                      ("graded_t03", 642125), ("rot", 613512)):
        m, _ = mean_reward(arm, "0.10")
        check(f"  {arm} reward = {want}", abs(m - want) < 1.0,
              f"(measured {m:.0f})")

    print("\n code-freeze claim: no code file is newer than any matrix file")
    code = ["env_terrarium_v8.py", "agent_emca_v8.py", "run_life_v8.py",
            "driver_v8.py"]
    newest_code = max(os.path.getmtime(os.path.join(HERE, f)) for f in code)
    oldest_mat = min(os.path.getmtime(f)
                     for f in glob.glob(os.path.join(D, "*.json")))
    check("  all 404 matrix files were written after the last code edit",
          newest_code < oldest_mat)

    print()
    if fails:
        print(f"FACT-CHECK: FAIL ({len(fails)})", fails)
        raise SystemExit(1)
    print("FACT-CHECK: ALL PASS")


if __name__ == "__main__":
    main()
