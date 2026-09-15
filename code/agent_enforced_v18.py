"""agent_enforced_v18.py -- turn 152, the v18 arms. NO NEW POLICY CODE except one
declared five-line escape instrument.

Owner directive msg_00152 -> NEW_TZ.md item 2. v16's scope lived in the agent; v18's
lives in the world (see env_enforced_v18.py). So the arms here are v16's arms and the
frozen base, IMPORTED VERBATIM, plus exactly one new arm:

  w_widen -- the frozen base with a declared WIDENING REQUEST appended: it calls the
             frozen `act`, and if that result is a non-move action on the harmful
             tile (i.e. the act the world's boundary would refuse), it returns
             "widen" instead. That is the whole arm: five lines, labelled in the
             prereg as an INSTRUMENT whose only purpose is to make "the agent asks
             for more" measurable -- not a model of a real agent's escape behaviour.

Everything else is re-exported unchanged, and the independent pass checks the
sha256 of `agent_scope_v16.py` and `agent_safety_v10.py`, so "no new policy code"
is a machine fact rather than a claim.
"""
from agent_emca_v7 import MOVES, NONMOVE
from agent_safety_v10 import AgentSafetyBase
from agent_scope_v16 import (
    WNone, WPrice, WGiven, NDoctor, NPump, NDoctorPrice, NPumpPrice, ScopeAgent,
)


class WWiden(AgentSafetyBase):
    """The frozen base + a declared widening request on the harmful act."""

    IDENTIFIER_VERSION = "v18 widen: frozen base + a widening request"

    def act(self, o):
        a = AgentSafetyBase.act(self, o)
        f = self._feat(o)
        if a in NONMOVE and f["on_rich"] and "widen" in o.get("afford", ()):
            return "widen"
        return a


ARMS = {
    "w_none": WNone,
    "w_price": WPrice,
    "w_given": WGiven,
    "n_doctor": NDoctor,
    "n_pump": NPump,
    "n_doctor_price": NDoctorPrice,
    "n_pump_price": NPumpPrice,
    "w_widen": WWiden,
}


def make_agent(arm, seed):
    return ARMS[arm](seed)