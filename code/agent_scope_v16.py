"""agent_scope_v16.py -- turn 149, the SCOPE line (owner directive msg_00149).

Owner: *"сравни двух агентов -- одного с широким набором возможных действий и
целей, другого узко специализированного на одной задаче (как в примере
владельца -- агент-врач всегда лечит, и ничего больше)."*

THE ONE CONSTRUCTION RULE (v10's, inherited): no line of the frozen policy is
copied. Every arm subclasses `agent_safety_v10.AgentSafetyBase`, whose `act`
CALLS the frozen `agent_emca_v7.AgentV7Base.act` and guards its output. Here the
guard is a SCOPE FILTER, not a brake: it decides which of the frozen policy's
outputs are inside the agent's declared task.

  WIDE arms (re-exported from v12, byte-identical classes):
    w_none   -- the frozen policy, no brake (v10 B0)
    w_price  -- the frozen B4 brake: harvest only if own rich_rate_obs > SOCIAL_COST
    w_given  -- v10 B2 rule: no harvest while commons < 10

  NARROW arms (the only new code):
    n_doctor       -- TASK="station": travel to STATION and tend it. It CANNOT
                      harvest the rich patch (not its task).
    n_pump         -- TASK="rich": travel to RICH and harvest. It CANNOT tend the
                      station, verify, or park.
    n_doctor_price -- the SAME scope as n_doctor, with the B4 brake class present.
                      The brake can never fire (the doctor's scoped action is
                      never a rich harvest), so this arm must be BYTE-IDENTICAL to
                      n_doctor -- the identity licence for the scope layer (H6).
    n_pump_price   -- TASK="rich" WITH the B4 brake: the harm is INSIDE the scope,
                      so the brake is live and the bribe is on the measured channel.

SURVIVAL IS KEPT IN EVERY SCOPE. The berry competence is the BODY, not a
privilege: a scope that lets the agent starve is not a scope, it is a bug. The
scope layer therefore calls the frozen `_survival` first and only filters what
remains. Declared in PREREG_SCOPE_V16.md §3.

WHAT THE SCOPE LAYER IS NOT ALLOWED TO DO: it does not compute a rate, does not
scale a rate, does not touch the frozen tables, and does not invent a new
preference. It only replaces an out-of-scope action with the task's own action
(an affordable non-move when in position, otherwise a move toward the task
landmark). The brake, where present, is v10's declared B4 rule verbatim.
"""
from agent_emca_v7 import AgentV7Base, MOVES, NONMOVE
from agent_safety_v10 import (AgentSafetyBase, SOCIAL_COST, MIN_OBS,
                              S2GivenRule, S4Internalized)

# the wide arms: the v12 classes, unchanged
WNone = AgentSafetyBase
WPrice = S4Internalized
WGiven = S2GivenRule


class ScopeAgent(AgentSafetyBase):
    """The frozen policy with its OUTPUT filtered to one declared task."""

    TASK = None          # "station" | "rich"
    BRAKE = False        # the B4 rule on the scoped action (only reachable if TASK=="rich")
    IDENTIFIER_VERSION = "scope v16 base"

    def _task_nonmove(self, f):
        """An affordable non-move for the task: the task's own action."""
        return "wait" if "wait" in f["afford"] else None

    def _brake_fires(self):
        """v10's B4 rule, verbatim: block a rich harvest once the agent's OWN
        measured rate is at or below SOCIAL_COST (after MIN_OBS harvests)."""
        return (getattr(self, "rich_steps", 0) >= MIN_OBS
                and self.rich_rate_obs <= SOCIAL_COST)

    def _brake_substitute(self, o, f):
        self.guard_blocks += 1
        self.guard_reason = "rate<=%.2f" % SOCIAL_COST
        s = self._nav(o.get("scent"), "station", f)
        return s if s else self.rng.choice(MOVES)

    def act(self, o):
        f = self._feat(o)
        # survival is the body, not a privilege -- kept in every scope.
        # DEFECT FIX (turn 149, found by H3 failing): the brake must apply to
        # the BODY's output too. The frozen v10 B4 arm guards the OUTPUT of the
        # frozen `act`, which includes the survival branch -- so a starvation
        # "wait" on RICH is blocked there. My first version returned survival
        # UNGUARDED, and the pump broke its own brake through exactly that hole:
        # at energy < LOW_ENERGY the frozen survival returns "wait" on RICH, the
        # pump harvested, its measured rate stayed 0.29, and it drained all 30.
        # The wide arm never had the hole because v10's guard wraps the frozen
        # act. Fixed to the same semantics; the pump's brake now blocks a
        # survival harvest exactly as w_price's does.
        surv = self._survival(o, f)
        if surv is not None:
            if self.BRAKE and surv in NONMOVE and f["on_rich"] \
                    and self._brake_fires():
                return self._brake_substitute(o, f)
            return surv
        if self.TASK == "station":
            if f["on_station"]:
                a = self._task_nonmove(f)
                if a is not None:
                    return a
            s = self._nav(o.get("scent"), "station", f)
            return s if s else self.rng.choice(MOVES)
        # TASK == "rich"
        if f["on_rich"]:
            if self.BRAKE and self._brake_fires():
                return self._brake_substitute(o, f)
            a = self._task_nonmove(f)
            if a is not None:
                return a
        s = self._nav(o.get("scent"), "rich", f)
        return s if s else self.rng.choice(MOVES)


class NDoctor(ScopeAgent):
    TASK = "station"
    IDENTIFIER_VERSION = "narrow: doctor (task=station, no brake)"


class NPump(ScopeAgent):
    TASK = "rich"
    IDENTIFIER_VERSION = "narrow: pump (task=rich, no brake)"


class NDoctorPrice(ScopeAgent):
    TASK = "station"
    BRAKE = True
    IDENTIFIER_VERSION = "narrow: doctor + inert B4 brake (identity licence)"


class NPumpPrice(ScopeAgent):
    TASK = "rich"
    BRAKE = True
    IDENTIFIER_VERSION = "narrow: pump + live B4 brake"


ARMS = {
    "w_none": WNone,
    "w_price": WPrice,
    "w_given": WGiven,
    "n_doctor": NDoctor,
    "n_pump": NPump,
    "n_doctor_price": NDoctorPrice,
    "n_pump_price": NPumpPrice,
}


def make_agent(arm, seed):
    return ARMS[arm](seed)