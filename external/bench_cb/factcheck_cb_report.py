"""factcheck_cb_report.py -- turn 128: re-derive every number in RESULTS_CB.md
from the frozen JSON on disk. Any number in the report that does not match the
files is a failure of the report, not of the files.

Run: python3 factcheck_cb_report.py
"""
import os, json, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def L(p):
    with open(os.path.join(HERE, p)) as f:
        return json.load(f)


def cell(arm, m):
    return L("results_cb/%s_m%d.json" % (arm, m))["mean_regret"]


def fam(arm, q1):
    return L("results_cb_family/%s_q%s.json" % (arm, q1))["mean_regret"]


def iso(what, key):
    return L("results_cb_iso/%s.json" % what)["cells"][key]["mean_regret"]


FAILS = []


def eq(name, got, want, tol=5e-5):
    ok = abs(got - want) <= tol
    if not ok:
        FAILS.append((name, got, want))
    print("[%s] %-58s got %.4f want %.4f" % ("OK " if ok else "FAIL", name, got, want))


def main():
    # ---- section 2: published shape table -----------------------------
    want = {("alg1_pub", 2): 0.0000, ("alg1_pub", 8): 0.0189, ("alg1_pub", 16): 0.1056,
            ("alg1_pub", 25): 0.1755, ("alg1_pub", 40): 0.2394, ("alg1_pub", 49): 0.2574,
            ("alg2_pub", 2): 0.0162, ("alg2_pub", 8): 0.1005, ("alg2_pub", 16): 0.1686,
            ("alg2_pub", 25): 0.2106, ("alg2_pub", 40): 0.2400, ("alg2_pub", 49): 0.2496,
            ("sr_pub", 2): 0.1638, ("sr_pub", 49): 0.1638,
            ("ucb_pub", 2): 0.2361, ("ucb_pub", 49): 0.2361}
    for (a, m), v in want.items():
        eq("shape %s m=%d" % (a, m), cell(a, m), v)

    # ---- section 3: mechanism vs published ----------------------------
    for m in [2, 8, 16, 25, 40, 49]:
        eq("pure m=%d == 0.3000" % m, cell("pure", m), 0.3000)
        eq("beta0 m=%d == 0.3000" % m, cell("beta0", m), 0.3000)
        eq("perm m=%d == 0.3000" % m, cell("perm", m), 0.3000)
    for m, v in [(2, 0.0000), (8, 0.0066), (16, 0.0537), (25, 0.0936),
                 (40, 0.1587), (49, 0.1728)]:
        eq("unc m=%d" % m, cell("unc", m), v)
    for m, v in [(2, 0.1029), (8, 0.1035), (16, 0.1035), (25, 0.1035),
                 (40, 0.1035), (49, 0.1035)]:
        eq("boot5 m=%d" % m, cell("boot5", m), v)

    # ---- section 4: generator silence ---------------------------------
    want_sil = {2: 0.9993, 8: 0.9993, 16: 0.9993, 25: 0.9994, 40: 0.9997, 49: 0.9999}
    for m, v in want_sil.items():
        d = L("results_cb/pure_m%d.json" % m)
        tg = sum(r["n_gen_calls"] for r in d["rows"])
        te = sum(r["n_empty_gen"] for r in d["rows"])
        eq("silence m=%d" % m, te / float(tg), v, tol=5e-5)
        eq("opt_trials m=%d == 0" % m, max(r["opt_trials"] for r in d["rows"]), 0.0)
        eq("frac_optimal m=%d == 0" % m, d["frac_optimal"], 0.0)

    # ---- section 5: C1 isolation --------------------------------------
    for m in [2, 8, 25, 49]:
        eq("iso none m=%d" % m, iso("isolate_pub", "none_m%d" % m), 0.3000)
        eq("iso inject_true m=%d" % m, iso("isolate_pub", "inject_true_m%d" % m), 0.0000)
        eq("iso inject_forced m=%d" % m, iso("isolate_pub", "inject_forced_m%d" % m), 0.0000)
    eq("iso grey none", iso("isolate_grey", "none"), 0.2270)
    eq("iso grey inject_true", iso("isolate_grey", "inject_true"), 0.0007)

    # ---- section 6(a): controls ---------------------------------------
    for m in [2, 8, 25, 49]:
        eq("greedy_half m=%d" % m, iso("controls_pub", "greedy_half_m%d" % m), 0.3000)
        eq("obs_only m=%d" % m, iso("controls_pub", "obs_only_m%d" % m), 0.3000)
        eq("know_probe m=%d" % m, iso("controls_pub", "know_probe_m%d" % m), 0.0000)
    for m, v in [(2, 0.1070), (8, 0.1070), (25, 0.1080), (49, 0.1080)]:
        eq("rnd_probe m=%d" % m, iso("controls_pub", "rnd_probe_m%d" % m), v)

    # ---- section 6(b): family -----------------------------------------
    famwant = {0.0: 0.3000, 0.02: 0.0702, 0.05: 0.0222, 0.1: 0.0033,
               0.2: 0.0000, 0.35: 0.0000, 0.5: 0.0000}
    for q1, v in famwant.items():
        eq("family pure q=%s" % q1, fam("pure", q1), v)
        eq("family beta0 q=%s" % q1, fam("beta0", q1), v)
        eq("family ucb q=%s" % q1, fam("ucb", q1), 0.0000)
        eq("family alg1 q=%s" % q1, fam("alg1_pub", q1), 0.0000)
    for q1, v in [(0.0, 0.1638), (0.5, 0.1593)]:
        eq("family sr q=%s" % q1, fam("sr_pub", q1), v)

    # ---- section 6(c): beta sweep -------------------------------------
    for b in [0.0, 1.0, 5.0, 10.0, 20.0, 50.0]:
        eq("beta sweep beta=%s" % b, iso("beta_sweep", "beta_%s" % b), 0.2270)

    # ---- section 6(c): horizon sweep ----------------------------------
    for T in [400, 1000, 2000, 4000, 8000]:
        eq("horizon T=%d" % T, iso("horizon_grey", "T_%d" % T), 0.2250)

    # ---- section 7: H3 claim beta0 == pure everywhere ------------------
    for m in [2, 8, 16, 25, 40, 49]:
        eq("H3 beta0==pure m=%d" % m, cell("beta0", m), cell("pure", m))
        eq("H3 perm==pure m=%d" % m, cell("perm", m), cell("pure", m))

    # ---- section 8: determinism shas ----------------------------------
    out = open(os.path.join(HERE, "verify_cb_out.txt")).read()
    for sha in ["64118da4a52b", "a454f5e5fcae"]:
        ok = sha in out
        if not ok:
            FAILS.append(("determinism sha " + sha, None, None))
        print("[%s] determinism sha %s present in verifier output" %
              ("OK " if ok else "FAIL", sha))
    ok = "ALL AGREE" in out
    if not ok:
        FAILS.append(("verifier ALL AGREE", None, None))
    print("[%s] verifier reported ALL AGREE" % ("OK " if ok else "FAIL"))

    # ---- constants quoted in the report --------------------------------
    meta = L("results_cb_meta.json")
    c = meta["frozen_constants"]
    eq("constant MIN_N", c["MIN_N"], 40, tol=0)
    eq("constant Z_MIN", c["Z_MIN"], 4.0, tol=0)
    eq("constant GAIN_UNIT", c["GAIN_UNIT"], 200.0, tol=0)
    eq("constant H_DEFAULT", c["H_DEFAULT"], 40.0, tol=0)
    eq("constant PROBE_COST", c["PROBE_COST_DEFAULT"], 4.0, tol=0)
    eq("arbiter rhs at rich 0.6", 0.6 * c["H_DEFAULT"] + c["PROBE_COST_DEFAULT"], 28.0)
    eq("arbiter value at score 0.5", c["GAIN_UNIT"] * 0.5, 100.0)
    eq("arbiter value at weak score 0.0888", c["GAIN_UNIT"] * 0.0888, 17.76, tol=5e-3)

    print()
    if FAILS:
        print("RESULT: %d FAILURES" % len(FAILS))
        for f in FAILS:
            print("   ", f)
        sys.exit(1)
    print("RESULT: ALL NUMBERS IN RESULTS_CB.md MATCH THE FROZEN FILES")


if __name__ == "__main__":
    main()
