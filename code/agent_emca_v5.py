"""EMCA v5 agents -- the TRUE-EDGE-VALUE arms (turn 106 directive
op_30a1023467a9 + op_849188424224). One lineage, identical survival
competences (everything the v4 layer provides), identical goal menus
-- the ONLY difference between the arms is WHICH EDGES each identifier
asserts, and the lotus plan routes ONLY through an edge in the agent's
own model.

THE HONEST HARNESS FIX (found by reading the code before writing this
file): the v3.2 ctx-key extension (altar_near) was DEAD CODE in the
filing path -- every observe() since v3.2 filed ctx_ae with the BASE
v2 features, so the extended _ctx_key never ran for the filed data.
For the spring's mask that would be fatal: spring_near MUST be in the
ctx key or the aura is not a context and the stratified contrast
cannot see the within-aura difference. All v5 arms file through ONE
observe (view_features5, spring_near in the ctx key, the v2.5c
door_gone data-fix). The identifiers differ ONLY in their edge rules.

ARM DESIGN:
  AgentV5Pooled  -- v2.1 pooled identifier (spec gate OFF).
  AgentV5Spec    -- v2.2 spec-gated (spec_cap 0.10).
  AgentV5Assoc   -- assoc-only, threshold 0.5 (the campaign's standing
                    assoc layer: structurally blind to the spring --
                    the marginal rate(wait->flow) = 0.65 * w < 0.5).
  AgentV5Assoc02 -- assoc-only, threshold 0.02 (the permissive
                    control: the causal layer's evidence bar -- it CAN
                    possess the spring edge AND every junk
                    co-occurrence above 0.02, decoy included).
  AgentV5        -- v2.5c stratified (the only layer whose contrast is
                    dilution-proof: RR = 0.65/0.25 = 2.6 within the
                    aura context, the wait-share cancels).

LOTUS PLAN (every arm, same code, no world-knowledge fallback): the
goal 'lotus' sits 5th in the menu. The plan's ONLY productive route is
an edge (a, spring_flow)/(a, lotus) in the agent's own model,
place-checked at the spring tile in view (the aura is exactly the set
of cells whose view contains the spring). Navigation to the aura (the
'spring' scent) and in-aura exploration (untried actions -> data for
every arm) are shared world-knowledge of WHERE the spring is -- WHAT
causes the flow is exactly what the identifiers disagree on. Blind
arms expire the goal 3 times (3600 steps of pursuit) and are demoted:
the exploration tax instead of the payoff. The waiting itself is
energy-gated (>= 55): waiting through a storm in the cold zone is
lethal, so the arm forages and returns -- the pool is frozen away
from the aura and holds its water.
"""
import random
from collections import defaultdict

from agent_emca_v2 import EMCA
from agent_emca_v33 import V33Mixin
from agent_emca_v4 import (
    V4Mixin, V4BelieverMixin, V4RejectorMixin, view_features4,
)
from sanity_stratified3 import AgentV25c
from env_terrarium_v2 import ACTIONS, BERRY, LEVER, TREASURE, KEY, TREE, WALL
from agent_emca_v31 import CHIME
from env_terrarium_v4 import BRAZIER_TILE
from env_terrarium_v5 import SPRING_TILE, LOTUS_TILE

ALTAR_TILE = "A"
TREASURY_TILE = "$"
MOVES = ("up", "down", "left", "right")


def view_features5(obs):
    f = dict(view_features4(obs))
    f["spring_near"] = obs["view"].count(SPRING_TILE)
    f["lotus_near"] = obs["view"].count(LOTUS_TILE)
    return f


class V5Filing:
    """ONE filing path for every v5 arm: view_features5 features, the
    spring in the ctx key, the v2.5c door_gone data-fix. Identifier
    classes differ ONLY in their edge rules, never in their data."""

    def observe(self, o, a, r, o2, done, info):
        self.t += 1
        f1, f2 = view_features5(o), view_features5(o2)
        flags = tuple(sorted(k for k in info if info[k] is True))
        ctx = self._ctx_key(f1)
        self.episodes.append((f1, a, r, f2, flags))
        self.working.append((f1, a, r, f2, flags))
        self.novelty_window.append((ctx, a, self._ctx_key(f2)))
        self.tried_here[ctx].add(a)
        trial = self.ctx_ae[ctx][a]
        if "trial" not in trial:
            trial["trial"] = [0, 0]
        trial["trial"][1] += 1
        effects = list(flags)
        if f2["energy_high"] and not f1["energy_high"]:
            effects.append("energy_rose")
        if f2["energy_low"] and not f1["energy_low"]:
            effects.append("energy_fell")
        # v2.5c data-fix: door_gone only for non-move actions
        if a not in MOVES and f1["door_near"] > 0 \
                and f2["door_near"] < f1["door_near"]:
            effects.append("door_gone")
        for e in effects:
            c = self.ctx_ae[ctx][a][e]
            c[1] += 1
            if self._effect_real(e, flags, f1, f2):
                c[0] += 1
                self.effect_ctx[e].add(ctx)
        self.seen_transitions.add((ctx, a, self._ctx_key(f2)))
        self._update_goals(o2, info, f2)
        if self.context_reset_at and self.t == self.context_reset_at:
            self._context_reset()

    def _ctx_key(self, f):
        # base v2 features + the place markers that stratify this world
        # (chime, altar, brazier, treasury, spring). The v3.2
        # altar_near extension never reached the filed data (dead code
        # in the observe path) -- here it is real for every arm.
        return (
            f["berry_near"] > 0, f["door_near"] > 0, f["lever_near"] > 0,
            f["treasure_near"] > 0, f["energy_low"],
            f["bell_glow_near"] > 0, f["bell_dark_near"] > 0,
            f["key_near"] > 0, f["tree_near"] > 0,
            f.get("chime_near", 0) > 0, f.get("altar_near", 0) > 0,
            f.get("torch_near", 0) > 0, f.get("treasury_near", 0) > 0,
            f.get("spring_near", 0) > 0,
        )


class V5Mixin(V5Filing, V4Mixin):
    """The v5 goal/planning layer: the lotus goal, the lotus plan
    (edge-routed, place-checked, energy-gated), the shared in-aura
    data cadence. Identifier untouched (each arm's own)."""

    GOAL_MENU = [
        ("homeostasis", "restore energy", "energy_high", 200, BERRY),
        ("explore", "open the door", "lever", 800, LEVER),
        ("key", "obtain the key", "key", 1200, KEY),
        ("tree", "gather the storm fruit", "tree_gather", 800, TREE),
        ("lotus", "bloom the spring lotus", "lotus_bloom", 1200,
         SPRING_TILE),
        ("ring", "make the bell ring", "ring_collected", 600, None),
        ("altar", "sprout a patch berry", "patch_berry", 900, ALTAR_TILE),
        ("torch", "bank a treasury torch", "torch_bank", 800, BRAZIER_TILE),
        ("treasure", "obtain the treasure", "treasure", 2000, TREASURE),
        ("curiosity", "find novel transitions", "novelty", 400, None),
    ]
    WANTING_COOLDOWN = 1500
    LOTUS_WAIT_ENERGY = 55      # waiting through a storm is lethal below
    _nav_pos = None
    _nav_anchor = None
    _nav_stuck = 0
    _cadence = 0

    def _effect_matches(self, e, target):
        m = {"energy_high": ("ate", "energy_rose", "tree_gather"),
             "lever": ("lever",), "key": ("key",),
             "tree_gather": ("tree_gather",),
             "lotus_bloom": ("spring_flow", "lotus_bloom", "lotus"),
             "ring_collected": ("bell_rang", "chime"),
             "patch_berry": ("patch_berry",),
             "torch_bank": ("torch_lit", "torch_collect", "treasury_ate"),
             "treasure": ("treasure",),
             "novelty": (), "rich": ()}
        return e in m.get(target, ())

    def _effect_tile_for_edge(self, a, e):
        m = {"patch_berry": ALTAR_TILE, "tree_gather": TREE,
             "ate": BERRY, "lever": LEVER, "key": KEY,
             "bell_rang": None, "chime": CHIME,
             "torch_lit": BRAZIER_TILE, "torch_collect": BRAZIER_TILE,
             "treasury_ate": TREASURY_TILE,
             "spring_flow": SPRING_TILE, "lotus_bloom": SPRING_TILE,
             "lotus": SPRING_TILE}
        return m.get(e)

    def _goal_satisfied(self, g, o2, info):
        if g["target"] == "lotus_bloom":
            return info.get("lotus_bloom") is True \
                or info.get("lotus") is True
        return super()._goal_satisfied(g, o2, info)

    # ---- acting entry: v5 features are visible to the planner ----
    def act(self, o):
        f = view_features5(o)
        self._last_view = o["view"]
        if f["energy_low"] and f["berry_near"] > 0 \
                and "eat" in o.get("afford", ()):
            return "eat"
        # a bloomed lotus in view is food for EVERY arm (sight, not
        # knowledge): the goal machinery may be busy elsewhere -- the
        # v4 opportunistic-eating lesson, carried to the lotus. Without
        # this the bloom died unseen while a key goal monopolised the
        # agent (measured: bloom at t=1983, 0 eats in 8000 steps).
        if f.get("lotus_near", 0) > 0 and "eat" in o.get("afford", ()):
            return "eat"
        if f.get("lotus_near", 0) > 0:
            return self._toward(LOTUS_TILE)
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

    # ---- the plan: the lotus routes ONLY through an edge ----
    def _scent_step_smart(self, scent, obj):
        """Scent descent that does not press into walls and does not
        get stuck in greedy dead ends. Measured defects of the plain
        _scent_step on this map: (1) the greedy path to the spring
        crosses the treasure-chamber walls; (2) the altar pocket
        (7,2)-(7,3) has the only distance-reducing direction walled;
        (3) a single random escape draw stayed inside the pocket
        (2891/3603 goal steps trapped, seed 2). The escape: a
        stuck-memory (same 2-cell neighbourhood > 12 steps) that
        climbs OUT deterministically (the free direction with MAX
        scent distance). NAVIGATION-ONLY: the caller uses this outside
        the aura; parking inside the aura is legitimate staying, not
        stuckness (the first escape draft marched parked waiters out
        of the aura and collapsed the cadence, measured: waits 130 ->
        6). A local view-based competence, identical for every arm."""
        g = scent.get(obj)
        if not g:
            return None
        v = self._last_view or ""
        if len(v) != 9:
            return self._scent_step(scent, obj)
        idx = {"up": 1, "down": 7, "left": 3, "right": 5}
        free = {d for d in idx if v[idx[d]] != WALL}
        if not free:
            return None
        # stuck detection by scent-signature oscillation: the original
        # _nav_pos anchor was NEVER updated (dead variable -- the stuck
        # counter fired every 13 steps regardless of motion, measured:
        # column-1 bouncing for 3600 steps). A real signature: the set
        # of distinct scent vectors seen in the last 16 steps. Making
        # progress -> many distinct vectors; oscillating -> few.
        hist = getattr(self, "_sig_hist", None)
        if hist is None:
            from collections import deque
            hist = self._sig_hist = deque(maxlen=16)
        hist.append(tuple(sorted(g.items())))
        dh = getattr(self, "_dir_hist", None)
        if dh is None:
            from collections import deque
            dh = self._dir_hist = deque(maxlen=24)
        # record the direction the caller is about to prefer (the
        # greedy pick) so the escape knows what has been over-used
        if getattr(self, "_escape_left", 0) <= 0:
            pick = None
            # DETERMINISTIC TIES (turn-115 fix): sorted() on equal g
            # values left ties to the key's hash order.
            _order = ("up", "down", "left", "right")
            for d in sorted(g, key=lambda k: (g[k], _order.index(k)
                                              if k in _order else 9)):
                if g[d] < 0 and d in free:
                    pick = d
                    break
            if pick is None and free:
                _order = ("up", "down", "left", "right")
                pick = min(free, key=lambda d: (g[d], _order.index(d)))
            if pick:
                dh.append(pick)
        if getattr(self, "_escape_left", 0) > 0:
            self._escape_left -= 1
            d = self._escape_dir
            if d in free:
                return d
            alt = [x for x in free if g.get(x, 0) >= 0]
            if alt:
                # DETERMINISTIC TIES (turn-115 fix): max over a list built
                # from a SET broke ties by string-hash order.
                _order = ("up", "down", "left", "right")
                self._escape_dir = max(alt, key=lambda x: (g[x],
                                                          -_order.index(x)))
                return self._escape_dir
            self._escape_left = 0
        elif len(hist) == 16 and len(set(hist)) <= 3:
            # oscillating: commit to the free direction taken LEAST in
            # the recent history (the max-distance rule picked corners:
            # from column 1 it chose 'up' into the top wall and died
            # there, measured). Committing to the neglected direction
            # breaks any local loop; greedy descent resumes after.
            from collections import deque as _dq
            dh = getattr(self, "_dir_hist", None)
            if dh is None:
                dh = self._dir_hist = _dq(maxlen=24)
            counts = {d: 0 for d in free}
            for dd in dh:
                if dd in counts:
                    counts[dd] += 1
            # DETERMINISTIC TIES (turn-115 fix, same as the LRU tie):
            # min over a SET-derived dict depended on string-hash order.
            _order = ("up", "down", "left", "right")
            self._escape_dir = min(free, key=lambda d: (counts[d],
                                                        _order.index(d)))
            self._escape_left = 10
            hist.clear()
            dh.append(self._escape_dir)
            return self._escape_dir
        # 1. any wall-free distance-reducing direction; TIES broken by
        # least-recent-use (dict order always picked 'down' at (3,1):
        # down=-1, right=-1 -- and 'down' led into the altar pocket
        # every time, measured: column-1 loop for 3600 steps)
        best_val = min(g[d] for d in free)
        if best_val < 0:
            cand = [d for d in free if g[d] == best_val]
            if len(cand) == 1:
                return cand[0]
            counts = {d: 0 for d in cand}
            for dd in getattr(self, "_dir_hist", ()) or ():
                if dd in counts:
                    counts[dd] += 1
            # DETERMINISTIC TIES (turn-115 fix): min() over a dict built
            # from a SET broke ties by string-hash iteration order -- the
            # campaign's runs silently depended on PYTHONHASHSEED through
            # this line (found because a v6 probe verdict flipped between
            # processes). Ties now break by the fixed direction order.
            order = ("up", "down", "left", "right")
            return min(cand, key=lambda d: (counts[d], order.index(d)))
        # 2. dead end: slide -- the flattest free direction
        best = None
        for d in free:
            if best is None or g[d] < g[best]:
                best = d
        if best is not None:
            # DETERMINISTIC TIES (turn-115 fix): strict less-than over a
            # SET iteration left ties to string-hash order.
            _order = ("up", "down", "left", "right")
            best = min([d for d in free if g[d] == g[best]],
                       key=lambda d: _order.index(d))
        return best

    def _plan(self, goal, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        target = goal["target"]
        if target == "lotus_bloom":
            # 0. a bloomed lotus in view is food -- walk to it and eat
            #    (sight is shared by every arm; knowing WHAT blooms it
            #    is the dispute, not seeing it)
            if f.get("lotus_near", 0) > 0:
                if "eat" in o.get("afford", ()):
                    return "eat"
                return self._toward(LOTUS_TILE)
            # 0b. survival preemption (the wait must not starve the arm)
            if f["energy_low"]:
                if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                    return "eat"
                tc = self._tree_competence(f, o)
                if tc is not None:
                    return tc
                return self._toward(BERRY)
            # 1. the ONLY productive route: an edge in the agent's own
            #    model, place-checked at the spring tile in view (the
            #    aura is exactly the view of the spring)
            if o["energy"] >= self.LOTUS_WAIT_ENERGY:
                a = self._v5_edge_block(target, f, o)
                if a is not None:
                    return a
            # 2. no edge (or too poor to wait): the shared in-aura
            #    cadence -- PARKED. The first draft let the agent dip
            #    in and out (untried actions, then random moves): 3603
            #    goal steps produced 3-18 waits and the stratified
            #    edge never formed (ctx fragmentation starves the
            #    contrast). The cadence now ROTATES the non-move
            #    actions in place (position stays, the ctx stays, the
            #    data accumulates): wait every 4th step, press/eat
            #    between (free actions). Wait share 0.25 -> blended
            #    flow 0.31 < 0.5: the cadence itself can NEVER bloom
            #    the lotus -- only an edge that says WAIT can.
            if f.get("spring_near", 0) > 0:
                # storm competence (the fury kills parked waiters):
                # the chime-on-the-ground signal reaches the far zone
                if f["bell_glow_near"] > 0 or scent.get("bell"):
                    tc = self._tree_competence(f, o)
                    if tc is not None:
                        return tc
                    s = self._scent_step(scent, "tree")
                    if s:
                        return s
                if o["energy"] >= 40:
                    self._cadence = getattr(self, "_cadence", 0) + 1
                    if self._cadence % 4 == 0:
                        return "wait"
                    rot = ("press", "eat", "press")
                    return rot[(self._cadence // 4) % len(rot)]
                # too poor to park: forage (the pool is frozen away
                # from the aura -- nothing is lost by leaving)
                if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                    return "eat"
                tc = self._tree_competence(f, o)
                if tc is not None:
                    return tc
                s = self._scent_step(scent, "tree") \
                    or self._scent_step(scent, "bell")
                if s:
                    return s
                return self._default_act(f, o, scent)
            s = self._scent_step_smart(scent, "spring")
            if s:
                return s
            # entering the aura resets the stuck-memory (parking is
            # legitimate there; the memory is navigation-only)
            self._nav_stuck = 0
            return None
        return super()._plan(goal, f, o, scent)

    def _v5_edge_block(self, target, f, o):
        """The edge block for the lotus: any action the agent's own
        model links to the spring's effects, place-checked at the
        spring tile in view."""
        edges = self.causal_edges() if self.use_causal \
            else self.assoc_edges()
        cands = [(p, a, e) for (a, e), p in edges.items()
                 if self._effect_matches(e, target)]
        cands.sort(reverse=True)
        for p, a, e in cands:
            if not self._affordable(a, o, f):
                continue
            tile = self._effect_tile_for_edge(a, e)
            if tile is not None and tile not in (self._last_view or ""):
                continue          # the effect's place must be in view
            return a
        return None


# ---- the concrete arms ------------------------------------------------
class _AssocThreshold:
    """assoc arms: the layer's evidence bar is the arm's threshold
    (0.5 = the campaign's standing assoc layer; 0.02 = the permissive
    control with the causal layer's bar). Explicit min_p calls keep
    their value."""
    assoc_min_p = 0.5

    def assoc_edges(self, min_n=3, min_p=None):
        if min_p is None:
            min_p = self.assoc_min_p
        return EMCA.assoc_edges(self, min_n=min_n, min_p=min_p)


class AgentV5Pooled(V5Mixin, V4BelieverMixin, EMCA):
    """v2.1 pooled identifier (spec gate OFF)."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", None)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.1-pooled + v5 lotus goals"


class AgentV5Spec(V5Mixin, V4BelieverMixin, EMCA):
    """v2.2 spec-gated identifier."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", 0.10)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.2-spec + v5 lotus goals"


class AgentV5Assoc(_AssocThreshold, V5Mixin, V4BelieverMixin, EMCA):
    """assoc-only, threshold 0.5 (the campaign's standing assoc layer:
    structurally blind to the spring)."""
    def __init__(self, *args, **kw):
        kw.setdefault("use_causal", False)
        super().__init__(*args, **kw)
        self.assoc_min_p = 0.5
        self.identifier_version = "assoc-only(0.5) + v5 lotus goals"


class AgentV5Assoc02(_AssocThreshold, V5Mixin, V4BelieverMixin, EMCA):
    """assoc-only, threshold 0.02 (the permissive control: the causal
    layer's evidence bar, no causal contrast -- it can possess the
    spring edge AND every junk co-occurrence above 0.02, decoy
    included)."""
    def __init__(self, *args, **kw):
        kw.setdefault("use_causal", False)
        super().__init__(*args, **kw)
        self.assoc_min_p = 0.02
        self.identifier_version = "assoc-only(0.02) + v5 lotus goals"


class AgentV5(V5Mixin, V4RejectorMixin, AgentV25c):
    """v2.5c stratified identifier (the only layer whose contrast is
    dilution-proof). Torch plan: the inherited world route."""
    IDENTIFIER_VERSION = "v2.5c-stratified + v5 lotus goals"
