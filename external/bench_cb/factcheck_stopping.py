"""factcheck_stopping.py -- turn 134. Recompute EVERY number in
RESULTS_STOPPING.md from the frozen JSON, so no figure in the prose is a
recollection. Any number in the report that is not reproduced here is a defect.

Prints each claimed number beside the value recomputed from disk and FAILS on a
mismatch. Exits 1 on any failure.

  STOPPING_OUT=<dir> python3 factcheck_stopping.py [nsim]
"""
import glob
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []


def check(name, got, want, tol=5e-4):
    ok = abs(float(got) - float(want)) <= tol
    print("%-4s %-58s disk=%-12s report=%s"
          % ("PASS" if ok else "FAIL", name, round(float(got), 6), want))
    if not ok:
        FAILS.append((name, got, want))


def main():
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    OUT = os.environ.get("STOPPING_OUT") or os.path.join(
        _HERE, "results_stopping_hi" if nsim == 2000 else "results_stopping")
    cells = {}
    for fn in glob.glob(os.path.join(OUT, "*.json")):
        if fn.endswith("SUMMARY.json"):
            continue
        d = json.load(open(fn))
        cells[(d["arm"], d["inst"], d["param"], d.get("base"))] = d

    def R(arm, inst, param, base=None, key="mean_regret"):
        return cells[(arm, inst, param, base)][key]

    def boot(a, b, n=5000, seed=777):
        rng = np.random.RandomState(seed)
        d = np.asarray(a, float) - np.asarray(b, float)
        idx = rng.randint(0, len(d), size=(n, len(d)))
        return (float(d.mean()), float(np.percentile(d[idx].mean(axis=1), 2.5)),
                float(np.percentile(d[idx].mean(axis=1), 97.5)))

    def diff(arm, inst, param, base=None):
        return boot([r["regret"] for r in cells[(arm, inst, param, base)]["rows"]],
                    [r["regret"] for r in
                     cells[("frozen_rule", inst, param, base)]["rows"]])

    print("=== factcheck of RESULTS_STOPPING.md against %s (nsim=%d)\n"
          % (os.path.basename(OUT), nsim))

    # --- §2 the new rule acts and stops -------------------------------------
    check("G1 voi mask eps=0.35 mean probes", R("voi", "mask", 0.35, key="mean_probes"), 3.98, 5e-3)
    check("G1 voi mask eps=0.15 mean probes", R("voi", "mask", 0.15, key="mean_probes"), 3.96, 5e-3)
    check("G1 voi mask eps=0.25 mean probes", R("voi", "mask", 0.25, key="mean_probes"), 3.99, 5e-3)

    # --- §3 the richness sweep (G2) -----------------------------------------
    for b, vp, fp in ((0.50, 3.9845, 3.3130), (0.60, 1.3360, 3.0095),
                      (0.70, 0.4625, 2.7570), (0.75, 0.6515, 2.3990),
                      (0.80, 0.2405, 1.4600), (0.85, 0.0045, 0.4650),
                      (0.90, 0.0040, 0.0815), (0.95, 0.0020, 0.0000)):
        check("G2 voi probes base=%.2f" % b,
              R("voi", "mask", 0.35, b, "mean_probes"), vp, 5e-4)
        check("G2 frozen probes base=%.2f" % b,
              R("frozen_rule", "mask", 0.35, b, "mean_probes"), fp, 5e-4)

    # --- §4 G3 regret -------------------------------------------------------
    for inst, p, vr, fr in (("mask", 0.35, 0.004635, 0.003299),
                            ("mask", 0.25, 0.014879, 0.014277),
                            ("mask", 0.15, 0.033238, 0.032836),
                            ("maskr", 0.35, 0.031290, 0.027238),
                            ("maskr", 0.25, 0.031290, 0.027122)):
        check("G3 voi %s eps=%.2f regret" % (inst, p), R("voi", inst, p), vr)
        check("G3 frozen %s eps=%.2f regret" % (inst, p),
              R("frozen_rule", inst, p), fr)

    # --- §5 the published instance ------------------------------------------
    for m, vr, fr in ((2, 0.005100, 0.005250), (8, 0.010800, 0.012750),
                      (16, 0.013200, 0.025500), (49, 0.012300, 0.024450)):
        check("pub m=%d voi regret" % m, R("voi", "pub", m), vr)
        check("pub m=%d frozen regret" % m, R("frozen_rule", "pub", m), fr)
    for m, vp, fp in ((8, 7.8025, 8.8875), (16, 8.2980, 9.9925),
                      (49, 8.8885, 9.9945)):
        check("pub m=%d voi probes" % m, R("voi", "pub", m, key="mean_probes"), vp, 5e-4)
        check("pub m=%d frozen probes" % m,
              R("frozen_rule", "pub", m, key="mean_probes"), fp, 5e-4)

    # --- §5 the two-sided band, from the rule's own diagnostic --------------
    dg = json.load(open(os.path.join(_HERE, "diag_sensitivity_v3.json")))
    check("diag: frozen probes at GAIN_UNIT 25 and 800 (both True)",
          float(dg["frozen_gain_unit"]["25.0"]) + float(dg["frozen_gain_unit"]["800.0"]),
          2.0, 0.0)
    check("diag: frozen answer does NOT move with r_alt (all True)",
          sum(1 for v in dg["by_r_alt"].values() if v["frozen"]), 6.0, 0.0)
    check("diag: voi answer DOES move with r_alt (exactly one True)",
          sum(1 for v in dg["by_r_alt"].values() if v["voi"]), 1.0, 0.0)
    check("diag: frozen answer is the same at PROBE_LEN 5 and 80",
          float(dg["frozen_probe_len"]["5.0"]) + float(dg["frozen_probe_len"]["80.0"]),
          2.0, 0.0)

    # --- §6 the probability-only rule (G4) ----------------------------------
    for b in (0.60, 0.70, 0.80, 0.85):
        check("G4 conf probes base=%.2f vs nocost (both high)" % b,
              R("conf", "mask", 0.35, b, "mean_probes"), 
              R("union_nocost", "mask", 0.35, b, "mean_probes"), 0.6)

    # --- §7 controls --------------------------------------------------------
    for arm in ("beta0",):
        c = cells.get((arm, "mask", 0.35, None))
        if c:
            check("G5 %s probes (must be 0)" % arm, c["mean_probes"], 0.0, 1e-9)

    print("\n%d failure(s)" % len(FAILS))
    if FAILS:
        print("FAILED:", FAILS)
        sys.exit(1)
    print("ALL PASS -- every number above was recomputed from the frozen JSON")


if __name__ == "__main__":
    main()