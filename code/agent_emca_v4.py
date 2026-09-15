"""EMCA v4 agents -- the EPISTEMIC-VALUE arms (turn 105, directive
op_097e99fae22e + op_6d6b5f5a1105). Two lineages, identical survival
competences -- the ONLY difference is what the causal layer tells the
planner to do.

The core finding of the disk-read: the v3.2+ _plan() has a
HARDCODED armour -- `if a == "grasp" and e == "bell_rang": continue`
plus a fixed chime-scent route -- that silently disabled the decoy
edge's actionable content for every arm since turn 101. A world that
prices the FALSE BELIEF cannot run believers with that armour on.
The v4 arms REMOVE the armour: decoy edges of THIS world
((grasp, torch_lit), (grasp, bell_rang)) are fired like any other
causal route. The v3.3 baseline arms (armour on) stay in the matrix
as controls: v4_believer vs emca_v21 isolates armour+decoy exactly.

ARM DESIGN (identical menus, identical competences, armour OFF):
  AgentV4Pooled -- v2.1 pooled identifier: ACCEPTS both decoys. When
    the torch goal is active, its causal block fires 'grasp' at the
    brazier (flame tile in view): it believes grasping banks torches,
    pays 1.8/empty grasp INSIDE the scorch pocket, away from the
    storm tree.
  AgentV4Spec   -- v2.2 spec-gated (decoy accepted 15/15 at v3.3):
    a second believer, replicate.
  AgentV4       -- v2.5c stratified (AgentV33 lineage): REJECTS both
    decoys. Its torch plan is the WORLD-KNOWLEDGE route: scent->torch,
    walk onto the brazier cell and STAND there (the collect is by
    standing). Epistemic honesty must pay HERE.
  AgentV4Assoc  -- assoc-only: NO causal route for the torch goal;
    the goal falls through to the scent route (correlation control).
  AgentV4Curious / AgentV4CuriousPure -- curiosity lineages (the
    directive's part 3: bitter curiosity).
"""
import random
from collections import defaultdict

from agent_emca_v2 import EMCA
from agent_emca_v33 import (
    V33Mixin, view_features33, AgentCuriousChain as _ChainBase,
    AgentCuriousPureV33 as _PureBase,
)
from sanity_stratified3 import AgentV25c
from agent_emca_v2 import ACTIONS
from env_terrarium_v2 import (
    BERRY, LEVER, TREASURE, BELL_GLOW, TREE, KEY,
)
from agent_emca_v31 import CHIME
from env_terrarium_v4 import TRAP_CELL, BRAZIER_TILE

TREASURY_TILE = "$"
ALTAR_TILE = "A"


def view_features4(obs):
    f = dict(view_features33(obs))
    v = obs["view"]
    f["torch_near"] = v.count(BRAZIER_TILE)
    f["treasury_near"] = v.count(TREASURY_TILE)
    return f


class V4Mixin(V33Mixin):
    """v4 planning layer: torch goal in the menu, the treasury
    competence, and the DECOY-ARMOUR REMOVED from the edge block.
    Identifier untouched."""

    GOAL_MENU = [
        ("homeostasis", "restore energy", "energy_high", 200, BERRY),
        ("explore", "open the door", "lever", 800, LEVER),
        ("key", "obtain the key", "key", 1200, KEY),
        ("tree", "gather the storm fruit", "tree_gather", 800, TREE),
        ("ring", "make the bell ring", "ring_collected", 600, BELL_GLOW),
        ("altar", "sprout a patch berry", "patch_berry", 900, ALTAR_TILE),
        ("torch", "bank a treasury torch", "torch_bank", 800, BRAZIER_TILE),
        ("treasure", "obtain the treasure", "treasure", 2000, TREASURE),
        ("curiosity", "find novel transitions", "novelty", 400, None),
    ]
    WANTING_COOLDOWN = 1500
    IDENTIFIER_VERSION = None

    # ---- effect maps: torch goal satisfiers ----
    def _effect_matches(self, e, target):
        m = {"energy_high": ("ate", "energy_rose", "tree_gather"),
             "lever": ("lever",),
             "key": ("key",),
             "tree_gather": ("tree_gather",),
             "ring_collected": ("bell_rang", "chime"),
             "patch_berry": ("patch_berry",),
             "torch_bank": ("torch_lit", "torch_collect", "treasury_ate"),
             "treasure": ("treasure",),
             "novelty": (), "rich": ()}
        return e in m.get(target, ())

    def _effect_tile_for_edge(self, a, e):
        m = {"patch_berry": ALTAR_TILE, "tree_gather": TREE,
             "ate": BERRY, "lever": LEVER, "key": KEY,
             "bell_rang": BELL_GLOW, "chime": CHIME,
             "torch_lit": BRAZIER_TILE, "torch_collect": BRAZIER_TILE,
             "treasury_ate": TREASURY_TILE}
        return m.get(e)

    # ---- goal satisfaction: torch banked / treasury eaten ----
    def _goal_satisfied(self, g, o2, info):
        if g["target"] == "torch_bank":
            return info.get("torch_collect") is True
        return super()._goal_satisfied(g, o2, info)

    # ---- feature plumbing: every f in the goal/plan chain is v4 ----
    def act(self, o):
        f = view_features4(o)
        self._last_view = o["view"]
        if f["energy_low"] and f["berry_near"] > 0 \
                and "eat" in o.get("afford", ()):
            return "eat"
        scent = o.get("scent") or {}
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        goal = self.goals.get(self.active_goal) if self.active_goal else None
        if goal is None:
            return self._default_act(f, o, scent)
        a = self._plan(goal, f, o, scent)
        if a is None:
            goal["status"] = "expired"
            goal["steps_pursued"] = goal["deadline"] + 1
            self.self_model[goal["kind"]][1] += 1
            self.active_goal = None
            return self._default_act(f, o, scent)
        return a

    # ---- treasury competence in the default act (all v4 arms) ----
    def _default_act(self, f, o, scent=None):
        if "eat" in o.get("afford", ()) \
                and f.get("treasury_near", 0) > 0 and o["energy"] < 100:
            return "eat"
        return super()._default_act(f, o, scent)


class V4BelieverMixin(V4Mixin):
    """The torch plan for believers (armour OFF, edge-driven):
    the causal/assoc block decides HOW to bank a torch. With the decoy
    edge (grasp, torch_lit) in the model, the plan fires 'grasp' at
    the brazier; without any torch edge (assoc arm may have none), the
    world-knowledge fallback (stand on the brazier) applies."""

    def _plan(self, goal, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        target = goal["target"]
        if target == "torch_bank":
            # the causal block FIRST (armour off): if the model says
            # an action banks torches, do it where the effect's tile is
            a = self._v4_edge_block(target, f, o)
            if a is not None:
                return a
            # world-knowledge fallback (no torch edge in the model)
            return self._torch_route(f, o, scent)
        return super()._plan(goal, f, o, scent)

    def _v4_edge_block(self, target, f, o):
        """The edge block with the v3.2 decoy armour REMOVED and the
        torch place-check made strict: grasp fires only where the
        effect tile (the brazier) is IN VIEW."""
        edges = self.causal_edges() if self.use_causal else self.assoc_edges()
        cands = [(p, a, e) for (a, e), p in edges.items()
                 if self._effect_matches(e, target)]
        cands.sort(reverse=True)
        for p, a, e in cands:
            if not self._affordable(a, o, f):
                continue
            tile = self._effect_tile_for_edge(a, e)
            if a == "grasp":
                if tile is None or tile not in (self._last_view or ""):
                    continue     # fire grasp only at the effect's tile
                return a
            return a
        return None

    def _torch_route(self, f, o, scent):
        """World knowledge: walk onto the brazier and STAND. Energy-
        gated (below 45 the scorch pocket is lethal)."""
        if o["energy"] < 45:
            tc = self._tree_competence(f, o)
            if tc is not None:
                return tc
            if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                return "eat"
            return self._toward(BERRY)
        if self._last_view and self._last_view[4] == BRAZIER_TILE:
            return "wait"
        if f["torch_near"] > 0:
            return self._toward(BRAZIER_TILE)
        s = self._scent_step(scent, "torch")
        if s:
            return s
        return None


class V4RejectorMixin(V4Mixin):
    """The torch plan for the stratified rejector (AgentV4, the
    AgentV33 lineage): its causal model has NO torch edge (the decoy
    rejected, torch_collect not yet learned) -- the plan uses the
    world-knowledge route directly. Same route the assoc arm falls to
    -- the contrast with the believer is the EDGE, not the route."""

    def _plan(self, goal, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        if goal["target"] == "torch_bank":
            return self._torch_route(f, o, scent)
        return super()._plan(goal, f, o, scent)

    _v4_edge_block = None
    _torch_route = V4BelieverMixin._torch_route


# ---- the concrete arms ------------------------------------------------
class AgentV4Pooled(V4BelieverMixin, EMCA):
    """BELIEVER: pooled v2.1 -- both decoys accepted."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", None)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.1-pooled + v4 torch goals (ARMOUR OFF)"


class AgentV4Spec(V4BelieverMixin, EMCA):
    """BELIEVER replicate: v2.2 spec-gated."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", 0.10)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.2-spec + v4 torch goals (ARMOUR OFF)"


class AgentV4Assoc(V4BelieverMixin, EMCA):
    """Assoc-only: torch goal has no CAUSAL route; the assoc layer may
    carry the decoy but the plan falls through to the world route."""
    def __init__(self, *args, **kw):
        kw.setdefault("use_causal", False)
        super().__init__(*args, **kw)
        self.identifier_version = "assoc-only + v4 torch goals"


class AgentV4(V4RejectorMixin, V33Mixin, AgentV25c):
    """REJECTOR: v2.5c stratified (the AgentV33 lineage + v4 layer)."""
    IDENTIFIER_VERSION = "v2.5c-stratified + v4 torch goals (world route)"
