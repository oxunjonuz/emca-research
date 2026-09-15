"""agent_wirehead_v12.py -- turn 141, the v12 arms. THE AGENT IS 100% FROZEN.

Owner directive msg_00141: *"агент его не фальсифицирует"* -- the agent does not
falsify the signal; the forger does. So this module introduces NO new agent code at
all: every arm is the v10 safety arm (`agent_safety_v10`, whose `act` calls the
frozen `agent_emca_v7.AgentV7Base.act` and guards its output) with a brake
configured, plus v11's `NBound` for the displaced-goal arm. Nothing computes a
rate; nothing scales a rate; no counter the brake reads is touched.

  v_none    -- no brake (v10's B0). The identity anchor and the saturation control.
  v_given   -- v10's B2 rule: no harvest while `commons < 10`. Keyed on the WORLD's
               stock, which this line's observation carries. The architecture's
               other brake family; H4 asks whether money buys this one too.
  v_price   -- v10's B4 FROZEN: harvest only if `rich_reward / rich_steps >
               SOCIAL_COST`. Both counters are the frozen ones; a harvest step
               counts when `r > 0`, and the world pays `rich_rate` on every harvest
               even when nobody sponsors, so an unpaid harvest STILL enters the
               counters as a 0.05 entry. That is precisely why the frozen brake can
               only accumulate evidence, never lose it -- and it is the object v12
               prices.
  v_bound   -- v11's NBound: the goal is bound to the signal; walk to the beacon
               field and park there.

The machine check that this file adds no falsification is H8 (AST/keyword scan) plus
the identity battery H9/H9b in the independent pass.
"""
from agent_safety_v10 import AgentSafetyBase, S2GivenRule
from agent_wirehead_v11 import NBound, NONMOVE

ARMS = {
    "v_none": AgentSafetyBase,
    "v_given": S2GivenRule,
    "v_price": None,      # filled below: S4Internalized verbatim
    "v_bound": NBound,
}

from agent_safety_v10 import S4Internalized as _S4  # noqa: E402
ARMS["v_price"] = _S4


def make_agent(arm, seed):
    cls = ARMS[arm]
    if arm == "v_bound":
        # NBound takes only the seed (see agent_wirehead_v11)
        return cls(seed)
    return cls(seed)
