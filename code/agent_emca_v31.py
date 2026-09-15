"""EMCA v3.1 agents -- the ACTIONABLE-DECOY turn (turn 100, op_39d83261dc8e).

Identifier lineage is UNTOUCHED: the identifiers are the turn-99 ones
(v2.1 pooled / v2.2 spec / v2.5c stratified-RR / assoc-only), imported
without modification. What changes here is the GOAL+PLANNING layer, which
now has channels the turn-99 world did not offer:

  * the RING goal ("make the bell ring") -- satisfied by info['bell_rang'].
    The goal's effect-tile bridge maps it to the bell, so an agent that
    BELIEVES grasp->bell_rang (v2.1/v2.2 arms) will route to the bell and
    GRASP there; an agent that has rejected the decoy (v2.5c) has no
    causal route to the ring and will not chase it. This is the mechanism
    by which the identifier choice becomes BEHAVIOURAL.
  * WANTING-REFRESH: achieved goal kinds are re-issued after a cooldown
    (the turn-99 world demoted tree/key/treasure forever after one
    achievement/3 expiries -- self_model['key']=[0,3], treasures 0/21).
    The key goal is now satisfiable (info['key'] exists in v3.1) and
    re-issued, so the chain can actually be pursued.
  * GRASP COMPETENCE: the v3.1 storm tree is gathered with grasp; the
    planner treats a tree in reach exactly as it treats berries (the
    turn-99 opportunistic-tree fix, carried to the new action).
  * SCENT PURSUIT for the v3.1 channels: 'treasure' (key+door) and
    'bell' (a chime is down) join tree/key as scent-followable targets.

AgentCurious (direction 3, learning-progress generator): the goal
generators are REPLACED by a novelty/learning-progress loop -- the agent
seeks unseen (ctx, action, ctx') transitions, not outcomes. Its
identifier is v2.5c. It tests whether v2.5c's decoy rejection is
structural (survives a different trajectory generator) or an artifact of
the goal-driven generator.
"""
import random
from collections import defaultdict

from agent_emca_v2 import EMCA, view_features
from env_terrarium_v2 import (
    ACTIONS, BERRY, DOOR, LEVER, TREASURE, EMPTY, WALL,
    BELL_GLOW, BELL_DARK, TREE, KEY,
)
from sanity_stratified3 import AgentV25c

CHIME = "C"


def view_features31(obs):
    f = view_features(obs)
    f["chime_near"] = obs["view"].count(CHIME)
    return f


class V31Mixin:
    """Goal+planning layer for the v3.1 world. Identifier untouched."""

    IDENTIFIER_VERSION = None      # set by the concrete class

    # ---- acting entry: v3.1 features (chime) are visible to the planner ----
    def act(self, o):
        f = view_features31(o)
        self._last_view = o["view"]
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        scent = o.get("scent") or {}
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        goal = self.goals.get(self.active_goal) if self.active_goal else None
        if goal is None:
            return self._default_act(f, o, scent)
        a = self._plan(goal, f, o, scent)
        return a if a else self._default_act(f, o, scent)

    # ---- goal menu v3.1: ring goal added, wanting-refresh enabled ----
    GOAL_MENU = [
        ("homeostasis", "restore energy", "energy_high", 200, BERRY),
        ("explore", "open the door", "lever", 800, LEVER),
        ("key", "obtain the key", "key", 1200, KEY),
        ("tree", "gather the storm fruit", "tree_gather", 800, TREE),
        ("ring", "make the bell ring", "ring_collected", 600, BELL_GLOW),
        ("treasure", "obtain the treasure", "treasure", 2000, TREASURE),
        ("curiosity", "find novel transitions", "novelty", 400, None),
    ]
    WANTING_COOLDOWN = 1500        # steps before an achieved kind re-issues

    def _generate_goal(self, o, f):
        if f["energy_low"]:
            return self._mk("homeostasis", "restore energy", "energy_high", 200)
        if not self.use_goal_generators:
            return None
        expired_counts = defaultdict(int)
        for g in self.goals.values():
            if g["status"] == "expired":
                expired_counts[g["kind"]] += 1
        now = self.t
        if self.use_self_model:
            for kind, text, target, dl, _ in self.GOAL_MENU:
                if kind == "homeostasis":
                    continue
                achieved, attempts = self.self_model[kind]
                has_active = any(g["status"] == "active" and g["kind"] == kind
                                 for g in self.goals.values())
                if has_active:
                    continue
                # wanting-refresh: an ACHIEVED kind re-issues after the
                # cooldown (the turn-99 world demoted it forever -- the
                # measured cause of treasures 0/21)
                if achieved > 0:
                    last_done = max((g.get("achieved_at") or 0)
                                    for g in self.goals.values()
                                    if g["kind"] == kind) \
                        if any(g["kind"] == kind for g in self.goals.values()) \
                        else 0
                    if now - last_done >= self.WANTING_COOLDOWN:
                        return self._mk(kind, text, target, dl)
                    continue
                if attempts < 10 and expired_counts[kind] < 3:
                    return self._mk(kind, text, target, dl)
        if len(self.seen_transitions) < 80:
            return self._mk("curiosity", "keep exploring", "novelty", 400)
        if f["berry_near"] + f["door_near"] + f["lever_near"] \
                + f["treasure_near"] + f["tree_near"] + f["key_near"] == 0:
            return self._mk("empowerment", "reach richer context", "rich", 400)
        return None

    def _goal_satisfied(self, g, o2, info):
        t = g["target"]
        if t == "ring_collected":
            # NON-VACUOUS ring goal: satisfied only by COLLECTING a chime
            # (walking onto the ring's artifact at the bell). A bare
            # bell_rang happens stochastically every ~2-3 storm steps
            # anywhere in the world -- the first draft made the goal
            # vacuous (satisfied in 5 steps by chance, measured), so the
            # believing arm never routed to the bell.
            return info.get("chime") is True
        if t == "tree_gather":
            return info.get("tree_gather") is True
        return super()._goal_satisfied(g, o2, info)

    def _effect_matches(self, e, target):
        m = {"energy_high": ("ate", "energy_rose", "tree_gather"),
             "lever": ("lever",),
             "key": ("key",),
             "tree_gather": ("tree_gather",),
             "ring_collected": ("bell_rang", "chime"),
             "treasure": ("treasure",),
             "novelty": (), "rich": ()}
        return e in m.get(target, ())

    def _effect_tile(self, target):
        for kind, text, tgt, dl, tile in self.GOAL_MENU:
            if tgt == target and tile:
                return tile
        return None

    # ---- acting: grasp competence + scent pursuit for the new channels ----
    def _default_act(self, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # v3.1: the fruit hangs high -- grasp from ADJACENT to the tree
        # (tree in the 3x3 view), eat only on calm trees (eat interface)
        if f["tree_near"] > 0:
            if "eat" in o.get("afford", ()):
                return "eat"
            return "grasp"
        if f["chime_near"] > 0:
            return self._toward(CHIME)
        if f["key_near"] > 0:
            return self._toward(KEY)
        s = self._scent_step(scent, "bell") \
            or self._scent_step(scent, "tree") \
            or self._scent_step(scent, "key")
        if s:
            return s
        if f["energy_low"]:
            return self._toward(BELL_GLOW) if f["bell_glow_near"] \
                else self.rng.choice(["up", "down", "left", "right"])
        return self.rng.choice(["up", "down", "left", "right"])

    def _plan(self, goal, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        target = goal["target"]
        if f["energy_low"]:
            if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                return "eat"
            return self._toward(BERRY)
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # grasp competence (v3.1): the storm tree in reach is harvested
        # even while pursuing another goal -- the same competence rule as
        # the turn-99 opportunistic fixes, carried to the new action.
        # The fruit hangs HIGH: it is gathered while STANDING NEXT TO the
        # tree (the tree is in the 3x3 view), with grasp -- no need to
        # step onto the cell. (First draft required standing ON the cell;
        # the toy trace measured the agent grasping one cell away from a
        # visible tree until it starved -- 22 deaths/4000.)
        if f["tree_near"] > 0:
            return "grasp"
        # STORM COMPETENCE (v3.1, measured before adoption): during a
        # storm the tree is the ONLY food and the fury drains 2.4/step;
        # the trace showed the treasure/key goal monopolising storms while
        # the agent wandered 9-10 cells from the tree and died (16/29
        # deaths mid-storm). The tree scent overrides goal pursuit while
        # the storm rages -- the same competence rule as opportunistic
        # eating, one level up: in a storm, foraging IS the goal.
        if f["bell_glow_near"] > 0:
            s = self._scent_step(scent, "tree")
            if s:
                return s
        # a chime in reach is collected in passing (it is on the way)
        if f["chime_near"] > 0:
            return self._toward(CHIME)
        edges = self.causal_edges() if self.use_causal else self.assoc_edges()
        cands = [(p, a) for (a, e), p in edges.items()
                 if self._effect_matches(e, target)]
        cands.sort(reverse=True)
        for p, a in cands:
            if self._affordable(a, o, f):
                return a
        if target in ("tree", "key", "treasure", "bell"):
            s = self._scent_step(scent, target)
            if s:
                return s
        if self.use_episodes:
            tile = self._effect_tile(target)
            if tile:
                if not self._tile_in_view(tile):
                    return self._toward(tile)
                ctx = self._ctx_key(f)
                tried = self.tried_here[ctx]
                if len(tried) < len(ACTIONS):
                    untried = [a for a in ACTIONS if a not in tried]
                    return self.rng.choice(untried)
                if self._visit_count(ctx) % 8 == 0:
                    pref = [a for a in ("press", "eat", "grasp")
                            if self._affordable(a, o, f)]
                    if pref:
                        return pref[0]
        ctx = self._ctx_key(f)
        untried = [a for a in ACTIONS if a not in self.tried_here[ctx]]
        if untried:
            return self.rng.choice(untried)
        return None


class AgentV31(V31Mixin, AgentV25c):
    """v3.1 agent with the v2.5c stratified identifier (decoy rejected)."""
    IDENTIFIER_VERSION = "v2.5c-stratified-RR-doorgonefix + v3.1 goals"


class AgentV31Pooled(V31Mixin, EMCA):
    """v3.1 agent with the v2.1 pooled identifier (decoy accepted)."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", None)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.1-pooled + v3.1 goals"


class AgentV31Spec(V31Mixin, EMCA):
    """v3.1 agent with the v2.2 spec-gated identifier (decoy accepted)."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", 0.10)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.2-spec + v3.1 goals"


class AgentV31Assoc(V31Mixin, EMCA):
    """v3.1 agent with NO causal layer (assoc-only; decoy accepted)."""
    def __init__(self, *args, **kw):
        kw.setdefault("use_causal", False)
        super().__init__(*args, **kw)
        self.identifier_version = "assoc-only + v3.1 goals"


class AgentCurious(AgentV25c):
    """Direction 3: learning-progress / novelty generator instead of the
    outcome goal generators. The identifier is v2.5c (unchanged). The
    trajectory generator is the variable under test.

    Policy: with prob (1-eps) take the action that maximises expected
    NOVELTY GAIN in this context -- i.e. the action whose (ctx, a, ctx')
    transitions are least known -- else eps-random. Novelty is counted
    over seen_transitions. Survival competence (eat berries/grasp the
    tree when in reach) is kept: the question is the trajectory
    generator, not suicide.
    """
    IDENTIFIER_VERSION = "v2.5c-stratified-RR-doorgonefix + curiosity-gen"

    def __init__(self, *args, novelty_h=6, **kw):
        super().__init__(*args, **kw)
        self.novelty_h = novelty_h
        self.trans_counts = defaultdict(lambda: defaultdict(int))
        self.identifier_version = self.IDENTIFIER_VERSION

    def observe(self, o, a, r, o2, done, info):
        f1 = view_features(o)
        f2 = view_features(o2)
        self.trans_counts[self._ctx_key(f1)][a] += 1
        super().observe(o, a, r, o2, done, info)

    def act(self, o):
        f = view_features31(o)
        self._last_view = o["view"]
        # survival preemption: imminent starvation overrides any active goal
        # (v2.1 fix: goal arbitration previously let a long-deadline goal starve
        #  the agent - seed 3 death spiral, recorded in RESULTS.md)
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # scent gradient: rare events (tree/key) are only reachable through the
        # long-range scent; every agent arm gets the same signal
        scent = o.get("scent") or {}
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        goal = self.goals.get(self.active_goal) if self.active_goal else None
        if goal is None:
            return self._default_act(f, o, scent)
        a = self._plan(goal, f, o, scent)
        return a if a else self._default_act(f, o, scent)
        # survival competence (kept: the variable is the generator, not death)
        if f["energy_low"] and f["berry_near"] > 0 \
                and "eat" in o.get("afford", ()):
            return "eat"
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        if f["tree_near"] > 0:
            if "eat" in o.get("afford", ()):
                return "eat"
            return "grasp"
        scent = o.get("scent") or {}
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        # learning-progress policy: prefer the least-tried action HERE,
        # tie-broken toward the one that historically led to unseen ctx'
        ctx = self._ctx_key(f)
        counts = self.trans_counts[ctx]
        untried = [a for a in ACTIONS if counts[a] == 0]
        if untried:
            return self.rng.choice(untried)
        # all tried: go where novelty is still available -- follow the
        # scent of the rarest object (tree/key/bell) if any, else the
        # least-tried action
        s = self._scent_step(scent, "bell") \
            or self._scent_step(scent, "tree") \
            or self._scent_step(scent, "key")
        if s:
            return s
        return min(ACTIONS, key=lambda a: counts[a])
