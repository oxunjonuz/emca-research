"""agent_emca_v9.py -- turn 133 (owner directive msg_00133).

The task: take the IMPROVED causal mechanism (the union: context-specificity +
exploration under thin evidence, WITHOUT the broken cost-aware arbiter) back into
the EMCA agent, replacing the old C2/C1 machinery, and re-run the final part of
the campaign on the ORIGINAL Terrarium world (v7 -- the world with goals,
planning, memory), to ask whether the improved mechanism finally buys a
MEASURABLE ADVANTAGE in a full agent world.

WHAT IS REPLACED, EXACTLY
  `_candidates()` (v7: generator + designer list + permutation + injection) and
  `_plan()` (v7: the priced arbiter arbitration.plan) are replaced by
  `union_layer_v9.UnionCausalLayer`:
      candidates = candidate_gen.generate over the agent's per-context tables
                   (context contrast)  UNION  exploration under thin evidence
      decision   = the top UNVERIFIED candidate is probed; no price, no beta.
  Kept verbatim (inherited from agent_emca_v7.AgentV7Base, whose module is NOT
  modified by this turn): the shared filing path and context attribution, the
  aura probe protocol (alternated blocks, exact Fisher p<0.05 and RR>=1.3,
  PROBE_MAX_BLOCKS=80), the survival competence, the exploration waypoint
  schedule (EXPLORE_END=3000), the navigation, the goal/planning layer and the
  exploitation branch. `env_terrarium_v7.py` is not touched at all: this
  transplant is agent-side only.

THE ONE STRUCTURAL FACT THE OWNER'S PROPOSAL HAS TO MEET (declared in
research/PREREG_V9.md before the first run): in v7 the exploitation branch fires
when the arbiter's accepted list is EMPTY. Removing the price removes the only
thing that ever emptied that list -- so the unconditional arm has no stop rule
and, since one candidate costs 800 scheduled steps and the world holds ~28
(action, effect) pairs, it can spend the whole life probing and never reach the
branch that collects the prize. `AgentV9Stop` is therefore part of the design,
not a rescue: it stops probing as soon as the agent's own protocol has issued
ONE CAUSAL verdict (a rule about the agent's own state, not a threshold), and
exploits from there.

ARMS
  AgentV9Union  -- ctx + exploration, unconditional probe (the requested form).
  AgentV9NoExp  -- ctx only, unconditional probe (ablation of source 2).
  AgentV9NoCtx  -- pooled discovery + exploration, unconditional probe.
  AgentV9Fixed  -- designer list, unconditional probe (hidden-hardcode control).
  AgentV9Stop   -- ctx + exploration + stop-on-first-CAUSAL (the recommended
                   composition if the prediction in the prereg holds).
  AgentV7Full / AgentV7Oracle / AgentV7Forager / AgentV7Random -- the frozen v7
                   arms, imported byte-identical, run through the SAME runner.
"""
from agent_emca_v7 import (          # noqa: F401  (re-exported unchanged)
    AgentV7Base, AgentV7Full, AgentV7Beta0, AgentV7Perm, AgentV7NoGen,
    AgentV7Oracle, AgentV7Forager, AgentV7Random, EXPLORE_END, MOVE_DELTA,
    NONMOVE, ACTIONS,
)
from union_layer_v9 import UnionCausalLayer

# the shared probe protocol holds the agent's position in the aura; the three
# in-place actions are its target vocabulary and the (frozen) control chooser,
# and it cannot hold a position for a move. Declared here, identically for every
# arm; the SELECTION among them and the choice of effect stay computed from the
# agent's own tables. (Contrast: in the v7 arms the designer list happens to name
# "wait" and no world token appears in the union layer.)
PROBE_ACTIONS = tuple(sorted(NONMOVE))


class AgentV9Union(UnionCausalLayer, AgentV7Base):
    """The improved mechanism: context contrast + exploration, no price."""
    USE_CTX = True
    USE_EXP = True
    PROBE_ACTIONS = PROBE_ACTIONS
    EXPLORE_END = EXPLORE_END
    STOP_ON_CAUSAL = False
    IDENTIFIER_VERSION = "v9 union layer (ctx + exploration, no price)"

    def _vocab(self):
        v = set(getattr(self, "action_vocab", ()))
        v |= set(PROBE_ACTIONS)
        self.action_vocab = sorted(v)

    def act(self, o):
        self._vocab()
        return super().act(o)

    def observe(self, o, a, r, o2, done, info):
        # the action vocabulary is what the observations offer (opaque strings)
        # plus the declared probe vocabulary -- the layer itself names nothing.
        v = set(getattr(self, "action_vocab", ()))
        v |= set(o.get("afford", ()))
        self.action_vocab = sorted(v)
        super().observe(o, a, r, o2, done, info)

    # ---- the stop rule, when the arm declares one --------------------
    def _plan(self):
        plan = super()._plan()
        if self.STOP_ON_CAUSAL and any(
                v.get("verdict") == "CAUSAL" for v in self.verdicts.values()):
            from union_layer_v9 import Plan
            return Plan([], [], 0.0, self.rich_rate_obs)
        return plan


class AgentV9Stop(AgentV9Union):
    """Union + stop-on-first-CAUSAL: probe until the agent's own protocol has
    issued one CAUSAL verdict, then exploit."""
    STOP_ON_CAUSAL = True
    IDENTIFIER_VERSION = "v9 union layer + stop on first CAUSAL"


class AgentV9NoExp(AgentV9Union):
    """Ablation: the exploration term is off (context contrast only, no price)."""
    USE_EXP = False
    IDENTIFIER_VERSION = "v9 union layer, exploration ablated"


class AgentV9NoCtx(AgentV9Union):
    """Ablation: the context split is off (pooled discovery + exploration)."""
    USE_CTX = False
    IDENTIFIER_VERSION = "v9 union layer, context split ablated"


class AgentV9Fixed(AgentV9Union):
    """Hidden-hardcode control: the SAME union machinery, but the candidate list
    is a fixed designer constant (the v7 'designer' candidate), so any advantage
    of the union over this arm is attributable to self-generation."""
    USE_CTX = False
    USE_EXP = False
    IDENTIFIER_VERSION = "v9 control: fixed designer candidate list"

    def _candidates(self):
        from candidate_gen import Candidate
        if self.t < EXPLORE_END:
            return []
        return [Candidate("wait", "hum", "designer", 0.3, 0.2, 999, 0.10)]


class AgentV9Oracle(AgentV9Union):
    """Analysis device (never in a fairness verdict): the true edge is injected
    into the union's own list at EXPLORE_END, giving the mechanism the ceiling."""
    IDENTIFIER_VERSION = "v9 union layer + INJECTED edge (oracle device)"

    def __init__(self, seed=0, edge=("wait", "hum")):
        super().__init__(seed)
        self.INJECT_EDGE = edge


ARMS = {
    "v9_union": AgentV9Union,
    "v9_stop": AgentV9Stop,
    "v9_noexp": AgentV9NoExp,
    "v9_noctx": AgentV9NoCtx,
    "v9_fixed": AgentV9Fixed,
    "v9_oracle": AgentV9Oracle,
    "v9_old": AgentV7Full,        # the frozen v7 mechanism, untouched module
    "v9_oldoracle": AgentV7Oracle,  # the frozen v7 oracle (ceiling comparator)
    "v9_forager": AgentV7Forager,   # reward floor
    "v9_random": AgentV7Random,     # brute-force floor
}


def make_agent(arm, seed, edge_action="wait"):
    cls = ARMS[arm]
    if arm in ("v9_oracle", "v9_oldoracle"):
        return cls(seed, edge=(edge_action, "hum"))
    return cls(seed)
