"""union_matrix_v4_hi.py -- turn 135. The HEADLINE cells at nsim = 2000.

The full matrix runs at 200 sims (matching turn 134's full-grid resolution). This
file re-shoots the DECISIVE cells at 2000 sims so the CI on the bayes-vs-voi
difference is tight enough to say whether the lookahead rule buys anything:

  mask   eps 0.35   bayes, voi, frozen_rule, conf, union_nocost
  maskr  eps 0.35   same
  richness base 0.70 and 0.80 (where T2/T4 are in their band)
  pub    m 16       bayes, voi

Writes into results_bayes_hi/ (a SEPARATE directory; the 200-sim matrix is not
touched).

  python3 union_matrix_v4_hi.py [nsim]
"""
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)

OUT = os.environ.get("BAYES_HI_OUT") or os.path.join(_HERE, "results_bayes_hi")

JOBS = [
    ("bayes", "mask", 0.35, None), ("voi", "mask", 0.35, None),
    ("frozen_rule", "mask", 0.35, None), ("conf", "mask", 0.35, None),
    ("union_nocost", "mask", 0.35, None),
    ("bayes", "maskr", 0.35, None), ("voi", "maskr", 0.35, None),
    ("frozen_rule", "maskr", 0.35, None), ("conf", "maskr", 0.35, None),
    ("bayes", "mask", 0.35, 0.70), ("voi", "mask", 0.35, 0.70),
    ("conf", "mask", 0.35, 0.70),
    ("bayes", "mask", 0.35, 0.80), ("voi", "mask", 0.35, 0.80),
    ("conf", "mask", 0.35, 0.80),
    ("bayes", "mask", 0.35, 0.60), ("voi", "mask", 0.35, 0.60),
    ("bayes", "mask", 0.35, 0.85), ("voi", "mask", 0.35, 0.85),
    ("bayes", "pub", 16, None), ("voi", "pub", 16, None),
    ("bayes", "pub", 49, None), ("voi", "pub", 49, None),
]


def fname(inst, param, arm, base):
    tag = "" if base is None else "_b%s" % str(base).replace(".", "p")
    return os.path.join(OUT, "%s%s_p%s_%s.json"
                        % (inst, tag, str(param).replace(".", "p"), arm))


def main():
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    from union_matrix_v4 import cell
    t0 = time.time()
    for i, (arm, inst, param, base) in enumerate(JOBS):
        fn = fname(inst, param, arm, base)
        if os.path.exists(fn):
            print("  skip %s" % os.path.basename(fn), flush=True)
            continue
        res = cell(arm, inst, param, nsim, base=base)
        with open(fn, "w") as f:
            json.dump(res, f, indent=1)
        print("  [%d/%d] %-12s %-6s p=%-5s base=%-5s regret=%.5f probes=%5.2f "
              "%.0fs" % (i + 1, len(JOBS), arm, inst, param, base,
                         res["mean_regret"], res["mean_probes"],
                         time.time() - t0), flush=True)
    print("done in %.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main()