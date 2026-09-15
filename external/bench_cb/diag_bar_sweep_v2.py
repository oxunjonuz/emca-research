#!/usr/bin/env python3
"""diag_bar_sweep_v2.py -- turn 132. THE DECISIVE DIAGNOSTIC.

The repair (arbitration_scaled) moved the level at which the arbiter is forced
silent from rich = (GU-c)/(GU+H) = 0.8167 to rich = (GU-c)/(GU+PROBE_LEN) =
0.8909. The measured maskr instance sits at rich ~ 0.9232 -- still ABOVE the
corrected cutoff. So the question "was the scale the whole story?" must be
answered by measurement, not by argument.

Design -- sweep the PRICE HORIZON itself, on the same instance, same seeds:
    rhs = rich_rate * PL + PROBE_COST          PL in {0, 5, 10, 15, 20, 30, 40, 60}
PL = 20 is the corrected rule; PL = 40 is the frozen rule.
PL = 0 bills only the declared probe cost -- the price term is gone.
`union_nocost` (probe the top candidate, no price at all) is run alongside as
the two-part reference.

READINGS THIS GIVES:
  * if some interior PL beats BOTH the frozen rule and the no-price arm, the
    scale was the whole story and the repair direction is confirmed (but the
    constant then needs the horizon argument, and the report must say so);
  * if regret falls monotonically as PL falls to 0, then on THIS instance the
    price never earns its place and the honest verdict is that the three-part
    union still does not beat the two-part -- the repair only removes an
    artefact, it does not buy a win.

GAIN_UNIT sensitivity is subsumed: the bar on a candidate's score is rhs/GU, so a
different GU is a rescaling of the same sweep. Stated in the report.

Instances: maskr (base .8) and mask (base .5) so the whole regime is visible.
T=400, eps=0.35, N=50, 200 sims/cell, seeds 1..200. Serial (no Pool -- see
union_matrix_v2.py for the reason).
"""
import sys, os, json, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "ext", "latt_py3"))
sys.path.insert(0, HERE); sys.path.insert(0, CAMPAIGN)

import arbitration_scaled as AS
import union_agent_v2 as U2
from union_instance import MaskedParallel

T = 400
NSIM = 200
PLS = [0.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0]
INSTS = [("maskr", 0.8), ("mask", 0.5)]


def run(kind, base, pl, nsim=NSIM):
    regs, probes = [], []
    old_pl = AS.PROBE_LEN
    AS.PROBE_LEN = pl
    try:
        for s in range(nsim):
            np.random.seed(s + 1)
            model = MaskedParallel(N=50, m=1, eps=0.35, base=base)
            ag = U2.make_agent(kind, s + 1)
            regs.append(ag.run(T, model))
            probes.append(ag.n_probes)
    finally:
        AS.PROBE_LEN = old_pl
    r = np.array(regs)
    return float(r.mean()), float(r.std(ddof=1) / np.sqrt(len(r))), float(np.mean(probes))


def main():
    out = {}
    for inst, base in INSTS:
        print(f"\n=== {inst} (base {base}) : price horizon sweep ===")
        print(f"{'PL':>5} {'rhs@rich.92':>11} {'regret':>10} {'sem':>8} {'probes':>8}")
        rows = []
        for pl in PLS:
            r, se, p = run("union", base, pl)
            rows.append({"PL": pl, "regret": round(r, 6), "sem": round(se, 6),
                         "probes": round(p, 4),
                         "rhs_at_rich_092": round(0.9232 * pl + AS.PROBE_COST_DEFAULT, 4)})
            print(f"{pl:>5.0f} {0.9232*pl+AS.PROBE_COST_DEFAULT:>11.2f} {r:>10.5f} {se:>8.5f} {p:>8.3f}")
        r, se, p = run("union_nocost", base, 20.0)
        rows.append({"PL": "nocost", "regret": round(r, 6), "sem": round(se, 6),
                     "probes": round(p, 4)})
        print(f"{'nocost':>5} {'--':>11} {r:>10.5f} {se:>8.5f} {p:>8.3f}")
        out[inst] = rows
    json.dump(out, open(os.path.join(HERE, "diag_bar_sweep_v2.json"), "w"), indent=1)
    print("\nwrote diag_bar_sweep_v2.json")
    print("NOTE: PL=20 is the corrected rule; PL=40 reproduces the frozen rule.")


if __name__ == "__main__":
    main()
