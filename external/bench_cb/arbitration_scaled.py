"""arbitration_scaled.py -- turn 132. The CORRECTED price for the union line.

WHY THIS FILE EXISTS, AND WHY `arbitration.py` IS LEFT BYTE-FROZEN
-----------------------------------------------------------------
`arbitration.py` (sha 2d3d825bcfc83cc8533866510960572c42140db2f2f03c6a9945807b71e0914c)
is the campaign's frozen C1 rule; every frozen V7/V8 artefact was produced under
it and it is hashed in `results_union_meta.json`. It is NOT edited here. This
module supplies the corrected rule for the union line only, so that the old
matrix and the new one can be told apart by their producer and not by memory.

THE ENGINEERING ERROR (measured turn 131, accepted by the owner msg_00132)
-------------------------------------------------------------------------
Frozen rule:

    value = beta * GAIN_UNIT * score          (GAIN_UNIT = 200)
    rhs   = rich_rate * H + PROBE_COST        (H = 40,  PROBE_COST = 4)
    probe iff value > rhs

The two sides are both "reward units", but they are totals computed over two
DIFFERENT horizons, and only one of them has anything to do with a probe:

  * the value side prices a per-step gap over the DECLARED valuation horizon
    (GAIN_UNIT = 200 steps of a full gap);
  * the price side bills the alternative's payoff over H = 40 steps -- while a
    probe actually consumes PROBE_BLOCK = 20 steps (union_agent.PROBE_BLOCK).

Consequence, pure arithmetic: no candidate can carry a score above the
achievable headroom, so the rule can approve NOTHING once

    GAIN_UNIT * (1 - rich) <= rich * H + PROBE_COST
    <=>  rich >= (GAIN_UNIT - PROBE_COST) / (GAIN_UNIT + H) = 196/240 = 0.81666...

Above that level the arbiter's silence is not a decision: it rejects even a
maximal-gap candidate, because the bar grows linearly with the world's reward
while the attainable gap shrinks. The maskr instance (rich ~ 0.92) sits above
it, which is why turn 129 measured the two-part union beating the three-part
one there.

THE REPAIR -- ONE SUBSTITUTION, NO NEW KNOB
-------------------------------------------
Bill exactly what the probe costs:

    rhs = rich_rate * PROBE_LEN + PROBE_COST,   PROBE_LEN = PROBE_BLOCK = 20

`PROBE_LEN` is not a free parameter introduced to move a verdict: it is the
campaign's own declared probe-block length (turn-128 A3, `union_agent.
PROBE_BLOCK`), i.e. the number of steps actually spent off the alternative. The
driver asserts the two constants agree. Nothing else changes: the same beta,
the same GAIN_UNIT, the same PROBE_COST, the same candidate list, the same
"probe iff value > price" form.

WHAT THE FIX DOES AND DOES NOT DO (stated BEFORE the run)
--------------------------------------------------------
* The bar the rule sets on a candidate's gap is now
      gap_bar(rich) = (rich * PROBE_LEN + PROBE_COST) / GAIN_UNIT,
  linear in the world's reward level with slope 20/200 = 0.10 instead of
  40/200 = 0.20.
* The rule still has a hard cutoff, at rich = (GAIN_UNIT - PROBE_COST) /
  (GAIN_UNIT + PROBE_LEN) = 196/220 = 0.8909. **This cutoff is NOT an artefact
  and cannot be removed**: it is the indifference point of the economics -- when
  the alternative already pays r per step, the largest conceivable gain is
  (1 - r) per step, so once (1 - r) * GAIN_UNIT < r * PROBE_LEN + PROBE_COST,
  no probe can pay for itself, whatever the candidate.
* So the honest claim is NOT "the effect disappeared". It is: the old cutoff
  sat at a level dictated by a horizon that has nothing to do with the probe
  (0.8167), the corrected one sits at the level dictated by the probe itself
  (0.8909), and in the band 0.8167 < rich < 0.8909 the old rule refuses while
  probing is profitable by direct arithmetic. That band is the falsifiable
  difference between the two rules and is measured in `sweep_arbiter_v2.py`.
* beta = 0 still clears nothing (rhs > 0 always): the C1 control survives the
  repair, which the sweep re-checks on every base.

HONEST LIMIT, DECLARED NOW
--------------------------
GAIN_UNIT = 200 is a DECLARED AGENT CONSTANT (the value of a full gap, in reward
units), not a world quantity. The corrected cutoff therefore still depends on it;
the sweep re-runs the comparison at GAIN_UNIT in {100, 200, 400} so the reader
can see whether a verdict hangs on that declaration.
"""
from collections import namedtuple

Plan = namedtuple("Plan", "probe_order values rhs rich_rate")

GAIN_UNIT = 200.0            # declared utility scale: reward units per unit gap
PROBE_LEN = 20.0             # = union_agent.PROBE_BLOCK, the declared probe length
PROBE_COST_DEFAULT = 4.0     # declared per-candidate probe cost
H_DEFAULT = 40.0             # RETIRED from the price; kept so old call
                             # signatures stay valid


def plan(cands, rich_rate, beta=1.0, horizon=None,
         probe_cost=PROBE_COST_DEFAULT, probe_len=None, gain_unit=None):
    """Return a Plan: the ranked candidates that clear the bar, in order.

    price = rich_rate * PROBE_LEN + PROBE_COST   (the alternative's payoff over
            the steps a probe actually spends, plus the declared probe cost)
    value = beta * GAIN_UNIT * score            (unchanged from the frozen rule)
    probe iff value > price.
    """
    pl = PROBE_LEN if probe_len is None else float(probe_len)
    gu = GAIN_UNIT if gain_unit is None else float(gain_unit)
    rhs = rich_rate * pl + probe_cost
    order = []
    values = []
    for c in cands:
        v = beta * gu * c.score
        values.append(round(v, 4))
        if v > rhs:
            order.append(c)
    return Plan(order, values, round(rhs, 4), rich_rate)


def would_probe(cands, rich_rate, beta=1.0, **kw):
    return bool(plan(cands, rich_rate, beta, **kw).probe_order)


# ---- the two cutoffs, as arithmetic (used by the report and the verifier) ----
def cutoff_old(gain_unit=GAIN_UNIT, probe_cost=PROBE_COST_DEFAULT,
               horizon=H_DEFAULT):
    """GAIN_UNIT*(1-r) = r*H + c  ->  r = (GU - c)/(GU + H)."""
    return (gain_unit - probe_cost) / (gain_unit + horizon)


def cutoff_new(gain_unit=GAIN_UNIT, probe_cost=PROBE_COST_DEFAULT,
               probe_len=PROBE_LEN):
    """GAIN_UNIT*(1-r) = r*PROBE_LEN + c  ->  r = (GU - c)/(GU + PROBE_LEN)."""
    return (gain_unit - probe_cost) / (gain_unit + probe_len)


def max_achievable_score(rich_rate):
    """The headroom bound: no candidate can promise more than 1 - rich per step
    over the best alternative the agent already sees."""
    return max(0.0, 1.0 - rich_rate)


if __name__ == "__main__":
    # arithmetic self-check: the band where the two rules must disagree
    co, cn = cutoff_old(), cutoff_new()
    print("cutoff_old = %.6f   cutoff_new = %.6f" % (co, cn))
    for r in (0.80, 0.83, 0.87, 0.89, 0.92):
        g = max_achievable_score(r)
        v = GAIN_UNIT * g
        print("rich=%.2f  max_gap=%.4f  value=%.2f  rhs_old=%.2f rhs_new=%.2f"
              "  old=%s new=%s" % (r, g, v, r * H_DEFAULT + PROBE_COST_DEFAULT,
                                   r * PROBE_LEN + PROBE_COST_DEFAULT,
                                   v > r * H_DEFAULT + PROBE_COST_DEFAULT,
                                   v > r * PROBE_LEN + PROBE_COST_DEFAULT))
    assert cn > co, "the repair must RAISE the level at which silence is forced"
