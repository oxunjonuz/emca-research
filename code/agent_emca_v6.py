"""EMCA v6 agents -- the GREY-TRUTH arms (turn 115, msg_00115).

The question: does ACTIVE causal experimentation pay when it is the
ONLY epistemic route to an expensive resource? The world (env_terrarium_
v6) makes the spring edge GREY (RR=1.5): no passive layer can accept it
(stratified gate RR>=2; pooled diluted; assoc(0.5) blind). The prize is
a golden lotus (+800). The only routes to the edge: an ACTIVE
do-intervention (the prober), possession-by-threshold (assoc02), or a
free injection (the oracle, an analysis device).

ARM LINEAGE (one filing path, one goal menu, one set of competences;
arms differ ONLY in edge rules + the prober module):

  AgentV6         -- v2.5c stratified, passive, honest (the REJECTOR:
                     grey is invisible to it by construction).
  AgentV6Pooled   -- v2.1 pooled (the BELIEVER: decoy accepted; the
                     spring edge is diluted for it -- measured column).
  AgentV6Assoc    -- assoc-only 0.5 (structurally blind).
  AgentV6Assoc02  -- assoc-only 0.02 (possession without contrast: it
                     CAN hold (wait, spring_flow) at p ~ 0.3*w > 0.02).
  AgentV6Oracle   -- v2.5c + the spring edge INJECTED at t=2000 (the
                     analysis device: the edge's GROSS value, no
                     discovery cost; never in fairness verdicts).
  AgentV6Prober   -- v2.5c + the active do-intervention module (the
                     prober of v3.2/v3.3, retargeted to the aura).
  AgentV6NoCausal -- no causal layer, no assoc layer (floor control).

THE SHARED POLICY COMPETENCE (fairness rule, declared in the prereg):
the momentum-window response is written ONCE in V6Mixin and inherited
by every arm. The edge block fires 'wait' at the spring whenever the
arm's own model carries an edge (a, spring_flow)/(a, lotus) --
streak-waiting farms the windows. The blind cadence (no edge) rotates
actions and never streaks: it nets ~-0.8 pool/step and cannot fill.
The contrast between arms is therefore KNOWLEDGE, not reflexes.

THE PROBER (adapted from AgentV32Prober, v3.2):
  * grey detection: edges with 1<=RR<2 in the stratified report, plus
    the spring edge (the world's grey cause by construction);
  * protocol: alternated blocks of wait vs grasp IN THE AURA (TOY-
    CAUGHT FIX: the first draft used 'press' as the control -- press
    is affordable only ON THE LEVER CELL, so the control arm never
    accumulated a single trial and no verdict ever fired; grasp is
    affordable everywhere, non-move, and inert at the spring); the
    probe pauses (aborts without a verdict) while the spring is DRY
    or a storm runs -- scoring zeros would poison the Fisher table
    with a false REJECT;
  * verdict: Fisher exact, p<0.05 AND RR>=1.3 -> CAUSAL; the edge
    then enters causal_edges() and the lotus plan fires.
  * the probe runs IN THE AURA (the edge is place-bound), after the
    passive data has accumulated (t>2000), one edge at a time, and
    survival preemption always wins (the v3.3 lesson).
"""
import math
import random
from collections import defaultdict, deque

from agent_emca_v2 import EMCA
from sanity_stratified3 import AgentV25c
from agent_emca_v33 import V33Mixin
from agent_emca_v4 import V4Mixin, V4BelieverMixin, V4RejectorMixin
from agent_emca_v5 import (
    V5Mixin, V5Filing, view_features5, _AssocThreshold,
)
from agent_emca_v32 import fisher_exact_2x2
from env_terrarium_v2 import ACTIONS, BERRY, LEVER, TREASURE, KEY, TREE, WALL
from env_terrarium_v5 import SPRING_TILE, LOTUS_TILE
from env_terrarium_v6 import DRY_TILE

ALTAR_TILE = "A"
TREASURY_TILE = "$"
BRAZIER_TILE_V6 = "X"
MOVES = ("up", "down", "left", "right")
SPRING_EDGE = ("wait", "spring_flow")


def view_features6(obs):
    f = dict(view_features5(obs))
    v = obs["view"]
    f["spring_near"] = v.count(SPRING_TILE) + v.count(DRY_TILE)
    f["spring_dry"] = v.count(DRY_TILE)
    return f


class V6Filing(V5Filing):
    """ONE filing path for every v6 arm: view_features6 (the dry spring
    is a distinct public tile; spring_near counts both), the spring in
    the ctx key, the v2.5c door_gone data-fix, and the v6 DATA BAR:
    every identifier's edge call in this world requires n_a >= 30
    trials (min_n 3 -> 30). TOY-CAUGHT: at min_n=3 the stratified gate
    accepted the spring edge at t=222 on n_a=7 (a lucky RR=3.0 draw
    crossed the 2.0 gate) -- the grey zone leaked into the passive
    layer on early noise. The bar is a DATA-SUFFICIENCY requirement,
    applied identically to every arm's every edge rule (it raises the
    evidence bar; it does not move any verdict threshold). Identifier
    classes differ ONLY in their edge rules, never in their data."""

    MIN_N_V6 = 30

    def causal_edges(self, min_n=None, min_p=0.02, margin=None):
        if min_n is None:
            min_n = self.MIN_N_V6
        return super().causal_edges(min_n=min_n, min_p=min_p,
                                    margin=margin if margin is not None
                                    else 0.02)

    def assoc_edges(self, min_n=None, min_p=None):
        if min_n is None:
            min_n = self.MIN_N_V6
        if min_p is None:
            min_p = getattr(self, "assoc_min_p", 0.5)
        return super().assoc_edges(min_n=min_n, min_p=min_p)

    def observe(self, o, a, r, o2, done, info):
        self.t += 1
        f1, f2 = view_features6(o), view_features6(o2)
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
        return (
            f["berry_near"] > 0, f["door_near"] > 0, f["lever_near"] > 0,
            f["treasure_near"] > 0, f["energy_low"],
            f["bell_glow_near"] > 0, f["bell_dark_near"] > 0,
            f["key_near"] > 0, f["tree_near"] > 0,
            f.get("chime_near", 0) > 0, f.get("altar_near", 0) > 0,
            f.get("torch_near", 0) > 0, f.get("treasury_near", 0) > 0,
            f.get("spring_near", 0) > 0,
        )


class V6Mixin(V6Filing, V5Mixin):
    """The v6 planning layer. The lotus plan routes through the edge
    (the edge block fires the streak-wait that farms the momentum
    windows); the blind cadence (no edge) rotates actions and never
    streaks: it nets ~-0.8 pool/step and cannot fill. The dry spring
    is respected (no lotus pursuit while the spring sleeps -- the
    cooldown is world-visible).

    TOY-CAUGHT FIX (documented in the prereg amendment, applied to
    every arm equally BEFORE the matrix): the v5 energy gate (55) left
    a 40-55 band where edge-carrying arms parked in the aura on the
    DRAINING cadence -- the pool bled ~0.8/step while waits fill only
    +0.073/wait, so even the oracle farmed 1 lotus in 3 toy seeds.
    The v6 structure: an edge-carrying arm either STREAK-WAITS (energy
    >= 40, the v3.3 altar-gate scale) or FORAGES AWAY (the pool is
    frozen outside the aura -- leaving costs nothing); the cadence is
    strictly the no-edge blind exploration, whose drain IS the
    anti-luck design. LOTUS_WAIT_ENERGY 55 -> 40."""

    LOTUS_WAIT_ENERGY = 40

    # ---- goal generation: the lotus goal must survive expiry ----
    # TOY-CAUGHT FIX (harness-level, every arm equally): the v2.2
    # arbitration DEMOTES a kind after 3 expiries for the rest of the
    # life. In v5 the lotus filled in ~50 waits, so 3x1200 steps were
    # plenty; in v6 the fill needs ~35-80 productive waits inside a
    # 2000-step cooldown cycle, and the goal expired 3 times (3603
    # steps) before the pool could fill -- the farmer was demoted
    # before it ever farmed (toy-2: oracle lotuses 0/2/1). The v6
    # rule: the lotus kind is exempt from expiry-demotion while the
    # spring is not dry (the world's own public signal that the
    # channel is open); when the spring sleeps, the goal expires
    # normally and the cooldown is respected. This is the v3.1
    # wanting-refresh lesson applied to expiry, not a threshold.
    def _generate_goal(self, o, f):
        g = super()._generate_goal(o, f)
        if g is not None:
            return g
        if not self.use_goal_generators or not self.use_self_model:
            return None
        # the lotus kind re-issues while the channel is open, even
        # after 3 expiries (the demotion rule stays for every other
        # kind; the spring's own dry tile gates this one)
        if f.get("spring_dry", 0) == 0 and f.get("spring_near", 0) > 0:
            has_active = any(g2["status"] == "active"
                             and g2["kind"] == "lotus"
                             for g2 in self.goals.values())
            if not has_active:
                achieved, attempts = self.self_model.get(
                    "lotus", [0, 0])
                if achieved > 0 or attempts < 10:
                    return self._mk("lotus", "bloom the spring lotus",
                                    "lotus_bloom", 1200)
        return None

    def act(self, o):
        f = view_features6(o)
        self._last_view = o["view"]
        if f["energy_low"] and f["berry_near"] > 0 \
                and "eat" in o.get("afford", ()):
            return "eat"
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

    def _plan(self, goal, f, o, scent=None):
        scent = scent or o.get("scent") or {}
        target = goal["target"]
        if target == "lotus_bloom":
            if f.get("lotus_near", 0) > 0:
                if "eat" in o.get("afford", ()):
                    return "eat"
                return self._toward(LOTUS_TILE)
            # the dry spring: the world says the channel is closed --
            # public signal, every arm respects it (no wasted pursuit)
            if f.get("spring_dry", 0) > 0:
                tc = self._tree_competence(f, o)
                if tc is not None:
                    return tc
                if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                    return "eat"
                return self._default_act(f, o, scent)
            if f["energy_low"]:
                if f["berry_near"] > 0 and "eat" in o.get("afford", ()):
                    return "eat"
                tc = self._tree_competence(f, o)
                if tc is not None:
                    return tc
                return self._toward(BERRY)
            # storm competence overrides the streak (waiting through a
            # storm in the cold zone is lethal; the pool is frozen
            # outside the aura -- nothing is lost by running)
            if f["bell_glow_near"] > 0 or scent.get("bell"):
                tc = self._tree_competence(f, o)
                if tc is not None:
                    return tc
                s = self._scent_step(scent, "tree")
                if s:
                    return s
            # 1. does the arm's own model carry a lotus route? (the
            #    edge block is place-checked only)
            edge_action = self._v5_edge_block(target, f, o)
            if edge_action is not None:
                if o["energy"] >= self.LOTUS_WAIT_ENERGY:
                    return edge_action   # the streak: the farmer
                # too poor to wait: forage AWAY (the pool is frozen
                # outside the aura -- leaving costs nothing)
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
            # 2. no edge: the shared blind cadence (rotates actions in
            #    place; NEVER a wait streak -- it cannot farm windows;
            #    its drain IS the anti-luck design)
            if f.get("spring_near", 0) > 0:
                if o["energy"] >= 40:
                    self._cadence = getattr(self, "_cadence", 0) + 1
                    if self._cadence % 4 == 0:
                        return "wait"
                    rot = ("press", "eat", "press")
                    return rot[(self._cadence // 4) % len(rot)]
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
            return None
        return super()._plan(goal, f, o, scent)


# ---------------------------------------------------------------------------
# The concrete arms
# ---------------------------------------------------------------------------
class AgentV6(V6Mixin, V4RejectorMixin, AgentV25c):
    """REJECTOR: v2.5c stratified, passive, honest. The grey spring
    edge is invisible to it by construction (RR=1.5 < 2)."""
    IDENTIFIER_VERSION = "v2.5c-stratified + v6 grey-lotus goals"


class AgentV6Pooled(V6Mixin, V4BelieverMixin, EMCA):
    """BELIEVER: v2.1 pooled (decoy accepted; spring diluted)."""
    def __init__(self, *args, **kw):
        kw.setdefault("spec_cap", None)
        super().__init__(*args, **kw)
        self.identifier_version = "v2.1-pooled + v6 grey-lotus goals"


class AgentV6Assoc(_AssocThreshold, V6Mixin, V4BelieverMixin, EMCA):
    """assoc-only 0.5 (structurally blind: marginal 0.30*w < 0.5)."""
    def __init__(self, *args, **kw):
        kw.setdefault("use_causal", False)
        super().__init__(*args, **kw)
        self.assoc_min_p = 0.5
        self.identifier_version = "assoc-only(0.5) + v6 grey-lotus goals"


class AgentV6Assoc02(_AssocThreshold, V6Mixin, V4BelieverMixin, EMCA):
    """assoc-only 0.02: possession without contrast (it CAN hold the
    spring edge at p ~ 0.3*w > 0.02 -- the H4 control)."""
    def __init__(self, *args, **kw):
        kw.setdefault("use_causal", False)
        super().__init__(*args, **kw)
        self.assoc_min_p = 0.02
        self.identifier_version = "assoc-only(0.02) + v6 grey-lotus goals"


class AgentV6NoCausal(V6Mixin, V4BelieverMixin, EMCA):
    """No causal layer, no assoc layer for planning (the floor)."""
    def __init__(self, *args, **kw):
        kw.setdefault("use_causal", False)
        super().__init__(*args, **kw)
        self.assoc_min_p = 99.0        # no layer ever asserts an edge
        self.identifier_version = "nocausal + v6 grey-lotus goals"

    def assoc_edges(self, min_n=3, min_p=None):
        return {}

    def causal_edges(self, *a, **kw):
        return {}


class AgentV6Oracle(V6Mixin, V4RejectorMixin, AgentV25c):
    """ORACLE (analysis device, not a fair arm): the v2.5c rejector
    with the spring edge INJECTED at t=2000. Its numbers enter only
    the decomposition (the edge's gross value), never fairness
    verdicts. The injection is declared in the prereg."""
    IDENTIFIER_VERSION = "v2.5c + INJECTED spring edge (oracle device)"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._injected = False

    def causal_edges(self, min_n=None, min_p=0.02, margin=None):
        base = super().causal_edges(min_n=min_n, min_p=min_p, margin=margin)
        if self.t >= 2000:
            base[SPRING_EDGE] = 0.30
        return base


class AgentV6Prober(V6Mixin, V4RejectorMixin, AgentV25c):
    """PROBER: v2.5c passive + the active do-intervention module,
    retargeted to the spring aura. Grey detection: the stratified
    report's 1<=RR<2 edges + the spring edge (the world's grey cause).
    Protocol: alternated blocks of wait vs press IN THE AURA; verdict
    by Fisher exact; CAUSAL -> the edge enters causal_edges() -> the
    lotus plan's edge block fires the streak-wait farmer."""
    IDENTIFIER_VERSION = "v2.5c + v6 goals + aura do-interventions"

    GRAY_LO, GRAY_HI = 1.0, 2.0
    BLOCK = 5
    MAX_BLOCKS = 160           # 800+800 scheduled trials per edge. The
                                # pauses (storm/dry) cut the effective n
                                # to ~60% of scheduled; measured at 100
                                # blocks: ~265/arm -> p=0.09-0.12 on a
                                # TRUE 0.30-vs-0.20 edge (verdicts
                                # REJECT/UNRESOLVED/CAUSAL across seeds).
                                # The v3.2 lesson: more DATA, not a
                                # looser threshold. 160 blocks -> ~500/
                                # arm effective -> expected p ~0.0003.
    P_VERDICT = 0.05
    RR_ACCEPT = 1.3

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.probe_state = None
        self.probe_log = defaultdict(lambda: {
            "target_yes": 0, "target_no": 0,
            "ctrl_yes": 0, "ctrl_no": 0, "blocks": 0})
        self.verdicts = {}
        self.probe_steps = 0

    # ---- grey detection ----
    def gray_edges(self, min_n=30):
        out = []
        self.causal_edges()        # refresh self.strat_report
        for (a, e), rep in getattr(self, "strat_report", {}).items():
            rr = rep.get("rr")
            if rr == "inf" or rr is None:
                continue
            if rep.get("n_a", 0) >= min_n and self.GRAY_LO <= rr < self.GRAY_HI:
                out.append(((a, e), rep))
        # the spring edge is the world's grey cause by construction;
        # probe it once the passive data has accumulated
        if SPRING_EDGE not in self.verdicts and self.t > 2000:
            out.append((SPRING_EDGE, {"rate_a": 0.0, "rate_o": 0.0,
                                      "rr": 1.5, "n_a": 0, "n_o": 0}))
        return out

    # ---- probe scheduling ----
    def _maybe_start_probe(self, o, f):
        if self.probe_state is not None:
            return False
        if self.t < 2000:
            return False
        if f.get("spring_near", 0) == 0:
            return False           # the spring edge is place-bound
        # TOY-CAUGHT FIX: never probe while the spring sleeps -- the
        # dry channel scores zeros for BOTH arms and the Fisher verdict
        # would banish the edge with a false REJECT (the first toy run
        # had the probe eating its 500+500 trials inside a cooldown)
        if f.get("spring_dry", 0) > 0:
            return False
        # TOY-CAUGHT FIX: never probe in a storm (the far-zone storm
        # signal is the same v3.2+ proxy; waiting out a fury in the
        # cold aura is lethal and the trials would die mid-block)
        scent_probe = o.get("scent") or {}
        if f["bell_glow_near"] > 0 or scent_probe.get("bell"):
            return False
        grays = self.gray_edges()
        if not grays:
            return False
        order = [g for g in grays if g[0] == SPRING_EDGE] \
            + [g for g in grays if g[0] != SPRING_EDGE]
        for (a, e), rep in order:
            if (a, e) in self.verdicts:
                continue
            self.probe_state = {
                "edge": (a, e), "ctrl": "grasp", "phase": "trial",
                "block": 0, "arm": "target", "n_this_block": 0,
            }
            return True
        return False

    # ---- acting: the probe takes over when active ----
    def act(self, o):
        f = view_features6(o)
        self._last_view = o["view"]
        # survival preemption always wins (even mid-probe)
        if f["energy_low"] and f["berry_near"] > 0 \
                and "eat" in o.get("afford", ()):
            return "eat"
        # a bloomed lotus is food for every arm (sight, not knowledge)
        if f.get("lotus_near", 0) > 0 and "eat" in o.get("afford", ()):
            return "eat"
        scent = o.get("scent") or {}
        # storm competence overrides probes (dying mid-probe helps
        # nobody) -- the same far-zone signal as v3.2+
        if f["bell_glow_near"] > 0 or scent.get("bell"):
            s = self._scent_step(scent, "tree")
            if s and (self.probe_state is not None or f["energy_low"]):
                return s
        if self.probe_state is not None:
            a = self._probe_act(f, o, scent)
            if a is not None:
                self.probe_steps += 1
                return a
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        if self._maybe_start_probe(o, f):
            a = self._probe_act(f, o, scent)
            if a is not None:
                self.probe_steps += 1
                return a
        return super().act(o)

    def _probe_act(self, f, o, scent):
        st = self.probe_state
        # TOY-CAUGHT FIX: a probe that finds itself in a storm or on a
        # DRY spring ABORTS without a verdict (scoring zeros would
        # poison the Fisher table; the edge is re-probed when the
        # channel reopens)
        if f.get("spring_dry", 0) > 0:
            self.probe_state = None
            return None
        if f["bell_glow_near"] > 0:
            self.probe_state = None
            return None
        # the probe must stay in the aura (the edge is place-bound);
        # if the survival preemption dragged us out, walk back
        if f.get("spring_near", 0) == 0:
            s = self._scent_step_smart(scent, "spring")
            if s:
                return s
            return None
        arm_action = st["edge"][0] if st["arm"] == "target" else st["ctrl"]
        if self._affordable(arm_action, o, f):
            st["n_this_block"] += 1
            if st["n_this_block"] >= self.BLOCK:
                st["n_this_block"] = 0
                st["arm"] = "ctrl" if st["arm"] == "target" else "target"
                st["block"] += 1
                if st["block"] >= self.MAX_BLOCKS:
                    self._finish_probe()
            return arm_action
        return None

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
            verdict = "REJECT"
        elif p >= self.P_VERDICT and rr < self.RR_ACCEPT:
            verdict = "REJECT"
        else:
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
        if st is not None:
            log = self.probe_log[st["edge"]]
            hit = info.get(st["edge"][1]) is True
            if st["arm"] == "target" and a == st["edge"][0]:
                log["target_yes" if hit else "target_no"] += 1
                log["blocks"] = st["block"]
            elif st["arm"] == "ctrl" and a == st["ctrl"]:
                log["ctrl_yes" if hit else "ctrl_no"] += 1
                log["blocks"] = st["block"]
        super().observe(o, a, r, o2, done, info)

    # ---- verdict-gated edges ----
    def causal_edges(self, min_n=None, min_p=0.02, margin=None):
        base = super().causal_edges(min_n=min_n, min_p=min_p, margin=margin)
        for (a, e), v in self.verdicts.items():
            if v["verdict"] == "CAUSAL":
                base[(a, e)] = round(v["rr"], 3) \
                    if v["rr"] != "inf" else 1.0
            elif v["verdict"] == "REJECT":
                base.pop((a, e), None)
        return base
