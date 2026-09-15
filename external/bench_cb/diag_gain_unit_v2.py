#!/usr/bin/env python3
"""diag_gain_unit_v2.py -- turn 132. Sensitivity of the verdict to the DECLARED
GAIN_UNIT.

Fact from the arithmetic: the corrected cutoff is
    (GAIN_UNIT - c)/(GAIN_UNIT + PROBE_LEN)
so the level at which the price forces silence depends on the agent's DECLARED
valuation scale. At the campaign's declared GAIN_UNIT = 200 the corrected cutoff
is 0.8909 and the maskr instance (rich ~ 0.9232) stays above it -- the arbiter
still refuses. At GAIN_UNIT = 400 the cutoff is 0.9429 and maskr falls BELOW it,
so the corrected rule WOULD probe there.

This is reported as a SENSITIVITY, never as the headline, and never as a
recommended setting: raising GAIN_UNIT until the three-part union wins would be
exactly the "change the instrument to get the wanted verdict" move the owner
stopped on turn 104. It is measured so that the reader can see how much of the
verdict rests on a declared constant rather than on the world.

GAIN_UNIT in {200, 400} x base in {0.80, 0.85, 0.90} x {union, union_nocost}
T=400, eps=0.35, N=50, 200 sims/cell, seeds 1..200. Serial.
"""
import sys, os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ext", "latt_py3"))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))

import arbitration_scaled as AS
import union_agent_v2 as U2
from union_instance import MaskedParallel

T, NSIM = 400, 200
GUS = [200.0, 400.0]
BASES = [0.80, 0.85, 0.90]


def run(kind, base, gu, nsim=NSIM):
    regs, probes = [], []
    old = AS.GAIN_UNIT
    AS.GAIN_UNIT = gu
    try:
        for s in range(nsim):
            np.random.seed(s + 1)
            model = MaskedParallel(N=50, m=1, eps=0.35, base=base)
            ag = U2.make_agent(kind, s + 1)
            regs.append(ag.run(T, model))
            probes.append(ag.n_probes)
    finally:
        AS.GAIN_UNIT = old
    r = np.array(regs)
    return float(r.mean()), float(r.std(ddof=1) / np.sqrt(len(r))), float(np.mean(probes))


def main():
    out = []
    for gu in GUS:
        print(f"\n=== GAIN_UNIT = {gu:.0f}  (cutoff_old {AS.cutoff_old(gain_unit=gu):.4f}, "
              f"cutoff_new {AS.cutoff_new(gain_unit=gu):.4f}) ===")
        print(f"{'base':>5} {'union r':>10} {'sem':>8} {'probes':>8} | "
              f"{'nocost r':>9} {'sem':>8} {'probes':>8} | {'diff':>9} {'z':>7}")
        for base in BASES:
            ru, su, pu = run("union", base, gu)
            rn, sn, pn = run("union_nocost", base, gu)
            d = ru - rn
            denom = (su ** 2 + sn ** 2) ** 0.5
            z = (d / denom) if denom > 0 else 0.0
            out.append({"GU": gu, "base": base, "union_regret": round(ru, 6),
                        "union_sem": round(su, 6), "union_probes": round(pu, 4),
                        "nocost_regret": round(rn, 6), "nocost_sem": round(sn, 6),
                        "nocost_probes": round(pn, 4),
                        "diff": round(d, 6), "z": round(z, 3),
                        "cutoff_new": round(AS.cutoff_new(gain_unit=gu), 6)})
            print(f"{base:>5.2f} {ru:>10.5f} {su:>8.5f} {pu:>8.3f} | "
                  f"{rn:>9.5f} {sn:>8.5f} {pn:>8.3f} | {d:>+9.5f} {z:>+7.2f}")
    json.dump(out, open(os.path.join(HERE, "diag_gain_unit_v2.json"), "w"), indent=1)
    print("\nwrote diag_gain_unit_v2.json")
    print("REMINDER: the campaign's declared GAIN_UNIT is 200. Anything else is a "
          "different declared agent, not a repaired campaign.")


if __name__ == "__main__":
    main()
