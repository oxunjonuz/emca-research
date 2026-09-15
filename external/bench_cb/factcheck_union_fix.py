#!/usr/bin/env python3
"""factcheck_union_fix.py -- turn 132.

Re-derive EVERY number that appears in RESULTS_UNION_FIX.md from the frozen JSON
on disk, and fail loudly on any disagreement. The numbers are not compared to a
copy of themselves: each one is recomputed from the raw per-seed rows or from the
module arithmetic.
"""
import sys, os, json, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ext", "latt_py3"))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))

import arbitration_scaled as AS

fails, n = 0, 0


def ck(name, got, want, tol=5e-6):
    global fails, n
    n += 1
    ok = (abs(got - want) <= tol) if isinstance(want, float) else (got == want)
    if not ok:
        fails += 1
        print(f"  FAIL {name}: got {got!r} want {want!r}")
    return ok


def main():
    S = json.load(open(os.path.join(HERE, "results_union_v2", "SUMMARY.json")))
    O = json.load(open(os.path.join(HERE, "results_union", "SUMMARY.json")))
    SW = json.load(open(os.path.join(HERE, "sweep_arbiter_v2.json")))
    TR = json.load(open(os.path.join(HERE, "trace_arbiter_summary.json")))
    HB = json.load(open(os.path.join(HERE, "diag_bar_sweep_v2.json")))
    GU = json.load(open(os.path.join(HERE, "diag_gain_unit_v2.json")))

    print("== cutoffs ==")
    ck("cutoff_old", AS.cutoff_old(), 0.816667, 1e-6)
    ck("cutoff_new", AS.cutoff_new(), 0.890909, 1e-6)
    ck("cutoff_old == 196/240", AS.cutoff_old(), 196.0 / 240.0, 1e-12)
    ck("cutoff_new == 196/220", AS.cutoff_new(), 196.0 / 220.0, 1e-12)

    print("== base sweep (old / new / nocost / beta0) ==")
    want = {
        0.50: (0.004855, 0.003105, 0.00289125, 3.365, 3.43, 0.0),
        0.55: (0.01196625, 0.00386125, 0.00289125, 3.18, 3.26, 0.0),
        0.60: (0.033915, 0.00756, 0.00225, 2.755, 2.99, 0.0),
        0.65: (0.046253, 0.02001, 0.003339, 2.405, 2.905, 0.0),
        0.70: (0.04932, 0.02888, 0.003821, 1.655, 2.795, 0.0),
        0.75: (0.051431, 0.02886, 0.010394, 0.44, 2.435, 0.0),
        0.80: (0.031, 0.02656, 0.021269, 0.01, 1.545, 0.0),
        0.85: (0.006, 0.006, 0.006875, 0.0, 0.465, 0.0),
        0.90: (0.00475, 0.00475, 0.00475, 0.0, 0.1, 0.0),
        0.95: (0.0035, 0.0035, 0.0035, 0.0, 0.0, 0.0),
    }
    for r in SW:
        b = r["base"]
        ck(f"sweep base {b} old", r["union_old_regret"], want[b][0])
        ck(f"sweep base {b} new", r["union_new_regret"], want[b][1])
        ck(f"sweep base {b} nocost", r["union_nocost_regret"], want[b][2])
        ck(f"sweep base {b} old probes", r["union_old_probes"], want[b][3], 1e-6)
        ck(f"sweep base {b} new probes", r["union_new_probes"], want[b][4], 1e-6)
        ck(f"sweep base {b} beta0 probes", r["beta0_new_probes"], want[b][5], 1e-9)

    print("== trace ==")
    ck("mask rich mean", TR["mask_base0.5"]["rich_mean"], 0.6482, 5e-5)
    ck("maskr rich mean", TR["maskr_base0.8"]["rich_mean"], 0.9232, 5e-5)
    ck("maskr frac cleared old", TR["maskr_base0.8"]["frac_cleared_old"], 0.0001, 5e-5)
    ck("maskr frac would clear new", TR["maskr_base0.8"]["frac_would_clear_new"],
       0.4162, 5e-5)
    ck("mask decisions in band", TR["mask_base0.5"]["n_in_band"], 0)
    ck("maskr decisions in band", TR["maskr_base0.8"]["n_in_band"], 503)

    print("== horizon sweep ==")
    hb = {round(r["PL"], 1): r for r in HB["maskr"] if isinstance(r["PL"], float)}
    ck("maskr PL=40 regret", hb[40.0]["regret"], 0.031)
    ck("maskr PL=20 regret", hb[20.0]["regret"], 0.02656)
    ck("maskr PL=0 regret", hb[0.0]["regret"], 0.02137)
    mono = all(hb[a]["regret"] <= hb[b]["regret"] + 1e-9
               for a, b in zip(sorted(hb), sorted(hb)[1:]))
    ck("maskr regret monotone nondecreasing in PL", mono, True)
    noc = [r for r in HB["maskr"] if r["PL"] == "nocost"][0]
    ck("maskr nocost regret", noc["regret"], 0.02127)
    ck("nocost is the best of the sweep (price never earns its place)",
       noc["regret"] <= hb[0.0]["regret"] + 1e-9, True)

    print("== full matrix: the owner's question ==")
    u = S["maskr|0.35|union"]; nc = S["maskr|0.35|union_nocost"]
    d = u["mean_regret"] - nc["mean_regret"]
    z = d / ((u["sem_regret"] ** 2 + nc["sem_regret"] ** 2) ** 0.5)
    ck("maskr union 0.02719", u["mean_regret"], 0.027188, 5e-6)
    ck("maskr nocost 0.02097", nc["mean_regret"], 0.020972, 5e-6)
    ck("maskr z ~ +8.1", z, 8.11, 0.05)
    ck("three-part LOSES to two-part on maskr", d > 0, True)
    u = S["mask|0.35|union"]; nc = S["mask|0.35|union_nocost"]
    d2 = u["mean_regret"] - nc["mean_regret"]
    z2 = d2 / ((u["sem_regret"] ** 2 + nc["sem_regret"] ** 2) ** 0.5)
    ck("mask union 0.00328", u["mean_regret"], 0.003279, 5e-6)
    ck("mask nocost 0.00341", nc["mean_regret"], 0.003413, 5e-6)
    checkpoint = "mask: three-part ties two-part (|z| < 2)"
    if abs(z2) < 2:
        ck(checkpoint, True, True)
    else:
        ck(checkpoint, abs(z2), "expected < 2")

    print("== improvement of the corrected rule over the frozen one ==")
    old_m = O["maskr|0.35|union"]["mean_regret"]
    new_m = S["maskr|0.35|union"]["mean_regret"]
    ck("maskr old 0.03125", old_m, 0.031252, 5e-6)
    ck("maskr new 0.02719", new_m, 0.027188, 5e-6)
    ck("maskr improvement 0.004064", old_m - new_m, 0.004064, 5e-6)

    print("== audit-page numbers ==")
    ck("maskr union probes 1.459", S["maskr|0.35|union"]["mean_probes"], 1.459, 5e-4)
    ck("mask union probes 3.312", S["mask|0.35|union"]["mean_probes"], 3.312, 5e-4)
    ck("mask nocost probes 4.266", S["mask|0.35|union_nocost"]["mean_probes"], 4.266, 5e-4)

    print("== GAIN_UNIT sensitivity ==")
    g = {(r["GU"], r["base"]): r for r in GU}
    ck("GU400 base .80 union", g[(400.0, 0.8)]["union_regret"], 0.022953, 5e-6)
    ck("GU400 base .80 nocost", g[(400.0, 0.8)]["nocost_regret"], 0.021269, 5e-6)
    ck("GU400 maskr_diff still POSITIVE (three-part still behind)", 
       g[(400.0, 0.8)]["diff"] > 0, True)
    ck("GU200 cutoff", AS.cutoff_new(gain_unit=200.0), 0.890909, 1e-6)
    ck("GU400 cutoff", AS.cutoff_new(gain_unit=400.0), 0.942857, 1e-6)

    print(f"\n{n - fails}/{n} numbers agree with the frozen data"
          + ("" if fails == 0 else f"  ({fails} FAILURES)"))


if __name__ == "__main__":
    main()
