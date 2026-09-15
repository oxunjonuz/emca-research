"""arbitration_v8.py -- the payoff-reading arbiter (claims C and F).

WHAT THIS MODULE DECIDES: whether to pay for evidence -- the probe -- or
spend the same steps on the harvest or on the permitted alternative.

It is a dimensionally consistent value-of-information calculation, and
that is the point: CONTINUOUS CONFIDENCE ENTERS THE DECISION ITSELF, not
only the belief. The agent probes iff

    (1 - gamma_pre) * home_gain * remaining_steps   >   home_gain * probe_steps
        [ the value of finding out ]                    [ what the probe forgoes ]

with `home_gain = max(0, home_yield_obs - rich_rate_obs)` measured from
the agent's OWN reward stream. Divide through by home_gain (>0) and the
rule reads: the probe is worth it iff the remaining opportunity, shrunk
by what is already known, exceeds the probe's own duration. Consequences,
all declared in PREREG_V8 §2 and all measurable:

  * home_gain = 0 (the alternative pays at least as well as the harvest)
    -> the right-hand side is not larger, the agent does not probe at
    all. That is the payoff-reading leg (claim F3).
  * gamma_pre -> 1 (already known) -> no probe: a confident agent does
    not spend on evidence it has.
  * probe_steps appears on the cost side, so the SAME rule makes a
    cheap protocol affordable and an expensive one marginal -- the
    threshold protocol's price is visible to the agent itself.

The module reads no world constants and contains no world tokens; every
quantity it consumes was produced by the agent (its own reward stream,
its own tables, its own clock).
"""


def home_gain(home_yield_obs, rich_rate_obs):
    """The harvest's edge over the permitted alternative, in reward per
    step, from the agent's own measurements. Never negative: a negative
    edge means the alternative already wins, so knowledge is worth 0."""
    if home_yield_obs is None or rich_rate_obs is None:
        return 0.0
    return max(0.0, float(home_yield_obs) - float(rich_rate_obs))


def value_of_information(home_gain_val, gamma_pre, remaining_steps,
                         tau=1.0):
    """tau * (1 - gamma_pre) * home_gain * remaining_steps."""
    g = max(0.0, min(1.0, float(gamma_pre)))
    return (float(tau) * (1.0 - g) * max(0.0, float(home_gain_val))
            * max(0, int(remaining_steps)))


def decision(home_yield_obs, rich_rate_obs, gamma_pre, remaining_steps,
             probe_steps, tau=1.0, floor=4.0):
    """Return (should_probe, value, cost). `probe_steps` is the number of
    steps the protocol will occupy (forgone harvest). `floor` is the
    agent's declared flat cost of setting up any experiment."""
    hg = home_gain(home_yield_obs, rich_rate_obs)
    value = value_of_information(hg, gamma_pre, remaining_steps, tau)
    cost = hg * float(probe_steps) + float(floor)
    if hg <= 0.0:
        return False, round(value, 3), round(cost, 3)
    return bool(value > cost), round(value, 3), round(cost, 3)
