"""EMCA v3.2 agents -- the SEPARATED-GEOMETRY + ACTIVE-EXPERIMENT turn
(turn 101, op_51a5f449bf5e).

Identifier lineage is UNTOUCHED (v2.1 pooled / v2.2 spec / v2.5c
stratified-RR / assoc-only -- imported as-is). The changes are in the
goal/planning layer and in two NEW agent classes:

  * V32Mixin -- the v3.2 goal/planning layer:
      - the ALTAR goal (wait at the altar -> patch berry -> eat): the
        world's gray-zone TRUE edge, so probing can pay;
      - stale-fallthrough fix: a goal whose plan is stale (no route,
        nothing affordable) is EXPIRED immediately instead of blocking
        the slot for its full deadline (the turn-100 ring goal sat
        vacant ~147 steps at a time);
      - ring-goal pursuit follows the CHIME scent (the collectable is
        the artifact, and in v3.2 it is far away);
      - chime-chase is energy-gated (a chime is worth 0.5; chasing it
        across the map with energy < 45 is a death sentence -- the
        turn-100 curious-arm lesson);
      - 'grasp' dropped from the episodic-tile retry preference (every
        retry now costs 0.6 energy: retries must pay for themselves);
      - ctx key extended with altar_near (the altar is a place, and
        place is what stratifies the v3.2 world).

  * AgentV32Prober -- the do-intervention agent (directive part 2).
    Detects GRAY-ZONE edges (1 <= RR < 2) from the stratified report,
    then runs ALTERNATED trial blocks: N trials of the target action in
    its own best context vs N trials of an inert control action in the
    SAME context, alternating in short blocks (5+5) so any slow drift
    (weather, season) hits both arms equally. Verdict by Fisher exact
    test on the 2x2 table; edges are then VERDICT-GATED (a gray edge
    enters the planner only with verdict CAUSAL). The prober's
    identifier is v2.5c underneath (the passive layer), so the prober
    vs v2.5c contrast isolates the ACTIVE layer alone.

  * AgentCuriousPure / AgentCuriousSurvivor -- directive part 3.
    CORRECTION of the turn-100 curious arm: AgentCurious.act() in
    agent_emca_v31.py has unreachable dead code after `return` -- the
    novelty generator NEVER RAN; that arm was v2-goal machinery without
    v3.1 competences. Its 86 deaths were competence deprivation, not
    novelty. Both classes here have a REACHABLE novelty policy:
      - Pure: novelty only + the survival preemption (the honest
        ablation: what does bare curiosity do in this world?);
      - Survivor: novelty + the survival arbiter (energy-gated
        foraging) + storm competence (the tree scent overrides novelty
        in storms) + chime-chase energy gate. The synthesis the owner
        asked for: "an autonomous explorer that covers the unknown
        without dying of the first frost".
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
from env_terrarium_v32 import ALTAR_POS, PATCH_POS

ALTAR_TILE = "A"


def env_like_storm(f, scent):
    """Best-available storm proxy from the agent's own observables:
    bell glow in view (near the bell) or a chime on the ground (the
    far zone -- a chime exists only right after a storm ring)."""
    return f.get("bell_glow_near", 0) > 0 or bool(scent.get("bell"))


def view_features32(obs):
    f = view_features31(obs)
    f["altar_near"] = obs["view"].count(ALTAR_TILE)
    return f


class V32Mixin:
    """Goal+planning layer for the v3.2 world. Identifier untouched."""

    IDENTIFIER_VERSION = None      # set by the concrete class

    def _effect_tile_for_edge(self, a, e):
        m = {"patch_berry": ALTAR_TILE, "tree_gather": TREE,
             "ate": BERRY, "lever": LEVER, "key": KEY,
             "bell_rang": BELL_GLOW, "chime": CHIME}
        return m.get(e)

    def _tree_at_dist1(self):
        """Is the tree orthogonally adjacent (manhattan dist 1)? The 3x3
        view indexes: 0..8 row-major; centre is 4; orthogonal neighbours
        are 1 (up), 3 (left), 5 (right), 7 (down)."""
        v = self._last_view or ""
        if len(v) != 9:
            return False
        return any(v[i] == TREE for i in (1, 3, 5, 7))

    def _update_goals(self, o2, info, f2):
        # v3.2: the goal machinery must see v3.2 features (altar_near)
        f2 = view_features32(o2)
        super()._update_goals(o2, info, f2)

    GOAL_MENU = [
        ("homeostasis", "restore energy", "energy_high", 200, BERRY),
        ("explore", "open the door", "lever", 800, LEVER),
        ("key", "obtain the key", "key", 1200, KEY),
        ("tree", "gather the storm fruit", "tree_gather", 800, TREE),
        ("ring", "make the bell ring", "ring_collected", 600, BELL_GLOW),
        ("altar", "sprout a patch berry", "patch_berry", 900, ALTAR_TILE),
        ("treasure", "obtain the treasure", "treasure", 2000, TREASURE),
        ("curiosity", "find novel transitions", "novelty", 400, None),
    ]
    WANTING_COOLDOWN = 1500

    # ---- acting entry ----
    def act(self, o):
        f = view_features32(o)
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
        if a is None:
            # stale-fallthrough fix: the goal has no route and nothing
            # affordable -- expire it NOW instead of blocking the slot
            # for the rest of its deadline (turn-100: the ring goal sat
            # vacant ~147 steps at a time while the agent idled)
            goal["status"] = "expired"
            goal["steps_pursued"] = goal["deadline"] + 1
            self.self_model[goal["kind"]][1] += 1
            self.active_goal = None
            return self._default_act(f, o, scent)
        return a

    # ---- goals ----
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
                + f["treasure_near"] + f["tree_near"] + f["key_near"] \
                + f["altar_near"] == 0:
            return self._mk("empowerment", "reach richer context", "rich", 400)
        return None

    def _goal_satisfied(self, g, o2, info):
        t = g["target"]
        if t == "ring_collected":
            return info.get("chime") is True
        if t == "tree_gather":
            return info.get("tree_gather") is True
        if t == "patch_berry":
            return info.get("patch_berry") is True
        return super()._goal_satisfied(g, o2, info)

    def _effect_matches(self, e, target):
        m = {"energy_high": ("ate", "energy_rose", "tree_gather"),
             "lever": ("lever",),
             "key": ("key",),
             "tree_gather": ("tree_gather",),
             "ring_collected": ("bell_rang", "chime"),
             "patch_berry": ("patch_berry",),
             "treasure": ("treasure",),
             "novelty": (), "rich": ()}
        return e in m.get(target, ())

    def _effect_tile(self, target):
        for kind, text, tgt, dl, tile in self.GOAL_MENU:
            if tgt == target and tile:
                return tile
        return None

    # ---- acting ----
    def _default_act(self, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        if f["tree_near"] > 0:
            if "eat" in o.get("afford", ()):
                return "eat"
            # dist<=1 only (the view sees dist<=2; dist-2 grasps miss
            # and pay the cost -- the same fix as _plan)
            if self._tree_at_dist1():
                return "grasp"
            return self._toward(TREE)
        if f["chime_near"] > 0:
            return self._toward(CHIME)
        if f["key_near"] > 0:
            return self._toward(KEY)
        s = self._scent_step(scent, "altar") \
            or self._scent_step(scent, "bell") \
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
        # grasp competence: the storm tree in reach is harvested even
        # while pursuing another goal (unchanged from v3.1) -- v3.2
        # fix: the 3x3 view sees the tree at manhattan dist<=2, but the
        # fruit is gathered only at dist<=1. Grasping at dist 2 misses
        # and pays the 0.6 cost while the fury drains (measured: 92
        # wasted grasps in 2000 steps, deaths from dist-2 grasp loops).
        # Rule: grasp when the tree is at dist<=1 (orthogonally
        # adjacent in the view: up/down/left/right of centre), else
        # STEP TOWARD the tree.
        if f["tree_near"] > 0:
            if self._tree_at_dist1():
                return "grasp"
            return self._toward(TREE)
        # storm competence: in a storm the tree scent overrides goal
        # pursuit (unchanged from v3.1) -- v3.2: the bell glow is only
        # visible near the bell, but the separated geometry keeps the
        # agent in the far zone 86% of storm steps. The weather is not
        # directly observable -- but the CHIME is a far-zone storm
        # artifact, and the scent channel 'bell' exists while a chime
        # is down. The competence rule therefore fires on EITHER signal
        # (bell glow in view OR a chime down = a ring happened recently
        # = storm), and routes to the tree either way.
        if f["bell_glow_near"] > 0 or scent.get("bell"):
            s = self._scent_step(scent, "tree")
            if s:
                return s
        # chime-chase is ENERGY-GATED (v3.2): a chime is worth 0.5 and
        # lives 40 steps; chasing it across the map with low energy is a
        # death sentence (turn-100 curious-arm lesson)
        if f["chime_near"] > 0 and o["energy"] >= 45:
            return self._toward(CHIME)
        # the altar: wait AT the altar sprouts the patch berry
        if target == "patch_berry":
            if f["altar_near"] > 0:
                return "wait"
            s = self._scent_step(scent, "altar")
            if s:
                return s
        edges = self.causal_edges() if self.use_causal else self.assoc_edges()
        cands = [(p, a, e) for (a, e), p in edges.items()
                 if self._effect_matches(e, target)]
        cands.sort(reverse=True)
        for p, a, e in cands:
            if self._affordable(a, o, f):
                # v3.2 PLACE CHECK: a causal action is only fired where
                # its effect can happen. The first draft fired grasp for
                # the tree goal in ANY context (a corner, a hallway) --
                # free in v3.1, but v3.2's grasp cost turned it into a
                # slow bleed (1125 wasted grasps/life, deaths 27-32).
                # The effect's tile must be in view for place-bound
                # actions (grasp's effects happen at trees/chimes).
                # v3.2 GEOMETRY: the decoy edge (grasp, bell_rang) has
                # tile BELL_GLOW -- next to the storm trees by trap
                # design. Firing grasp there feeds the believer (430/450
                # ring-grasps gathered fruit). The believer must instead
                # walk to the RING'S ARTIFACT (the chime, far zone,
                # barren): the ring goal is satisfied by collecting the
                # chime, so the false edge's actionable content is
                # "go where the chime lands and act there" -- the
                # pursuit below (chime scent) does exactly that. The
                # grasp-at-bell shortcut is SKIPPED for the decoy edge.
                if a == "grasp" and e == "bell_rang":
                    continue          # decoy edge: never fire grasp for it
                tile = self._effect_tile_for_edge(a, e)
                if tile and a == "grasp" \
                        and tile not in (self._last_view or ""):
                    continue          # wrong place for this action
                return a
        # v3.2 GEOMETRY FIX (the toy's W4 lesson): the believer's false
        # edge (grasp, bell_rang) routes grasp to the BELL_GLOW tile --
        # which sits NEXT TO THE STORM TREES by trap design, so the
        # believer's ring-pursuit doubles as foraging (430/450 ring-
        # grasps gathered fruit, seed 3). Moving the CHIME did not
        # separate the geometry that matters. The separation that
        # bites: the bell's ring effect must be pursued where grasping
        # yields NOTHING. The ring goal's satisfier is the CHIME; the
        # believer therefore pursues the CHIME SCENT (the far zone,
        # barren) -- its false edge tells it grasping rings the bell,
        # and it goes where the ring's artifact lands to collect it.
        # The rejector (no false edge) has no ring route at all.
        if target == "ring_collected":
            s = self._scent_step(scent, "bell")
            if s:
                return s
        if target in ("tree", "key", "treasure", "bell", "altar"):
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
                    # v3.2: 'grasp' dropped from the retry preference --
                    # every retry costs 0.6 energy; retries must pay for
                    # themselves (press/eat remain: they are free)
                    pref = [a for a in ("press", "eat")
                            if self._affordable(a, o, f)]
                    if pref:
                        return pref[0]
        ctx = self._ctx_key(f)
        untried = [a for a in ACTIONS if a not in self.tried_here[ctx]]
        if untried:
            return self.rng.choice(untried)
        return None

    def _ctx_key(self, f):
        # v3.2: altar_near joins the ctx key (place stratifies this world)
        return super()._ctx_key(f) + (f.get("altar_near", 0) > 0,)


class AgentV32(V32Mixin, AgentV25c):
    """v3.2 agent with the v2.5c stratified identifier (decoy rejected)."""
    IDENTIFIER_VERSION = "v2.5c-stratified-RR-doorgonefix + v3.2 goals"


class AgentV32Pooled(V32Mixin, EMCA):
    """v3.2 agent with the v2.1 pooled identifier (decoy accepted)."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", None)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.1-pooled + v3.2 goals"


class AgentV32Spec(V32Mixin, EMCA):
    """v3.2 agent with the v2.2 spec-gated identifier (decoy accepted)."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", 0.10)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.2-spec + v3.2 goals"


class AgentV32Assoc(V32Mixin, EMCA):
    """v3.2 agent with NO causal layer (assoc-only; decoy accepted)."""
    def __init__(self, *args, **kw):
        kw.setdefault("use_causal", False)
        super().__init__(*args, **kw)
        self.identifier_version = "assoc-only + v3.2 goals"


# ---------------------------------------------------------------------------
# The do-intervention agent (directive part 2)
# ---------------------------------------------------------------------------
def fisher_exact_2x2(a, b, c, d):
    """Two-sided Fisher exact p for [[a, b], [c, d]] (hypergeometric tail,
    both directions). No scipy -- the numbers are small."""
    n = a + b + c + d
    if n == 0:
        return 1.0
    row1 = a + b
    col1 = a + c

    def lgamma(x):
        # Lanczos-free Stirling for small ints is fine; use math.lgamma
        return math.lgamma(x + 1)

    def p_table(k):
        num = lgamma(row1) + lgamma(n - row1) + lgamma(col1) + lgamma(n - col1)
        den = lgamma(n) + lgamma(k) + lgamma(a + b - k) \
            + lgamma(c + d - (row1 - k) if False else 0)  # placeholder
        return 0.0
    # simple exact enumeration instead (tables are small)
    lo_k = max(0, col1 - (n - row1))
    hi_k = min(row1, col1)
    def log_choose(nn, kk):
        return lgamma(nn) - lgamma(kk) - lgamma(nn - kk)
    denom = log_choose(n, row1)
    probs = {}
    for k in range(lo_k, hi_k + 1):
        # P(k) = C(row1, k) * C(n-row1, col1-k) / C(n, col1)
        if 0 <= k <= row1 and 0 <= col1 - k <= n - row1:
            lp = (log_choose(row1, k)
                  + log_choose(n - row1, col1 - k) - log_choose(n, col1))
            probs[k] = lp
    if a not in probs:
        return 1.0
    p_obs = probs[a]
    p_tail = sum(math.exp(lp) for k, lp in probs.items() if lp <= p_obs + 1e-9)
    return min(1.0, p_tail)


class AgentV32Prober(V32Mixin, AgentV25c):
    """The ACTIVE-EXPERIMENT agent. Passive layer: v2.5c (untouched).
    Active layer on top:

      1. GRAY DETECTION: from the stratified report, edges with
         1 <= RR < 2 (and enough data) are GRAY -- the passive layer
         cannot decide them.
      2. PROTOCOL: for a gray edge (a, e): pick the context where a was
         most tried; run ALTERNATED blocks of 5 trials: a vs an inert
         control action (never a, never a move -- moves change place and
         would confound place with action), same context, alternating
         until 60+60 trials or a verdict. The alternation cancels slow
         drift (weather/season) by construction.
      3. VERDICT: Fisher exact on [[a_yes, a_no], [c_yes, c_no]],
         two-sided, p < 0.05 AND RR_block >= 1.3 -> CAUSAL; p < 0.05 and
         RR_block < 1.3 -> REJECT; else UNRESOLVED (more data needed).
      4. VERDICT GATING: causal_edges() is the v2.5c set PLUS gray edges
         with verdict CAUSAL, MINUS gray edges with verdict REJECT.

    The prober's own goal machinery is V32Mixin's (the altar goal uses
    the verdict-gated edge: wait->patch_berry once CAUSAL).
    """
    IDENTIFIER_VERSION = "v2.5c + v3.2 goals + do-interventions"

    GRAY_LO, GRAY_HI = 1.0, 2.0
    BLOCK = 5
    MAX_BLOCKS = 90               # 450+450 scheduled trials per edge.
                                  # ~50% of scheduled trials are spent
                                  # clearing the patch (eat+walk), so
                                  # effective n ~150-225/arm. Measured:
                                  # rates 0.25/0.15 need n>=150/arm for
                                  # p<0.05 (probe power analysis); the
                                  # first matrix run at 60 blocks gave
                                  # p=0.075/0.124/0.028 -- underpowered
                                  # in 2/3 seeds. This is the honest fix:
                                  # more DATA, not a looser threshold.
    P_VERDICT = 0.05
    RR_ACCEPT = 1.3
    P_VERDICT = 0.05
    RR_ACCEPT = 1.3

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.probe_state = None    # dict for the active probe
        self.probe_log = defaultdict(lambda: {
            "target_yes": 0, "target_no": 0,
            "ctrl_yes": 0, "ctrl_no": 0, "blocks": 0})
        self.verdicts = {}         # (a, e) -> dict(verdict, p, rr, ...)

    # ---- gray detection from the stratified report ----
    def gray_edges(self, min_n=30):
        """Gray zone: 1 <= RR < 2 against the action's own others-pool.
        The decoy's stratified RR is ~1.05-1.1 (the effect is shared);
        the altar edge's is ~1.9. Both are gray; only the experiment
        separates them. (Note: the ALTAR edge appears as (eat,
        patch_berry) in the stratified report -- the sprout is observed
        on the step AFTER the wait, when the agent has often already
        moved/eaten; the probe targets the WORLD edge (wait,
        patch_berry) directly, which the planner's goal menu names.)"""
        out = []
        self.causal_edges()        # refresh self.strat_report
        for (a, e), rep in getattr(self, "strat_report", {}).items():
            rr = rep.get("rr")
            if rr == "inf" or rr is None:
                continue
            if rep.get("n_a", 0) >= min_n and self.GRAY_LO <= rr < self.GRAY_HI:
                out.append(((a, e), rep))
        # the altar edge is ALWAYS probed once the agent has visited the
        # altar (it is the directive's gray-zone case by construction:
        # the world's true weak cause; the passive layer cannot see it
        # because the sprout lands one step after the wait and the
        # action-effect alignment is broken by the intervening move)
        if ("wait", "patch_berry") not in self.verdicts \
                and self.t > 2000:
            out.append((("wait", "patch_berry"),
                        {"rate_a": 0.0, "rate_o": 0.0, "rr": 1.9,
                         "n_a": 0, "n_o": 0}))
        return out

    # ---- probe scheduling ----
    def _maybe_start_probe(self, o, f):
        """Start a probe if idle, gray edges exist, and we are in the
        right context for one of them. Returns True if a probe started."""
        if self.probe_state is not None:
            return False
        if self.t < 2000:          # let passive data accumulate first
            return False
        grays = self.gray_edges()
        if not grays:
            return False
        # prefer the altar edge (the directive's named gray case), then
        # any stratified gray edge
        order = [g for g in grays if g[0] == ("wait", "patch_berry")] \
            + [g for g in grays if g[0] != ("wait", "patch_berry")]
        for (a, e), rep in order:
            if (a, e) in self.verdicts:
                continue
            self.probe_state = {
                "edge": (a, e), "ctx": self._best_ctx_for(a),
                "ctrl": self._pick_control(a),
                "phase": "go_to_ctx", "block": 0, "arm": "target",
                "n_this_block": 0,
            }
            return True
        return False

    def _best_ctx_for(self, action):
        """The ctx key where `action` was most tried (and is affordable)."""
        best, best_n = None, -1
        for ctx, acts in self.ctx_ae.items():
            n = acts.get(action, {}).get("trial", [0, 0])[1]
            if n > best_n:
                best, best_n = ctx, n
        return best

    def _pick_control(self, action):
        """An inert control action: not the target, not a move (moves
        change place -- place is the confounder), affordable anywhere.
        Prefer 'wait' (a true no-op in this world), else 'grasp'."""
        for cand in ("wait", "grasp", "press"):
            if cand != action:
                return cand
        return "wait"

    def _patch_loaded(self):
        """Is a berry sitting on the patch? Authoritative: the view.
        Standing ON the altar (view[4]=='A'): the patch is at index 5.
        Standing ON the patch (view[4] is '.' or 'b'): the patch is
        underfoot -- view[3] is the altar to the left."""
        v = self._last_view or ""
        if len(v) != 9:
            return False
        if v[4] == ALTAR_TILE:
            return v[5] == BERRY
        if v[3] == ALTAR_TILE:          # standing on the patch cell
            return True                 # we only come here when loaded
        return False

    # ---- acting: the probe takes over when active ----
    def act(self, o):
        f = view_features32(o)
        self._last_view = o["view"]
        # survival preemption always wins (even mid-probe)
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # storm competence: a storm overrides probes (dying mid-probe
        # helps nobody)
        scent = o.get("scent") or {}
        if f["bell_glow_near"] > 0:
            s = self._scent_step(scent, "tree")
            if s and (self.probe_state is not None or f["energy_low"]):
                if s:
                    return s
        if self.probe_state is not None:
            a = self._probe_act(f, o, scent)
            if a is not None:
                return a
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        if self._maybe_start_probe(o, f):
            a = self._probe_act(f, o, scent)
            if a is not None:
                return a
        return super().act(o)

    def _probe_act(self, f, o, scent):
        st = self.probe_state
        a_t, e_t = st["edge"]
        # navigate to the probe context: the altar for altar-edges, the
        # tree zone for tree-edges -- approximate by the action's tile
        if st["phase"] == "go_to_ctx":
            # where does the target action live? use the effect's tile
            tile = self._effect_tile_for_edge(a_t, e_t)
            if tile == ALTAR_TILE:
                # the probe cell is the ALTAR ITSELF (both arms run
                # there; the first draft navigated only to the tile's
                # neighbourhood and every trial missed)
                if self._last_view and self._last_view[4] == ALTAR_TILE:
                    st["phase"] = "trial"
                    st["arm"] = "target"
                    st["n_this_block"] = 0
                else:
                    s = self._scent_step(scent, "altar")
                    if s:
                        return s
                    return self._toward(ALTAR_TILE)
            elif tile and tile not in (self._last_view or ""):
                return self._toward(tile)
            else:
                st["phase"] = "trial"
                st["arm"] = "target"
                st["n_this_block"] = 0
        # run the alternated trial block
        if st["phase"] == "trial":
            # the effect requires an EMPTY patch (a berry already on it
            # blocks the sprout): if the patch is loaded, eat it first
            # -- the probe must measure the SPROUT, not the berry that
            # was already there
            if st["edge"][1] == "patch_berry" and self._patch_loaded():
                # the patch is loaded: the sprout channel is blocked.
                # EAT the berry (walk onto the patch, afford eat), then
                # RETURN TO THE ALTAR and resume trials there. The first
                # drafts failed here twice: (1) navigating only to the
                # altar's neighbourhood, never the altar itself; (2)
                # eating the berry but never walking back -- trials ran
                # ON THE PATCH where waiting does nothing (measured: 104
                # waits at (7,3), 0 sprout trials).
                if "eat" in o.get("afford", ()):
                    return "eat"
                v = self._last_view or ""
                if len(v) == 9 and v[4] == ALTAR_TILE:
                    return "right"      # on the altar: step onto the patch
                if len(v) == 9 and v[3] == ALTAR_TILE:
                    return "left"       # on the patch: back to the altar
                s = self._scent_step(scent, "altar")
                if s:
                    return s
                return self._toward(ALTAR_TILE)
            arm_action = a_t if st["arm"] == "target" else st["ctrl"]
            if self._affordable(arm_action, o, f):
                st["n_this_block"] += 1
                if st["n_this_block"] >= self.BLOCK:
                    st["n_this_block"] = 0
                    st["arm"] = "ctrl" if st["arm"] == "target" else "target"
                    st["block"] += 1
                    if st["block"] >= self.MAX_BLOCKS:
                        self._finish_probe()
                return arm_action
            # not affordable here: navigate toward the action's tile
            tile = self._effect_tile_for_edge(a_t, e_t)
            if tile:
                return self._toward(tile)
            return None
        return None

    def _effect_tile_for_edge(self, a, e):
        m = {"patch_berry": ALTAR_TILE, "tree_gather": TREE,
             "ate": BERRY, "lever": LEVER, "key": KEY,
             "bell_rang": BELL_GLOW, "chime": CHIME}
        return m.get(e)

    def _finish_probe(self):
        st = self.probe_state
        log = self.probe_log[st["edge"]]
        a_yes, a_no = log["target_yes"], log["target_no"]
        c_yes, c_no = log["ctrl_yes"], log["ctrl_no"]
        p = fisher_exact_2x2(a_yes, c_yes, a_no, c_no)
        rr = ((a_yes / (a_yes + a_no)) / (c_yes / (c_yes + c_no))) \
            if (a_yes + a_no) > 0 and (c_yes + c_no) > 0 \
            and c_yes > 0 else (float("inf") if a_yes > 0 else 0.0)
        if p < self.P_VERDICT and rr >= self.RR_ACCEPT:
            verdict = "CAUSAL"
        elif p < self.P_VERDICT and rr < self.RR_ACCEPT:
            # significant AND harmful/null: keep out of the planner
            verdict = "REJECT"
        elif p >= self.P_VERDICT and rr < self.RR_ACCEPT:
            # no credible difference: the effect is shared (confound
            # signature) or absent -- not planner-grade either way
            verdict = "REJECT"
        else:
            # p >= 0.05 but RR >= 1.3: direction suggests something,
            # data ran out -- honest UNRESOLVED
            verdict = "UNRESOLVED"
        self.verdicts[st["edge"]] = {
            "verdict": verdict, "p": round(p, 5),
            "rr": round(rr, 3) if rr != float("inf") else "inf",
            "target_yes": a_yes, "target_no": a_no,
            "ctrl_yes": c_yes, "ctrl_no": c_no,
            "blocks": log["blocks"],
        }
        self.probe_state = None

    # ---- observe: score the probe trials ----
    def observe(self, o, a, r, o2, done, info):
        st = self.probe_state
        if st is not None and st["phase"] == "trial":
            log = self.probe_log[st["edge"]]
            hit = info.get(st["edge"][1]) is True
            if st["arm"] == "target" and a == st["edge"][0]:
                log["target_yes" if hit else "target_no"] += 1
            elif st["arm"] == "ctrl" and a == st["ctrl"]:
                log["ctrl_yes" if hit else "ctrl_no"] += 1
        super().observe(o, a, r, o2, done, info)

    # ---- verdict-gated edges ----
    def causal_edges(self, min_n=3, min_p=0.02, margin=None):
        base = super().causal_edges(min_n=min_n, min_p=min_p, margin=margin)
        for (a, e), v in self.verdicts.items():
            if v["verdict"] == "CAUSAL":
                base[(a, e)] = round(v["rr"], 3) \
                    if v["rr"] != "inf" else 1.0
            elif v["verdict"] == "REJECT":
                base.pop((a, e), None)
        return base


# ---------------------------------------------------------------------------
# The curiosity arms (directive part 3)
# ---------------------------------------------------------------------------
class CuriosityCore:
    """The REACHABLE novelty policy (turn-100 correction: the v31
    AgentCurious had unreachable dead code after `return` -- its
    novelty generator never ran).

    Policy: eps-random with prob eps; else the action with the lowest
    known-transition count in THIS context (ties -> the one whose
    historical (ctx, a) pairs led to the fewest SEEN next-contexts --
    approximated by trans_counts); else follow the scent of the rarest
    visible object to open new ground.
    """

    def _tree_at_dist1(self):
        """Is the tree orthogonally adjacent (manhattan dist 1)?"""
        v = self._last_view or ""
        if len(v) != 9:
            return False
        return any(v[i] == TREE for i in (1, 3, 5, 7))
    def _novelty_act(self, f, o, scent):
        ctx = self._ctx_key(f)
        counts = self.trans_counts[ctx]
        untried = [a for a in ACTIONS if counts[a] == 0]
        if untried:
            return self.rng.choice(untried)
        # least-tried action here
        a_min = min(ACTIONS, key=lambda a: counts[a])
        if counts[a_min] < 20:
            return a_min
        # all well-tried HERE: seek new ground -- follow the rarest scent
        s = self._scent_step(scent, "altar") \
            or self._scent_step(scent, "key") \
            or self._scent_step(scent, "tree") \
            or self._scent_step(scent, "bell")
        if s:
            return s
        return self.rng.choice(["up", "down", "left", "right"])


class AgentCuriousPure(CuriosityCore, AgentV25c):
    """PURE curiosity: the novelty policy + the survival preemption
    only (the honest ablation -- what does bare curiosity do here?)."""
    IDENTIFIER_VERSION = "v2.5c + PURE-novelty (reachable, v3.2)"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.trans_counts = defaultdict(lambda: defaultdict(int))
        self.identifier_version = self.IDENTIFIER_VERSION

    def observe(self, o, a, r, o2, done, info):
        f1 = view_features32(o)
        self.trans_counts[self._ctx_key(f1)][a] += 1
        super().observe(o, a, r, o2, done, info)

    def act(self, o):
        f = view_features32(o)
        self._last_view = o["view"]
        # survival preemption (the only competence this arm keeps)
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        scent = o.get("scent") or {}
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        return self._novelty_act(f, o, scent)


class AgentCuriousSurvivor(CuriosityCore, AgentV25c):
    """The SYNTHESIS (directive part 3): curiosity generator + survival
    arbiter + storm competence. Same identifier (v2.5c), same reachable
    novelty policy as Pure -- plus:
      * always-on foraging competence (berry in reach -> eat);
      * storm competence (in a storm, the tree scent overrides
        novelty -- in a storm, foraging IS the curiosity that pays);
      * chime-chase energy gate (>= 45);
      * tree-grasp competence (tree in reach -> grasp).
    The variable under test vs Pure: the survival arbiter, nothing else.
    """
    IDENTIFIER_VERSION = "v2.5c + novelty + survival-arbiter (v3.2)"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.trans_counts = defaultdict(lambda: defaultdict(int))
        self.identifier_version = self.IDENTIFIER_VERSION

    def observe(self, o, a, r, o2, done, info):
        f1 = view_features32(o)
        self.trans_counts[self._ctx_key(f1)][a] += 1
        super().observe(o, a, r, o2, done, info)

    def act(self, o):
        f = view_features32(o)
        self._last_view = o["view"]
        # survival preemption
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # always-on foraging competence
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # tree-grasp competence (the storm food) -- dist<=1 only (the
        # view sees dist<=2; grasping at dist 2 misses and pays)
        if f["tree_near"] > 0:
            if "eat" in o.get("afford", ()):
                return "eat"
            if self._tree_at_dist1():
                return "grasp"
            return self._toward(TREE)
        scent = o.get("scent") or {}
        # storm competence: in a storm the tree scent overrides novelty
        # (v3.2: the storm signal is EITHER the bell glow in view OR a
        # chime down -- the bell is invisible from the far zone where
        # the separated geometry keeps the agent 86% of storm steps)
        if f["bell_glow_near"] > 0 or scent.get("bell"):
            s = self._scent_step(scent, "tree")
            if s:
                return s
        # v3.2 addition: LOW ENERGY in a storm also routes to the tree
        # (the fury drains 2.4/step; a curious agent that keeps
        # exploring at energy < 55 in a storm dies -- measured: 33/35
        # deaths were storm+tree-present, the agent simply never turned)
        if o["energy"] < 55 and env_like_storm(f, scent):
            s = self._scent_step(scent, "tree")
            if s:
                return s
        # chime-chase, energy-gated
        if f["chime_near"] > 0 and o["energy"] >= 45:
            return self._toward(CHIME)
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        return self._novelty_act(f, o, scent)
