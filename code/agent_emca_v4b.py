"""EMCA v4 curiosity arms (continuation of agent_emca_v4.py; kept in
a second module to leave the planner lineage import-light)."""
from collections import defaultdict

from agent_emca_v33 import CuriosityCore, AgentCuriousChain as _ChainBase
from agent_emca_v4 import (
    AgentV4, V4Mixin, V4BelieverMixin, view_features4,
    V4RejectorMixin, AgentV4Pooled, AgentV4Spec, AgentV4Assoc,
)
from sanity_stratified3 import AgentV25c
from env_terrarium_v2 import ACTIONS, BERRY, TREE, KEY, LEVER, BELL_GLOW
from agent_emca_v31 import CHIME
from env_terrarium_v4 import BRAZIER_TILE, TREASURY_TILE as TREASURY_TILE4


class AgentV4Curious(CuriosityCore, AgentV4):
    """Object-directed novelty in the v4 world: the brazier pulse is a
    novelty-rich interaction (the torches stack changes the pocket's
    rhythm; 'X' in view is a rare tile for a forager). The pull toward
    the rarest available interaction -- lever, key, torch pocket --
    is exactly what the scorch prices. Survival competences shared
    with every v4 arm; identifier v2.5c (decoy rejected)."""
    IDENTIFIER_VERSION = "v2.5c + object-directed novelty (v4, bitter)"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.trans_counts = defaultdict(lambda: defaultdict(int))
        self.interaction_counts = defaultdict(int)
        self.chain_events = defaultdict(int)
        self.tree_bare = False
        self._had_key_last = False

    def observe(self, o, a, r, o2, done, info):
        f1 = view_features4(o)
        self.trans_counts[self._ctx_key(f1)][a] += 1
        if info.get("lever"):
            self.interaction_counts["lever_press"] += 1
            self.chain_events["lever_press"] += 1
        if info.get("key"):
            self.interaction_counts["key_pickup"] += 1
            self.chain_events["key_pickup"] += 1
        if info.get("chime"):
            self.interaction_counts["chime_pickup"] += 1
        if info.get("torch_collect"):
            self.interaction_counts["torch_collect"] += 1
            self.chain_events["torch_collect"] += 1
        if info.get("treasure"):
            self.interaction_counts["treasure_visit"] += 1
            self.chain_events["treasure"] += 1
        if info.get("tree_bare"):
            self.tree_bare = True
        if info.get("tree_appeared"):
            self.tree_bare = False
        super().observe(o, a, r, o2, done, info)

    def _pull(self, kind):
        return 1.0 / (1.0 + self.interaction_counts[kind])

    def act(self, o):
        f = view_features4(o)
        self._last_view = o["view"]
        scent = o.get("scent") or {}
        # 1. survival preemption
        if f["energy_low"] and f["berry_near"] > 0 \
                and "eat" in o.get("afford", ()):
            return "eat"
        # 2. treasury food whenever affordable (competence, not novelty)
        if "eat" in o.get("afford", ()) and f.get("treasury_near", 0) > 0 \
                and o["energy"] < 100:
            return "eat"
        # 3. the treasure dash (chain, shared with v3.3)
        if scent.get("treasure"):
            s = self._scent_step(scent, "treasure")
            if s:
                return s
        # 4. foraging competence
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        if f["tree_near"] > 0 and not self.tree_bare:
            if "eat" in o.get("afford", ()):
                return "eat"
            if self._tree_at_dist1():
                return "grasp"
            return self._toward(TREE)
        # 5. object-directed novelty: the rarest available interaction.
        #    The torch pocket is one of them (rarity pull) -- curiosity
        #    walks into the scorch on its OWN generator.
        pulls = []
        if f["lever_near"] > 0:
            pulls.append((self._pull("lever_press"), "lever"))
        if f["key_near"] > 0 or scent.get("key"):
            pulls.append((self._pull("key_pickup"), "key"))
        if f["chime_near"] > 0 and o["energy"] >= 60:
            pulls.append((self._pull("chime_pickup"), "chime"))
        if f.get("torch_near", 0) > 0 and o["energy"] >= 45:
            pulls.append((self._pull("torch_collect") * 1.5, "torch"))
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
            if kind == "torch":
                if self._last_view and self._last_view[4] == BRAZIER_TILE:
                    return "wait"
                return self._toward(BRAZIER_TILE)
        # 6. storm competence
        if f["bell_glow_near"] > 0 or scent.get("bell"):
            s = self._scent_step(scent, "tree")
            if s:
                return s
        # 7. roaming novelty
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        return self._novelty_act(f, o, scent)


class AgentV4CuriousPure(CuriosityCore, AgentV4):
    """Pure novelty under the v4 world (the honest ablation: no
    object-directed pulls, no gates -- the directive's 'curiosity in
    vain' measured directly)."""
    IDENTIFIER_VERSION = "v2.5c + PURE-novelty (v4)"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.trans_counts = defaultdict(lambda: defaultdict(int))
        self.tree_bare = False

    def observe(self, o, a, r, o2, done, info):
        f1 = view_features4(o)
        self.trans_counts[self._ctx_key(f1)][a] += 1
        if info.get("tree_bare"):
            self.tree_bare = True
        if info.get("tree_appeared"):
            self.tree_bare = False
        super().observe(o, a, r, o2, done, info)

    def act(self, o):
        f = view_features4(o)
        self._last_view = o["view"]
        if f["energy_low"] and f["berry_near"] > 0 \
                and "eat" in o.get("afford", ()):
            return "eat"
        if "eat" in o.get("afford", ()) and f.get("treasury_near", 0) > 0 \
                and o["energy"] < 100:
            return "eat"
        scent = o.get("scent") or {}
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        return self._novelty_act(f, o, scent)
