#!/usr/bin/env python3
"""diag_cost_baseline_sweep.py -- turn 131.

THE CAUSE, stated as a testable law and then tested.

Observation from diag_cost_decompose.py:
    mask  (base .5): union probes 3.34/run,  regret .00544
    maskr (base .8): union probes 0.04/run,  regret .03128
    maskr NO-CLIP  : union probes 0.04/run  -- so NOT clipping (control refuted it)

Traced source-by-source (60 runs each):
    mask : exploration candidate top score 0.5094,  rich_rate 0.64  -> value 101.9 > rhs 29.7  -> CLEARS
    maskr: exploration candidate top score 0.1837,  rich_rate 0.92  -> value  36.7 < rhs 40.9  -> FAILS

THE LAW this suggests. The frozen arbiter compares
    value = beta · GAIN_UNIT · gap          (gap <= 1 - best_rate_in_ctx)
    rhs   = rich_rate · H + PROBE_COST
Both sides move with the world's reward range, but NOT proportionally: `rhs` is
AFFINE in rich_rate, while the achievable `gap` is bounded ABOVE by 1 - rich.
So the rule clears a candidate only while

    GAIN_UNIT · (1 - rich) > rich · H + c        i.e.    GAIN_UNIT > rich·(H + GAIN_UNIT) + c

which has a hard cutoff in `rich`. Above that cutoff the arbiter stops probing
ENTIRELY — not because the information became less valuable, but because the
scale of the value term and the scale of the price term drift apart.

TEST: sweep base across the transition on the SAME instance, same eps, and
record probes for union / union_nocost / beta0. The law predicts
  (i) union's probe count falls monotonically to 0;
  (ii) union_nocost's does NOT (no price term);
  (iii) the cutoff is at rich such that the top achievable score stops clearing.
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ext", "latt_py3"))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from union_instance import MaskedParallel
import union_agent as UA
import arbitration as AR

T, NSIM = 400, 200
BASES = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]


def sweep(kind, model):
    regs, probes, clears = [], [], []
    real = AR.plan
    for s in range(NSIM):
        np.random.seed(s + 1)
        ag = UA.make_agent(kind, s + 1)
        calls = []
        def spy(cands, rich, beta=1.0, **kw):
            p = real(cands, rich, beta=beta, **kw)
            calls.append((rich, p.rhs, max(p.values) if p.values else 0.0,
                          len(p.probe_order)))
            return p
        AR.plan = spy
        try:
            regs.append(ag.run(T, model))
        finally:
            AR.plan = real
        probes.append(ag.n_probes)
        if calls:
            clears.append(float(np.mean([1 if c[3] > 0 else 0 for c in calls])))
    return (float(np.mean(regs)), float(np.mean(probes)),
            float(np.mean(clears)) if clears else None)


def main():
    rows = []
    print(f"{'base':>5} {'rich':>6} {'1-rich':>7} | {'union r':>9} {'probes':>7} {'clear%':>7} "
          f"| {'nocost r':>9} {'probes':>7} | {'beta0 probes':>12}")
    for base in BASES:
        m = MaskedParallel(N=50, m=1, eps=0.35, base=base)
        ru, pu, cu = sweep("union", m)
        rn, pn, _ = sweep("union_nocost", m)
        rb, pb, _ = sweep("beta0", m)
        row = {"base": base, "rich_rate": None, "union_regret": round(ru, 6),
               "union_probes": round(pu, 4), "union_clear_frac": cu,
               "nocost_regret": round(rn, 6), "nocost_probes": round(pn, 4),
               "beta0_probes": round(pb, 4)}
        rows.append(row)
        print(f"{base:>5.2f} {'':>6} {1-base:>7.2f} | {ru:>9.5f} {pu:>7.3f} "
              f"{(cu if cu is not None else -1):>7.3f} | {rn:>9.5f} {pn:>7.3f} | {pb:>12.3f}")
    json.dump(rows, open(os.path.join(HERE, "diag_cost_baseline_sweep.json"), "w"), indent=1)
    print("\nwrote diag_cost_baseline_sweep.json")
    # the law's cutoff, computed from the frozen constants
    print(f"\nfrozen: GAIN_UNIT={AR.GAIN_UNIT} H={AR.H_DEFAULT} PROBE_COST={AR.PROBE_COST_DEFAULT}")
    print("law: a candidate with gap g clears iff g > (rich*H + c)/GAIN_UNIT")
    for base in BASES:
        rich = base        # dense exploration: resolved arms already pay ~base
        print(f"  base={base:.2f}: bar on gap = {(rich*AR.H_DEFAULT+AR.PROBE_COST_DEFAULT)/AR.GAIN_UNIT:.4f}"
              f"  headroom 1-rich = {1-rich:.4f}"
              f"  -> {'headroom exceeds bar' if (1-rich) > (rich*AR.H_DEFAULT+AR.PROBE_COST_DEFAULT)/AR.GAIN_UNIT else 'headroom BELOW bar -> cannot clear'}")


if __name__ == "__main__":
    main()
