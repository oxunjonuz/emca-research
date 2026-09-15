"""EMCA v3.3 agents -- the SCARCITY + CHAIN-CURIOSITY turn
(turn 102, op_6181258f9eae).

Identifier lineage UNTOUCHED (v2.1 pooled / v2.2 spec / v2.5c
stratified-RR / assoc-only -- imported as-is). Two deltas:

DELTA A -- SCARCITY COMPETENCE for every planner arm (task 1).
  The v3.3 world prices mistakes: empty grasp 0.6/1.8 (calm/storm),
  altar waits 1.0, fury -3.0, tree 18 capped 60/storm, berries 2/1.
  The v3.2 goal layer bleeds under these prices; three gates:
    1. chime-chase: energy >= 60 (was 45) -- a far-zone chime walk in
       a storm costs ~34 energy for +0.5 reward: pure loss in scarcity.
    2. altar waits: energy >= 40 -- each wait burns a 1.0 offering.
    3. bare-tree competence: info['tree_bare'] (the 60-fruit cap)
       stops tree grasps until the next tree appears. A competence,
       not an identifier change -- every arm gets it.

DELTA B -- AgentCuriousChain (task 2): the chain WITHOUT a planner.
  The owner's ask: connect curious_surv with multi-step chains so a
  purely exploratory agent learns to solve logical quests without a
  hard goal planner. Design (NO goal machinery: no goals, no
  deadlines, no self_model, no plan -- object-directed novelty only):
    * OBJECT-DIRECTED NOVELTY: the pull toward an object interaction
      scales with its RARITY (how rarely the agent has done it), not
      with any utility. Lever press, key pickup, treasure-scent dash,
      chime pickup are interaction tokens with counts; the agent is
      drawn to the rarest interaction available in view/scent.
    * THE DASH: the one piece curious_surv lacked (measured: it
      pressed levers 15-27x and picked keys 14-42x per life but never
      ran for the treasure). When the env emits the 'treasure' scent
      (active ONLY with key in hand + door open), following it IS
      novelty-seeking (the agent has almost never stood on the
      treasure cell) -- no plan, just the rarest gradient in view.
    * The chain emerges from the world's own gates: press lever
      (rare interaction) -> door opens -> key in cold (rare object)
      -> pickup -> 12-step window with the treasure scent live.
      The ORDER gate (key after door) is not planned either: the
      roaming produces many lever/key encounters per life; when the
      order aligns, the dash converts it.
  Contrast isolation: AgentCuriousChain vs AgentCuriousSurvivorV33
  share ALL survival competences (foraging, storm tree, energy gates);
  the only difference is the object-directed novelty layer. And
  AgentCuriousSurvivorV33 vs the v3.2 curious_surv isolates scarcity.

Identifier for every curious arm: v2.5c, untouched.
"""
import math
import random
from collections import defaultdict

from agent_emca_v2 import EMCA, view_features
from agent_emca_v31 import view_features31, CHIME
from sanity_stratified3 import AgentV25c
from env_terrarium_v2 import (
    ACTIONS, BERRY, DOOR, LEVER, TREASURE, EMPTY, WALL,
    BELL_GLOW, BELL_DARK, TREE, KEY,
)
from agent_emca_v32 import (
    V32Mixin, AgentV32, AgentV32Pooled, AgentV32Spec, AgentV32Assoc,
    AgentV32Prober, AgentCuriousPure, AgentCuriousSurvivor,
    CuriosityCore, view_features32, env_like_storm, fisher_exact_2x2,
)
from env_terrarium_v32 import ALTAR_POS, PATCH_POS

ALTAR_TILE = "A"
TREASURE_POS = (6, 5)          # from the v3 MAP (the chain's end cell)


def view_features33(obs):
    return view_features32(obs)


class V33Mixin(V32Mixin):
    """v3.2 goal/planning layer + scarcity competence. Identifier
    untouched. The three gates are priced by the v3.3 world."""

    CHIME_GATE_ENERGY = 60      # was 45 in v3.2 (a chime pays 0.5)
    ALTAR_GATE_ENERGY = 40      # each altar wait burns a 1.0 offering

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.tree_bare = False        # competence state, not identifier

    # ---- observe: track the bare-tree signal (the 60-fruit cap) ----
    def observe(self, o, a, r, o2, done, info):
        if info.get("tree_bare"):
            self.tree_bare = True
        if info.get("tree_appeared"):
            self.tree_bare = False     # a new tree is a new budget
        # v3.3 harness defect caught by the matrix death-trace: the
        # storm tree spawn does NOT emit 'tree_appeared' (only calm
        # rare trees do), so after the first storm hit its 60-fruit
        # cap, tree_bare stayed True forever -- the agent refused to
        # grasp ANY later storm tree and starved beside food (36% of
        # storm steps lived with a stuck bare flag; deaths 45-69).
        # Fix: a NEW tree object (different position or a fresh storm)
        # resets the flag. The env's storm spawn sets self.tree without
        # info -- the agent detects the reset by position change.
        t2 = o2.get("view", "")
        if self.tree_bare and "F" in t2:
            # a tree is visible again: is it the SAME tree? The view
            # alone cannot tell position -- but the bare tree stops
            # giving fruit while visible trees keep appearing; the
            # conservative reset: bare only persists while NO tree is
            # in view (the agent left the bare tree behind).
            self.tree_bare = False
        super().observe(o, a, r, o2, done, info)

    # ---- the tree competence, bare-aware (shared by plan and default) ----
    def _tree_competence(self, f, o):
        if f["tree_near"] > 0 and not self.tree_bare:
            if "eat" in o.get("afford", ()):
                return "eat"
            if self._tree_at_dist1():
                return "grasp"
            return self._toward(TREE)
        return None

    # ---- acting: the scarcity gates ----
    def _plan(self, goal, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        target = goal["target"]
        # gate 2: the altar experiment must be affordable
        if target == "patch_berry" and o["energy"] < self.ALTAR_GATE_ENERGY:
            if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                return "eat"
            return self._toward(BERRY)
        # gate 1: chime-chase under scarcity (a chime pays 0.5; the
        # walk costs ~34 energy in a storm)
        if target == "ring_collected" and o["energy"] < self.CHIME_GATE_ENERGY:
            if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                return "eat"
            return self._toward(BERRY)
        # tree competence with the bare gate (overrides the v3.2 inline
        # version: a bare tree must not be grasped at 1.8/grasp)
        tc = self._tree_competence(f, o)
        if tc is not None and f["tree_near"] > 0:
            return tc
        return super()._plan(goal, f, o, scent)

    # ---- default acting: bare-aware + gated chime ----
    def _default_act(self, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        tc = self._tree_competence(f, o)
        if tc is not None:
            return tc
        if f["chime_near"] > 0 and o["energy"] >= self.CHIME_GATE_ENERGY:
            return self._toward(CHIME)
        if f["key_near"] > 0:
            return self._toward(KEY)
        s = self._scent_step(scent, "altar") \
            or self._scent_step(scent, "key") \
            or self._scent_step(scent, "tree") \
            or self._scent_step(scent, "bell")
        if s:
            return s
        if f["energy_low"]:
            return self._toward(BELL_GLOW) if f["bell_glow_near"] \
                else self.rng.choice(["up", "down", "left", "right"])
        return self.rng.choice(["up", "down", "left", "right"])


class AgentV33(V33Mixin, AgentV32):
    IDENTIFIER_VERSION = "v2.5c-stratified-RR-doorgonefix + v3.3 scarcity goals"


class AgentV33Pooled(V33Mixin, AgentV32Pooled):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.identifier_version = "v2.1-pooled + v3.3 scarcity goals"


class AgentV33Spec(V33Mixin, AgentV32Spec):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.identifier_version = "v2.2-spec + v3.3 scarcity goals"


class AgentV33Assoc(V33Mixin, AgentV32Assoc):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.identifier_version = "assoc-only + v3.3 scarcity goals"


class AgentV33Prober(V33Mixin, AgentV32Prober):
    """The prober under scarcity: the offering prices every trial.
    Probe machinery inherited untouched; the scarcity gate keeps it
    from experimenting itself to death (no altar waits under energy
    40 -- the offering burns 1.0/wait)."""
    IDENTIFIER_VERSION = "v2.5c + v3.3 goals + do-interventions (offering-priced)"

    def act(self, o):
        f = view_features33(o)
        self._last_view = o["view"]
        # survival preemption always wins (even mid-probe)
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # scarcity gate: no probing while poor -- the offering burns
        if self.probe_state is not None and o["energy"] < self.ALTAR_GATE_ENERGY:
            if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                return "eat"
            s = self._scent_step(o.get("scent") or {}, "tree") \
                or self._scent_step(o.get("scent") or {}, "altar")
            if s:
                return s
            return self._toward(BERRY)
        return super().act(o)


# ---------------------------------------------------------------------------
# Task 2: the chain WITHOUT a planner -- object-directed novelty
# ---------------------------------------------------------------------------
class AgentCuriousChain(CuriosityCore, AgentV25c):
    """The chain arm. NO goal machinery runs (no goals are generated,
    no plan is consulted): the policy is survival competence (shared
    with curious_surv) + object-directed novelty:

      * interaction_counts: how often the agent has done each object
        interaction (lever press, key pickup, chime pickup, treasure
        visit). The PULL toward an available interaction scales with
        1/(1+count) -- pure rarity, no utility.
      * THE DASH: scent['treasure'] exists ONLY with key in hand and
        the door open (the env's own gate). Following it is novelty
        (the treasure cell is the least-visited cell in the agent's
        life). Priority: survival preemption > dash > rarest
        interaction > roaming novelty.
      * The order gate (key after door) is NOT planned: roaming yields
        15-27 lever presses and 14-42 key pickups per life (measured,
        turn 101); when the order aligns inside the 300-step door
        window, the dash converts it into a treasure.

    Identifier: v2.5c, untouched (the passive layer still rejects the
    decoy; the arm never consults edges -- curiosity has no planner).
    """
    IDENTIFIER_VERSION = "v2.5c + object-directed novelty (chain, v3.3)"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.trans_counts = defaultdict(lambda: defaultdict(int))
        self.identifier_version = self.IDENTIFIER_VERSION
        self.interaction_counts = defaultdict(int)
        self.chain_events = defaultdict(int)
        self.tree_bare = False
        self._had_key_last = False

    # ---- observe: count interactions, track chain events ----
    def observe(self, o, a, r, o2, done, info):
        f1 = view_features33(o)
        self.trans_counts[self._ctx_key(f1)][a] += 1
        if info.get("lever"):
            self.interaction_counts["lever_press"] += 1
            self.chain_events["lever_press"] += 1
        if info.get("key"):
            self.interaction_counts["key_pickup"] += 1
            self.chain_events["key_pickup"] += 1
        if info.get("chime"):
            self.interaction_counts["chime_pickup"] += 1
        if info.get("treasure"):
            self.interaction_counts["treasure_visit"] += 1
            self.chain_events["treasure"] += 1
        if o.get("scent", {}).get("treasure"):
            self.chain_events["dash_steps"] += 1
        # bare-tree competence (shared with every v3.3 arm)
        if info.get("tree_bare"):
            self.tree_bare = True
        if info.get("tree_appeared"):
            self.tree_bare = False
        super().observe(o, a, r, o2, done, info)

    # ---- the rarity pull ----
    def _pull(self, kind):
        return 1.0 / (1.0 + self.interaction_counts[kind])

    def act(self, o):
        f = view_features33(o)
        self._last_view = o["view"]
        scent = o.get("scent") or {}
        # 1. survival preemption (shared with curious_surv)
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # 2. THE DASH: the treasure scent is live ONLY with key+door
        #    (the env's own gate). It is the rarest gradient in view.
        if scent.get("treasure"):
            s = self._scent_step(scent, "treasure")
            if s:
                return s
        # 3. always-on foraging competence (shared with curious_surv)
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # 4. storm-tree competence, bare-aware (shared)
        if f["tree_near"] > 0 and not self.tree_bare:
            if "eat" in o.get("afford", ()):
                return "eat"
            if self._tree_at_dist1():
                return "grasp"
            return self._toward(TREE)
        # storm routing at low energy (shared with curious_surv v3.2)
        if o["energy"] < 55 and env_like_storm(f, scent):
            s = self._scent_step(scent, "tree")
            if s:
                return s
        # 5. object-directed novelty: the rarest available interaction
        #    (lever press / key pickup). No plan: the object must be
        #    in view or scent, and rarity (not utility) sets priority.
        pulls = []
        if f["lever_near"] > 0:
            pulls.append((self._pull("lever_press"), "lever"))
        if f["key_near"] > 0 or scent.get("key"):
            pulls.append((self._pull("key_pickup"), "key"))
        if f["chime_near"] > 0 and o["energy"] >= 60:
            pulls.append((self._pull("chime_pickup"), "chime"))
        if pulls:
            pulls.sort(reverse=True)
            kind = pulls[0][1]
            if kind == "lever":
                if "press" in o.get("afford", ()):
                    return "press"
                return self._toward(LEVER)
            if kind == "key":
                return self._toward(KEY)
            if kind == "chime":
                return self._toward(CHIME)
        # 6. storm competence (shared): the tree scent in a storm
        if f["bell_glow_near"] > 0 or scent.get("bell"):
            s = self._scent_step(scent, "tree")
            if s:
                return s
        # 7. roaming novelty (the v3.2 policy -- unchanged)
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        return self._novelty_act(f, o, scent)


class AgentCuriousSurvivorV33(CuriosityCore, AgentV25c):
    """The v3.2 synthesis under scarcity (the dominance test): same
    reachable novelty policy, same survival arbiter, plus the v3.3
    competences (bare-tree gate; chase gate at 60). The contrast vs
    AgentCuriousChain isolates the object-directed layer; the contrast
    vs the v3.2 curious_surv isolates scarcity."""
    IDENTIFIER_VERSION = "v2.5c + novelty + survival-arbiter (v3.3 scarcity)"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.trans_counts = defaultdict(lambda: defaultdict(int))
        self.identifier_version = self.IDENTIFIER_VERSION
        self.tree_bare = False

    def observe(self, o, a, r, o2, done, info):
        f1 = view_features33(o)
        self.trans_counts[self._ctx_key(f1)][a] += 1
        if info.get("tree_bare"):
            self.tree_bare = True
        if info.get("tree_appeared"):
            self.tree_bare = False
        super().observe(o, a, r, o2, done, info)

    def act(self, o):
        f = view_features33(o)
        self._last_view = o["view"]
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # tree competence, bare-aware (the 60-fruit cap)
        if f["tree_near"] > 0 and not self.tree_bare:
            if "eat" in o.get("afford", ()):
                return "eat"
            if self._tree_at_dist1():
                return "grasp"
            return self._toward(TREE)
        scent = o.get("scent") or {}
        if f["bell_glow_near"] > 0 or scent.get("bell"):
            s = self._scent_step(scent, "tree")
            if s:
                return s
        if o["energy"] < 55 and env_like_storm(f, scent):
            s = self._scent_step(scent, "tree")
            if s:
                return s
        if f["chime_near"] > 0 and o["energy"] >= 60:
            return self._toward(CHIME)
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        return self._novelty_act(f, o, scent)


class AgentCuriousPureV33(CuriosityCore, AgentV25c):
    """Pure novelty under scarcity (the honest ablation)."""
    IDENTIFIER_VERSION = "v2.5c + PURE-novelty (v3.3 scarcity)"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.trans_counts = defaultdict(lambda: defaultdict(int))
        self.identifier_version = self.IDENTIFIER_VERSION
        self.tree_bare = False

    def observe(self, o, a, r, o2, done, info):
        f1 = view_features33(o)
        self.trans_counts[self._ctx_key(f1)][a] += 1
        if info.get("tree_bare"):
            self.tree_bare = True
        if info.get("tree_appeared"):
            self.tree_bare = False
        super().observe(o, a, r, o2, done, info)

    def act(self, o):
        f = view_features33(o)
        self._last_view = o["view"]
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        scent = o.get("scent") or {}
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        return self._novelty_act(f, o, scent)
