"""arbitration.py -- the FROZEN arbitration rule (claim C1).

C1 asks whether the decision "verify a hypothesis or exploit the
permitted alternative" is COMPUTED from the agent's own epistemic state
plus the world's reward structure -- or scheduled/hardcoded.

THE FROZEN RULE (research/PREREG_V7.md, amendment A1):

    for each candidate k in ranked order:
        value_k = beta * GAIN_UNIT * score_k      (the agent's own gap)
        rhs     = rich_rate * H + PROBE_COST      (what exploiting pays)
        probe k  iff  value_k > rhs

The rule is evaluated candidate by candidate down the ranked list, so
the NUMBER of candidates verified is itself a computed quantity: a cheap
alternative (small rich_rate) clears more candidates; an expensive one
clears fewer; beta=0 clears none. That is the operational meaning of
"the price of truth is measured, not scheduled".

Quantities:
  score_k     -- the bounded exclusivity gap from candidate_gen (0..1),
                 derived ONLY from the agent's own tables.
  GAIN_UNIT   -- the agent's DECLARED utility scale (how much a full
                 gap is worth in reward units). A declared constant of
                 the agent, like beta -- not read from the world.
  rich_rate   -- reward per step the alternative actually pays, OBSERVED
                 by the agent from its own reward stream while standing
                 on the alternative (the world's config is never read).
  H           -- the agent's declared evaluation horizon (steps).
  PROBE_COST  -- the agent's declared per-candidate probe-cost estimate.
  beta        -- the weight of epistemic value (0 -> pure reward seeker).

The two controls that make this auditable:
  * beta=0   -> value_k = 0 for every k, so no candidate clears a positive
                rhs: the arm can never probe when the alternative pays.
                If it probes anyway, the priority is hardcoded.
  * permute  -> the rule must follow the permuted ranking (candidate_gen.
                permute). If the probe order does not follow, the decision
                is constant, not computed.

This module reads NO world constants and contains no world tokens.
"""
from collections import namedtuple

Plan = namedtuple("Plan", "probe_order values rhs rich_rate")

GAIN_UNIT = 200.0          # the agent's declared utility scale (per gap)
H_DEFAULT = 40.0           # the agent's declared evaluation horizon
PROBE_COST_DEFAULT = 4.0   # the agent's declared per-candidate probe cost


def plan(cands, rich_rate, beta=1.0, horizon=H_DEFAULT,
         probe_cost=PROBE_COST_DEFAULT):
    """Return a Plan: the ranked candidates that clear the bar, in order.
    `cands` is the ranked candidate list (candidate_gen output).
    `rich_rate` -- the agent's own observed alternative payoff/step."""
    rhs = rich_rate * horizon + probe_cost
    order = []
    values = []
    for c in cands:
        v = beta * GAIN_UNIT * c.score
        values.append(round(v, 4))
        if v > rhs:
            order.append(c)
    return Plan(order, values, round(rhs, 4), rich_rate)


def would_probe(cands, rich_rate, beta=1.0, horizon=H_DEFAULT,
                probe_cost=PROBE_COST_DEFAULT):
    p = plan(cands, rich_rate, beta, horizon, probe_cost)
    return bool(p.probe_order)