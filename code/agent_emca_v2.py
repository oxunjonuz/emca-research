"""EMCA v2.2 - Episodic Model-based Causal Agent, specificity-gated identifier.

Version lineage (must stay explicit, per TZ.md: never silently mix identifier
versions with v1 numbers):
  * v2.1 (agent_emca.py, RESULTS.md v1 matrix): pooled contrast identifier.
    FAILS on phase-confounded decoys (SANITY_V2_CONFOUNDER.md S2: accepts
    grasp->bell_rang 3/3 seeds).
  * v2.2 (this file): S7 specificity gate added to causal_edges() -- an edge
    stands only if the effect is also RARE on other actions in the pooled
    contexts (pooled_others <= spec_cap=0.10). Validated at toy scale (run 3:
    decoy rejected 3/3, true edges kept 3/3, variants A and B; regression on
    the original Terrarium: edge sets identical to v2.1). Stated boundary:
    in multi-cause worlds (two levers, one door) this rejects true edges.
  * ctx key v2: includes the visible phase trace (bell glow/dark in view),
    key_near and tree_near -- decoy design requirement (b) from the sanity
    report: the confounder's visible trace must be in the ctx key, else the
    identifier cannot subtract the phase.

Environment: env_terrarium_v2.TerrariumV2 (active decoy, rare tree, key-gated
treasure). This agent does NOT import env_terrarium (v1).
"""
import random
from collections import defaultdict, deque

from env_terrarium_v2 import (
    ACTIONS, BERRY, DOOR, LEVER, TREASURE, EMPTY, WALL,
    BELL_GLOW, BELL_DARK, TREE, KEY,
)

IDENTIFIER_VERSION = "v2.2-spec"


def view_features(obs):
    v = obs["view"]
    return {
        "berry_near": v.count(BERRY),
        "door_near": v.count(DOOR),
        "lever_near": v.count(LEVER),
        "treasure_near": v.count(TREASURE),
        "wall_near": v.count(WALL),
        "empty_near": v.count(EMPTY),
        "bell_glow_near": v.count(BELL_GLOW),
        "bell_dark_near": v.count(BELL_DARK),
        "tree_near": v.count(TREE),
        "key_near": v.count(KEY),
        "energy_low": obs["energy"] < 25,
        "energy_mid": 25 <= obs["energy"] < 60,
        "energy_high": obs["energy"] >= 60,
    }


TILE_OF_EFFECT = {          # sensory-symbol grounding: effect -> view tile to seek
    "ate": BERRY, "energy_rose": BERRY, "tree_ate": TREE,
    "lever": LEVER, "treasure": TREASURE, "door_gone": DOOR,
    "key": KEY,
}


class EMCA:
    def __init__(self, seed=0, use_causal=True, use_episodes=True,
                 use_goal_generators=True, use_self_model=True,
                 exploration=0.15, context_reset_at=None, full_wipe=False,
                 spec_cap=0.10):
        self.rng = random.Random(seed)
        self.use_causal = use_causal
        self.use_episodes = use_episodes
        self.use_goal_generators = use_goal_generators
        self.use_self_model = use_self_model
        self.eps = exploration
        self.full_wipe = full_wipe
        self.spec_cap = spec_cap      # None -> no specificity gate (v2.1-equivalent)
        self.identifier_version = (IDENTIFIER_VERSION if spec_cap is not None
                                   else "v2.1-pooled (spec gate OFF)")
        # long-term structures (survive context reset; wiped only in amnesia mode)
        self.episodes = deque(maxlen=200000)
        self.ctx_ae = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
        self.effect_ctx = defaultdict(set)     # effect -> ctx keys where it occurred
        self.goals = {}
        self.goal_seq = 0
        self.active_goal = None
        self.self_model = defaultdict(lambda: [0, 0])   # kind -> [achieved, attempts]
        self.seen_transitions = set()
        # working memory (wiped at context reset)
        self.working = deque(maxlen=64)
        self.novelty_window = deque(maxlen=200)
        self.tried_here = defaultdict(set)     # ctx -> actions tried since reset
        # instrumentation
        self.stats = defaultdict(float)
        self.goals_at_reset = []
        self.context_reset_at = context_reset_at
        self.t = 0

    # ------------------------------------------------------------------ observe
    def observe(self, o, a, r, o2, done, info):
        self.t += 1
        f1, f2 = view_features(o), view_features(o2)
        flags = tuple(sorted(k for k in info if info[k] is True))
        ctx = self._ctx_key(f1)
        self.episodes.append((f1, a, r, f2, flags))
        self.working.append((f1, a, r, f2, flags))
        self.novelty_window.append((ctx, a, self._ctx_key(f2)))
        self.tried_here[ctx].add(a)
        # ALWAYS record the action trial (denominator), then any effects (numerator)
        trial = self.ctx_ae[ctx][a]
        if "trial" not in trial:
            trial["trial"] = [0, 0]
        trial["trial"][1] += 1
        # detect effects (info flags + energy crossings only; view-motion artifacts
        # like "berry left the 3x3 window" are NOT effects - v1 lesson)
        effects = list(flags)
        if f2["energy_high"] and not f1["energy_high"]:
            effects.append("energy_rose")
        if f2["energy_low"] and not f1["energy_low"]:
            effects.append("energy_fell")
        if f1["door_near"] > 0 and f2["door_near"] < f1["door_near"]:
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

    def _effect_real(self, e, flags, f1, f2):
        if e in flags:
            return True
        if e == "energy_rose":
            return f2["energy_high"] and not f1["energy_high"]
        if e == "energy_fell":
            return f2["energy_low"] and not f1["energy_low"]
        if e == "door_gone":
            return f2["door_near"] < f1["door_near"]
        return False

    def _ctx_key(self, f):
        # v2: visible phase trace (glow/dark) + key/tree presence are part of the
        # context -- decoy design requirement (b), sanity report lesson 2.
        # NOTE: key_near/tree_near are almost always False (rare events), so the
        # ctx key stays informative; the degenerate all-False tuple of v1 is
        # broken by the phase trace (glow/dark) which flips constantly.
        return (f["berry_near"] > 0, f["door_near"] > 0, f["lever_near"] > 0,
                f["treasure_near"] > 0, f["energy_low"],
                f["bell_glow_near"] > 0, f["bell_dark_near"] > 0,
                f["key_near"] > 0, f["tree_near"] > 0)

    # ------------------------------------------------------------------ goals
    def _update_goals(self, o2, info, f2):
        for gid, g in list(self.goals.items()):
            if g["status"] != "active":
                continue
            g["steps_pursued"] += 1
            if self._goal_satisfied(g, o2, info):
                g["status"] = "achieved"
                g["achieved_at"] = self.t
                self.self_model[g["kind"]][0] += 1
                self.self_model[g["kind"]][1] += 1
                if self.active_goal == gid:
                    self.active_goal = None
            elif g["steps_pursued"] > g["deadline"]:
                g["status"] = "expired"
                self.self_model[g["kind"]][1] += 1
                if self.active_goal == gid:
                    self.active_goal = None
        if self.active_goal is None or \
                self.goals.get(self.active_goal, {}).get("status") != "active":
            g = self._generate_goal(o2, f2)
            if g:
                self.goal_seq += 1
                gid = f"g{self.goal_seq}"
                self.goals[gid] = g
                self.active_goal = gid

    GOAL_MENU = [
        ("homeostasis", "restore energy", "energy_high", 200, BERRY),
        ("explore", "open the door", "lever", 800, LEVER),
        ("key", "obtain the key", "key", 1200, KEY),
        ("tree", "eat from the fruit tree", "tree", 800, TREE),
        ("treasure", "obtain the treasure", "treasure", 2000, TREASURE),
        ("curiosity", "find novel transitions", "novelty", 400, None),
    ]

    def _generate_goal(self, o, f):
        if f["energy_low"]:
            return self._mk("homeostasis", "restore energy", "energy_high", 200)
        if not self.use_goal_generators:
            return None
        # goal arbitration v2.2 (matrix finding: the key goal monopolised the
        # whole life -- 5178/6000 steps -- while the treasure chain was complete
        # 147 steps; persistence without completion-sensing starves downstream
        # goals). Rule: a goal kind that has expired 3+ times is DEMOTED for the
        # rest of this life; unachieved-but-not-exhausted kinds still re-issue.
        expired_counts = defaultdict(int)
        for g in self.goals.values():
            if g["status"] == "expired":
                expired_counts[g["kind"]] += 1
        # persistent intentions: unachieved kinds get re-issued (cap 10 attempts)
        if self.use_self_model:
            for kind, text, target, dl, _ in self.GOAL_MENU:
                if kind == "homeostasis":
                    continue
                achieved, attempts = self.self_model[kind]
                if achieved == 0 and attempts < 10 and expired_counts[kind] < 3:
                    has_active = any(g["status"] == "active" and g["kind"] == kind
                                     for g in self.goals.values())
                    if not has_active:
                        return self._mk(kind, text, target, dl)
        if len(self.seen_transitions) < 80:
            return self._mk("curiosity", "keep exploring", "novelty", 400)
        # empowerment only when the current context is actually poor; otherwise
        # idle (no goal) so the planner falls back to competent behaviour
        if f["berry_near"] + f["door_near"] + f["lever_near"] + f["treasure_near"] \
                + f["tree_near"] + f["key_near"] == 0:
            return self._mk("empowerment", "reach richer context", "rich", 400)
        return None

    def _mk(self, kind, text, target, deadline):
        return {"kind": kind, "text": text, "target": target, "status": "active",
                "born": self.t, "deadline": deadline, "steps_pursued": 0,
                "achieved_at": None}

    def _goal_satisfied(self, g, o2, info):
        f2 = view_features(o2)
        t = g["target"]
        if t == "energy_high":
            return f2["energy_high"]
        if t == "lever":
            return info.get("lever") is True
        if t == "key":
            return info.get("key") is True
        if t == "tree":
            return info.get("tree_ate") is True
        if t == "treasure":
            return info.get("treasure") is True
        if t == "novelty":
            return len(self.seen_transitions) > getattr(self, "_nt_mark", 0) + 5
        if t == "rich":
            return f2["berry_near"] + f2["door_near"] + f2["lever_near"] >= 2
        return False

    # ------------------------------------------------------------------ acting
    def act(self, o):
        f = view_features(o)
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

    def _scent_step(self, scent, obj):
        """Follow the scent gradient toward tree/key. Returns a move or None."""
        g = scent.get(obj)
        if not g:
            return None
        best = min(g, key=lambda k: g[k])     # most negative delta = closest
        if g[best] < 0:
            return best
        return None

    def _default_act(self, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        if f["tree_near"] > 0:
            if "eat" in o.get("afford", ()):
                return "eat"                     # eat when standing on the tree
            return self._toward(TREE)
        if f["key_near"] > 0:
            return self._toward(KEY)
        s = self._scent_step(scent, "tree") or self._scent_step(scent, "key")
        if s:
            return s
        if f["energy_low"]:
            # no berry visible: head for the bell zone (warm-phase berries bloom
            # there -- this is the confounder's pull on a competent forager too)
            return self._toward(BELL_GLOW) if f["bell_glow_near"] \
                else self.rng.choice(["up", "down", "left", "right"])
        return self.rng.choice(["up", "down", "left", "right"])

    def _plan(self, goal, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        target = goal["target"]
        # survival sub-goal: if energy is low, any plan must route through eating
        if f["energy_low"]:
            if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                return "eat"
            return self._toward(BERRY)
        # opportunistic foraging (v2.2 fix): a berry in reach is taken even while
        # pursuing another goal -- the matrix showed 1705 berry-visible steps and
        # only 170 eats; goal obsession starved competence. Survival preemption
        # (energy_low) was not enough; foraging is now always-on.
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        # opportunistic tree eating (v3 fix, measured on TerrariumV3 before
        # adoption): the tree is the only storm food, but _plan only ate
        # berries -- the tree goal is demoted after one achievement
        # (self_model['tree']=[1,1]) and key/treasure goals monopolise ~97%
        # of steps, so the storm tree was invisible to the planner (fruits
        # 50-62/6000, toy_v3_check C3 FAIL). The berry-fix analogue -- a
        # tree in reach is eaten even while pursuing another goal -- lifted
        # fruits to 262-374 and cut deaths to 1-2 (monkeypatch measurement,
        # 3 seeds). Competence fix, not identifier change: all arms get it.
        if f["tree_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        edges = self.causal_edges() if self.use_causal else self.assoc_edges()
        # 1. direct causal action, affordable right here
        cands = [(p, a) for (a, e), p in edges.items()
                 if self._effect_matches(e, target)]
        cands.sort(reverse=True)
        for p, a in cands:
            if self._affordable(a, o, f):
                return a
        # 1b. scent-guided pursuit of rare-event goals (tree/key): the only
        # navigation channel to objects outside the 3x3 view
        if target in ("tree", "key"):
            s = self._scent_step(scent, target)
            if s:
                return s
        # 2. episodic context navigation: seek the sensory context where the
        #    target effect has occurred before
        if self.use_episodes:
            tile = self._effect_tile(target)
            if tile:
                if not self._tile_in_view(tile):
                    return self._toward(tile)
                # in tile context: interventional exploration - vary actions here;
                # retry affordance-relevant actions periodically (context resets
                # clear tried_here, but within one epoch each action gets retried
                # every 8 visits so causal data keeps flowing)
                ctx = self._ctx_key(f)
                tried = self.tried_here[ctx]
                if len(tried) < len(ACTIONS):
                    untried = [a for a in ACTIONS if a not in tried]
                    return self.rng.choice(untried)
                if self._visit_count(ctx) % 8 == 0:
                    # re-run affordance-relevant actions for this tile, preferring
                    # the one that matches the current goal's effect tile
                    pref = [a for a in ("press", "eat") if self._affordable(a, o, f)]
                    if pref:
                        return pref[0]
                    for a in ACTIONS:
                        if self._affordable(a, o, f) and a not in ("up", "down",
                                                                   "left", "right",
                                                                   "wait", "grasp"):
                            return a
        # 3. no known route: interventional exploration anyway (generates data)
        ctx = self._ctx_key(f)
        untried = [a for a in ACTIONS if a not in self.tried_here[ctx]]
        if untried:
            return self.rng.choice(untried)
        return None

    def _affordable(self, a, o, f):
        if a in ("up", "down", "left", "right", "wait", "grasp"):
            return True
        return a in o.get("afford", ())

    def _effect_matches(self, e, target):
        m = {"energy_high": ("ate", "energy_rose", "tree_ate"),
             "lever": ("lever",),
             "key": ("key",),
             "tree": ("tree_ate",),
             "treasure": ("treasure",),
             "novelty": (), "rich": ()}
        return e in m.get(target, ())

    def _effect_tile(self, target):
        for kind, text, tgt, dl, tile in self.GOAL_MENU:
            if tgt == target and tile:
                return tile
        return None

    def _tile_in_view(self, tile):
        return tile in (self._last_view or "")

    def _toward(self, tile):
        v = self._last_view
        if not v:
            return self.rng.choice(["up", "down", "left", "right"])
        idxs = [i for i, ch in enumerate(v) if ch == tile]
        if not idxs:
            return self.rng.choice(["up", "down", "left", "right"])
        i = idxs[0]
        r, c = divmod(i, 3)
        if r < 1:
            return "up"
        if r > 1:
            return "down"
        if c < 1:
            return "left"
        return "right"

    _last_view = None

    def _visit_count(self, ctx):
        self.stats["visits"] = getattr(self.stats, "visits", 0)
        key = "visits_" + str(ctx)
        self.stats[key] = self.stats.get(key, 0) + 1
        return int(self.stats[key])

    # ------------------------------------------------------------------ reset
    def _context_reset(self):
        """Subjectivity probe. Normal mode: wipe working memory only.
        Amnesia mode (control): wipe EVERYTHING long-term too."""
        self.working.clear()
        self.novelty_window.clear()
        self.tried_here = defaultdict(set)
        self.stats["context_resets"] += 1
        self.goals_at_reset = [
            {"id": gid, "kind": g["kind"], "target": g["target"]}
            for gid, g in self.goals.items() if g["status"] == "active"
        ]
        if self.full_wipe:
            self.episodes.clear()
            self.ctx_ae = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
            self.effect_ctx = defaultdict(set)
            self.self_model = defaultdict(lambda: [0, 0])
            self.seen_transitions = set()
            # goals: only the active one survives as a bare intention (amnesia keeps
            # the felt intention but loses all knowledge) - strictest honest control
            kept = self.goals.get(self.active_goal) if self.active_goal else None
            self.goals = {}
            if kept:
                self.goals[self.active_goal] = kept
            self.stats["full_wipes"] += 1

    # ------------------------------------------------------------------ edges
    def causal_edges(self, min_n=3, min_p=0.02, margin=0.02):
        """v2.2 specificity-gated contrast (S7). An edge stands only if:
          (i)  rate(a,e) >= min_p over >= min_n trials,
          (ii) rate(a,e) - pooled_rate(others, e) >= margin  [contrast],
          (iii) pooled_rate(others, e) <= spec_cap            [specificity].
        Rationale: a cause is the DOMINANT source of its effect; a
        phase-confounded decoy shares its effect with every action taken in
        the same phase (grasp->bell_rang: others ~0.37). Validated at toy
        scale; boundary: multi-cause worlds (two levers, one door) lose true
        edges. Denominators from explicit 'trial' counters. Single-action
        boundary case (on==0) still accepted."""
        out = {}
        effects = {e for acts in self.ctx_ae.values()
                   for effs in acts.values() for e in effs if e != "trial"}
        for e in effects:
            agg = defaultdict(lambda: [0, 0])          # action -> [yes, n]
            for ctx, acts in self.ctx_ae.items():
                for a, effs in acts.items():
                    n = effs.get("trial", [0, 0])[1]
                    if e in effs:
                        y = effs[e][0]
                        agg[a][0] += y
                        agg[a][1] += n
                    else:
                        agg[a][1] += n
            for a, (y, n) in agg.items():
                if n < min_n:
                    continue
                rate_a = y / n
                if rate_a < min_p:
                    continue
                # pooled rate of OTHER actions in contexts where a was tried
                oy = on = 0
                for ctx, acts in self.ctx_ae.items():
                    if a in acts and e in acts[a]:
                        for a2, effs in acts.items():
                            if a2 != a:
                                oy += effs.get(e, [0, 0])[0]
                                on += effs.get("trial", [0, 0])[1]
                if on == 0:
                    out[(a, e)] = round(rate_a, 3)   # single-action boundary case
                    continue
                pooled = oy / on
                if self.spec_cap is not None and pooled > self.spec_cap:
                    continue                        # S7: necessity/specificity
                if rate_a - pooled >= margin:
                    out[(a, e)] = round(rate_a, 3)
        return out

    def assoc_edges(self, min_n=3, min_p=0.5):
        """Raw co-occurrence rates (what correlation alone would assert)."""
        out = {}
        agg = defaultdict(lambda: [0, 0])
        for ctx, acts in self.ctx_ae.items():
            for a, effs in acts.items():
                n = effs.get("trial", [0, 0])[1]
                for e, (y, en) in effs.items():
                    if e == "trial":
                        continue
                    agg[(a, e)][0] += y
                    agg[(a, e)][1] += n
        for k, (y, n) in agg.items():
            if n >= min_n and y / n >= min_p:
                out[k] = round(y / n, 3)
        return out
