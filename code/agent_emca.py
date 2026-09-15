"""EMCA v2 - Episodic Model-based Causal Agent.

Changes vs v1 (recorded after smoke run exposed defects, see RESULTS.md):
  * Causal edges are now identified by RANDOMIZED CONTRAST: an action a "causes"
    effect e only if P(e | do(a), ctx) exceeds P(e | do(a'), ctx) pooled over the
    same contexts by a margin. v1's "varied actions" heuristic produced spurious
    edges (left->died, right->treasure at p=1.0) because mere co-occurrence in a
    varied context was counted as intervention. This was a real identification bug.
  * Planner is generic (no hand-coded lever/door/treasure chain): direct causal
    action -> episodic context navigation -> interventional exploration.
  * Goal bookkeeping: attempts counted on every completion (v1 never counted
    successes as attempts, so one goal kind regenerated 1659 times).
  * Persistent intentions: unachieved goal kinds are re-issued (cap 10) - this is
    what makes goals survive context resets (E6) and long pursuits possible (E5).
  * Amnesia mode: full wipe of long-term structures at reset (E2 control).

Architecture claim under test (H-A): append-only episodes + contrast-identified
causal graph + generic planner + intrinsic goal generators + self-model.
"""
import random
from collections import defaultdict, deque

from env_terrarium import ACTIONS, BERRY, DOOR, LEVER, TREASURE, EMPTY, WALL


def view_features(obs):
    v = obs["view"]
    return {
        "berry_near": v.count(BERRY),
        "door_near": v.count(DOOR),
        "lever_near": v.count(LEVER),
        "treasure_near": v.count(TREASURE),
        "wall_near": v.count(WALL),
        "empty_near": v.count(EMPTY),
        "energy_low": obs["energy"] < 25,
        "energy_mid": 25 <= obs["energy"] < 60,
        "energy_high": obs["energy"] >= 60,
    }


TILE_OF_EFFECT = {          # sensory-symbol grounding: effect -> view tile to seek
    "ate": BERRY, "energy_rose": BERRY, "lever": LEVER,
    "treasure": TREASURE, "door_gone": DOOR,
}


class EMCA:
    def __init__(self, seed=0, use_causal=True, use_episodes=True,
                 use_goal_generators=True, use_self_model=True,
                 exploration=0.15, context_reset_at=None, full_wipe=False):
        self.rng = random.Random(seed)
        self.use_causal = use_causal
        self.use_episodes = use_episodes
        self.use_goal_generators = use_goal_generators
        self.use_self_model = use_self_model
        self.eps = exploration
        self.full_wipe = full_wipe
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
        return (f["berry_near"] > 0, f["door_near"] > 0, f["lever_near"] > 0,
                f["treasure_near"] > 0, f["energy_low"])

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
        ("treasure", "obtain the treasure", "treasure", 1200, TREASURE),
        ("curiosity", "find novel transitions", "novelty", 400, None),
    ]

    def _generate_goal(self, o, f):
        if f["energy_low"]:
            return self._mk("homeostasis", "restore energy", "energy_high", 200)
        if not self.use_goal_generators:
            return None
        # persistent intentions: unachieved kinds get re-issued (cap 10 attempts)
        if self.use_self_model:
            for kind, text, target, dl, _ in self.GOAL_MENU:
                if kind == "homeostasis":
                    continue
                achieved, attempts = self.self_model[kind]
                if achieved == 0 and attempts < 10:
                    has_active = any(g["status"] == "active" and g["kind"] == kind
                                     for g in self.goals.values())
                    if not has_active:
                        return self._mk(kind, text, target, dl)
        if len(self.seen_transitions) < 80:
            return self._mk("curiosity", "keep exploring", "novelty", 400)
        # empowerment only when the current context is actually poor; otherwise
        # idle (no goal) so the planner falls back to competent behaviour
        if f["berry_near"] + f["door_near"] + f["lever_near"] + f["treasure_near"] == 0:
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
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        goal = self.goals.get(self.active_goal) if self.active_goal else None
        if goal is None:
            return self._default_act(f, o)
        a = self._plan(goal, f, o)
        return a if a else self._default_act(f, o)

    def _default_act(self, f, o):
        if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            return "eat"
        if f["energy_low"]:
            return self._toward(BERRY)
        return self.rng.choice(["up", "down", "left", "right"])

    def _plan(self, goal, f, o):
        target = goal["target"]
        # survival sub-goal: if energy is low, any plan must route through eating
        if f["energy_low"]:
            if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                return "eat"
            return self._toward(BERRY)
        edges = self.causal_edges() if self.use_causal else self.assoc_edges()
        # 1. direct causal action, affordable right here
        cands = [(p, a) for (a, e), p in edges.items()
                 if self._effect_matches(e, target)]
        cands.sort(reverse=True)
        for p, a in cands:
            if self._affordable(a, o, f):
                return a
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
        m = {"energy_high": ("ate", "energy_rose"), "lever": ("lever",),
             "treasure": ("treasure",), "novelty": (), "rich": ()}
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
            for gid, g in self.goals.items() if g["status"] == "active"]
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
        """Contrast-identified edges (rare-effect calibration): rate(a,e) must
        exceed the pooled rate of OTHER actions in the SAME contexts by `margin`.
        Denominators come from explicit 'trial' counters (every action trial is
        recorded, effect or not). Rare-but-exclusive effects (press->lever fires
        only at the lever tile, ~2/72 overall) are identified by contrast, not by
        absolute rate. If no other action was ever tried in those contexts (on==0),
        the edge is accepted as the single-action boundary case."""
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
                if rate_a - oy / on >= margin:
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
