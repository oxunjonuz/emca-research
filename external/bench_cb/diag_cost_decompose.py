#!/usr/bin/env python3
"""diag_cost_decompose.py -- turn 131.

WHY does the cost-aware arbiter fail in the RICH regime?

Frozen: maskr_p0p35 union 0.031252 (probes 0.018) vs union_nocost 0.020972
        (probes 4.396). One switch differs: the price.

TWO candidate causes, and this script separates them:
  (P) PRICE   -- rich_rate is higher in maskr (base 0.8 vs 0.5), so
                 rhs = rich*H + PROBE_COST rises and fewer candidates clear.
  (S) SCORE   -- the instance CLIPS pY to [0,1]. In maskr the true cause's raw
                 pY in ctx0 is 0.8+0.35 = 1.15 -> 1.0, while the decoy is
                 0.8+0.15 = 0.95: the observable in-context contrast is 0.05,
                 not 0.20. A saturated ceiling COMPRESSES the signal, so the
                 candidate scores the arbiter is asked to price are smaller.

Design: a no-clip control. Same instance, same base=0.8 (same rich_rate, same
price), but pY is allowed above 1 so the contrast is not compressed. If the
arbiter starts probing in the no-clip control, the cause is (S) score
compression, not (P) the price.
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ext", "latt_py3"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from numpy.random import binomial
from union_instance import MaskedParallel
import union_agent as UA

T, NSIM = 400, 300


class NoClip(MaskedParallel):
    """Identical to MaskedParallel except pYgivenX is NOT clipped to [0,1].
    A measurement control only -- never an agent-facing instance."""
    def pYgivenX(self, x, z):
        v = self.base
        if x[0] == 1:
            v += self.eps if z == 0 else -self.eps
        if x[1] == 1:
            v += self.decoy if z == 0 else -self.decoy * self.decoy_rev
        return v                      # no clip

    def sample(self, action):
        z = int(binomial(1, self.pZ))
        x = binomial(1, self._pX_given_c(z))
        if action != self.K - 1:
            i, j = action % self.N, action // self.N
            x[i] = j
        p = min(max(self.pYgivenX(list(x), z), 0.0), 1.0)   # sampling stillBernoulli-legal
        y = binomial(1, p)
        return x, y, z


def sweep(kind, model):
    regs, probes = [], []
    for s in range(NSIM):
        np.random.seed(s + 1)
        ag = UA.make_agent(kind, s + 1)
        regs.append(ag.run(T, model))
        probes.append(ag.n_probes)
    return float(np.mean(regs)), float(np.mean(probes))


def main():
    out = {}
    for label, cls, base in [("mask (base .5)", MaskedParallel, 0.5),
                             ("maskr (base .8)", MaskedParallel, 0.8),
                             ("maskr NO-CLIP (base .8)", NoClip, 0.8)]:
        m = cls(N=50, m=1, eps=0.35, base=base)
        # the observable in-context contrast the generator can see
        er = m.er_ctx[0]
        gap_obs = float(er.max() - np.sort(er)[-2])
        gap_true = float(m.pYgivenX([1, 0] + [0]*48, 0) - m.pYgivenX([0, 1] + [0]*48, 0))
        row = {"base": base, "gap_observable_ctx0": round(gap_obs, 4),
               "gap_true_unclipped": round(gap_true, 4)}
        for kind in ("union", "union_nocost"):
            r, p = sweep(kind, m)
            row[kind + "_regret"] = round(r, 6)
            row[kind + "_probes"] = round(p, 4)
        out[label] = row
        print(f"{label}:  gap_obs={gap_obs:.4f}  gap_true={gap_true:.4f}"
              f"  union r={row['union_regret']:.5f} probes={row['union_probes']:.3f}"
              f"  |  nocost r={row['union_nocost_regret']:.5f} probes={row['union_nocost_probes']:.3f}")
    json.dump(out, open(os.path.join(HERE, "diag_cost_decomposition.json"), "w"), indent=1)
    print("\nwrote diag_cost_decomposition.json")


if __name__ == "__main__":
    main()
