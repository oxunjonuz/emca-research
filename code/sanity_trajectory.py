#!/usr/bin/env python3
"""Toy check of TZ.md direction 1 (trajectory confounder) + direction 4
(reflexive identifier: the agent's own eps as its randomized trial).

TZ.md (turn 97) asks whether a confounder routed through the agent's own
purposiveness can bite a randomised agent, which the phase confounder of v2
could not (RESULTS_V2.md negative result 1: eps-noise balances actions across
phases, so the decoy never reaches the identifier).

DIRECTION 1 (as specified in TZ.md, made non-degenerate):
  Hidden WEATHER (calm/storm) is the common cause. In storm: a fruit tree
  spawns near the bell (Manhattan dist <= 2) and the wind rings the bell
  often (P=0.40); in calm: no tree, berries bloom at the far shelter, the
  bell almost never rings (P=0.01). The bell is NEVER causally affected by
  any action (oracle-checked). The agent's own goal architecture produces
  the confounded trajectory: when a tree exists it walks purposively to the
  bell zone (scent gradient, ~85% deliberate steps), so its "up"-moves
  (shelter is at the bottom, the bell at the top) concentrate in storms,
  where the ring rate is 40x higher. Correlation without causation, carried
  by the trajectory, not by the phase. eps cannot wash it out: the 15%
  random steps dilute but do not re-route the 85% purposive ones.
  NOTE (design requirement found by analysis): a uniform gust probability
  produces ZERO correlation (rate(move->ring) == pooled == P(gust)); the
  coupling through a hidden common cause is what makes direction 1 a
  confounder at all. Deliberately NO visible storm trace (unlike v2's glow):
  the whole point is that the confounder is invisible in observation and
  lives only in behaviour.

DIRECTION 4 (mine): the v2 negative result said the agent's eps-noise
  "self-decorrelates" its actions from the phase. Turn that nuisance into
  the instrument: an edge (a,e) stands only if the effect holds BOTH when
  the action was chosen deliberately AND when it was chosen by the agent's
  own eps -- within the same refined context (base ctx + affordance flags,
  so position-gated effects are not falsely rejected). A true cause does
  not care why you acted; a trajectory confounder lives in the deliberation.
  Boundary (stated up front): eps randomises the ACTION, not the
  DESTINATION, so it controls trajectory confounding only partially; the
  measured gap is the "scent-following premium". If it falls below the
  slack, direction 4 fails as instrumented and the honest fix is
  destination-randomisation (4b), not a bigger slack.

ORACLES (independent of any agent):
  O1 gust action-independence: P(ring|do(a)) equal for all actions (<0.02)
  O2 storm-ring coupling: P(ring|storm)~0.40, P(ring|calm)~0.01
  O3 tree geometry: spawns always within dist<=2 of the bell; tree exists
     only during storm

PRE-REGISTERED CRITERIA (fixed before the first run of this file):
  T1 correlation fooled:      any (move,ring) in assoc(min_p=0.02) >=2/3
     (assoc threshold lowered from v2's 0.5 to 0.02 to match the causal
      identifier's sensitivity -- otherwise the comparison is rigged)
  T2 pooled v2.1 fooled:      any (move,ring) in pooled >=2/3
  T3 spec v2.2 fooled:        any (move,ring) in spec >=2/3 (informative
     either way: if FAIL, the spec gate already survives direction 1)
  T4 reflex rejects:          no (move,ring) in reflex >=2/3, data present
  T5 true edges survive:      (eat,ate) and (press,lever) in spec AND
     reflex >=2/3; (eat,tree_ate) reported (survival informative)
  T6 consistency+determinism: recomputed arms identical; fresh re-run of
     seed 1 bit-identical edge sets
  READY = T1 & T2 & T4 & T5 & T6.
  Harness gate (before verdicts): tree_fruits > 0 in every agent run
  (else the pursuit never completes -- a V5-like defect, fix the env first).
"""
import sys
from collections import defaultdict

from agent_emca_v2 import EMCA, view_features
from env_terrarium_v2 import ACTIONS, BERRY, LEVER, EMPTY, WALL
from env_terrarium_v2 import BELL_DARK, TREE

W, H = 9, 9
MAP = [
    "#########",
    "#..Q....#",      # bell at (1,3) -- top area, never glows (no storm trace)
    "#.......#",
    "#.......#",
    "#.......#",
    "#.......#",
    "#.....L.#",      # lever at (6,6) -- inside the calm shelter zone
    "#.......#",
    "#########",
]
BELL_POS = (1, 3)
LEVER_POS = (6, 6)
RING_STORM, RING_CALM = 0.40, 0.01
STORM_DWELL = (60, 100)
CALM_DWELL = (200, 300)
TREE_SPAWN_MAX_DIST = 2
SHELTER = [(r, c) for r in range(5, 8) for c in range(5, 8)
           if MAP[r][c] == EMPTY and (r, c) != LEVER_POS]
MOVES = ("up", "down", "left", "right")
DECOY_MOVES = (("up", "bell_rang"), ("down", "bell_rang"),
               ("left", "bell_rang"), ("right", "bell_rang"))
TRUE_EDGES = [("eat", "ate"), ("press", "lever"), ("eat", "tree_ate")]


class GustEnv:
    """Trajectory-confounder environment (direction 1).

    Hidden weather calm/storm. Storm: tree near the bell + frequent ringing.
    Calm: berries at the shelter + almost no ringing. The bell is never
    affected by any action. Energy is static: the only reasons to move are
    the tree (scent) and goal-driven wandering -- the trajectory is maximally
    purposive.
    """

    def __init__(self, seed):
        import random
        self.rng = random.Random(seed)
        self.seed = seed
        self.t = 0
        self.pos = [4, 4]
        self.phase = "calm"
        self.dwell = self.rng.randint(*CALM_DWELL)
        self.tree = None
        self.tree_fuel = 0
        self.berries = set()
        self.tree_eaten = 0
        self.berries_eaten = 0
        self.lever_presses = 0
        self.storm_steps = 0
        self._maintain_berries()

    def _maintain_berries(self):
        if self.phase == "calm":
            if len(self.berries) < 3:
                free = [c for c in SHELTER if c not in self.berries]
                if free:
                    self.berries.add(self.rng.choice(free))
        else:
            self.berries = set()          # storm blows the berries away

    def obs(self):
        r, c = self.pos
        view = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    view.append(WALL)
                    continue
                ch = MAP[rr][cc]
                if ch == EMPTY and (rr, cc) in self.berries:
                    ch = BERRY
                if self.tree and (rr, cc) == self.tree:
                    ch = TREE
                view.append(ch)
        afford = ["grasp", "wait"]
        if (r, c) in self.berries or (self.tree and (r, c) == self.tree):
            afford.append("eat")
        if (r, c) == LEVER_POS:
            afford.append("press")
        scent = {}
        if self.tree is not None:
            orow, ocol = self.tree
            d = abs(r - orow) + abs(c - ocol)
            scent["tree"] = {
                "up": (abs(r - 1 - orow) + abs(c - ocol)) - d,
                "down": (abs(r + 1 - orow) + abs(c - ocol)) - d,
                "left": (abs(r - orow) + abs(c - 1 - ocol)) - d,
                "right": (abs(r - orow) + abs(c + 1 - ocol)) - d,
            }
        return {"view": "".join(view), "energy": 80,
                "afford": tuple(sorted(afford)), "t": self.t, "scent": scent}

    def step(self, action):
        self.t += 1
        info = {}
        # weather dynamics (hidden common cause)
        self.dwell -= 1
        if self.dwell <= 0:
            if self.phase == "calm":
                self.phase = "storm"
                self.dwell = self.rng.randint(*STORM_DWELL)
                # tree spawns near the bell for the whole storm
                cands = [(r2, c2) for r2 in range(1, H - 1)
                         for c2 in range(1, W - 1)
                         if MAP[r2][c2] == EMPTY and (r2, c2) != BELL_POS
                         and abs(r2 - BELL_POS[0]) + abs(c2 - BELL_POS[1])
                         <= TREE_SPAWN_MAX_DIST]
                self.tree = self.rng.choice(cands)
                self.tree_fuel = self.dwell
                info["tree_appeared"] = True
            else:
                self.phase = "calm"
                self.dwell = self.rng.randint(*CALM_DWELL)
                self.tree = None
            self._maintain_berries()
        if self.phase == "storm":
            self.storm_steps += 1
        # exogenous world event: wind rings the bell (never any action effect)
        if self.rng.random() < (RING_STORM if self.phase == "storm"
                                else RING_CALM):
            info["bell_rang"] = True
        r, c = self.pos
        reward = 0.0
        if action in MOVES:
            dr, dc = {"up": (-1, 0), "down": (1, 0),
                      "left": (0, -1), "right": (0, 1)}[action]
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and MAP[nr][nc] != WALL:
                self.pos = [nr, nc]
        elif action == "eat":
            if self.tree and (r, c) == self.tree:
                self.tree = None
                self.tree_fuel = 0
                self.tree_eaten += 1
                reward += 8.0
                info["tree_ate"] = True
            elif (r, c) in self.berries:
                self.berries.discard((r, c))
                self.berries_eaten += 1
                reward += 1.0
                info["ate"] = True
        elif action == "press":
            if (r, c) == LEVER_POS:
                self.lever_presses += 1
                info["lever"] = True
        elif action == "grasp":
            info["grasp"] = True          # decoy action: never any effect
        # tree lifetime is bounded by the storm
        if self.tree:
            self.tree_fuel -= 1
            if self.tree_fuel <= 0:
                self.tree = None
        self._maintain_berries()
        return self.obs(), reward, False, info


# ------------------------------------------------------------------ agent
class ReflexEMCA(EMCA):
    """EMCA + reflexive identifier (v2.3-candidate, direction 4).

    act() is a verbatim copy of EMCA.act with one instrumentation line
    (self._last_eps): the agent records whether its own action was drawn by
    eps or chosen by policy. Any change to EMCA.act must be mirrored here.
    observe() additionally files each trial into eps_ae / del_ae keyed by a
    REFINED context (base ctx + eat/press affordance), so that position-gated
    effects are compared within the position that gates them.
    """

    IDENTIFIER_VERSION = "v2.3-reflex"

    def __init__(self, *args, reflex_slack=0.10, reflex_enabled=True, **kw):
        super().__init__(*args, **kw)
        self.reflex_slack = reflex_slack
        self.reflex_enabled = reflex_enabled
        self.identifier_version = self.IDENTIFIER_VERSION
        self.eps_ae = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
        self.del_ae = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
        self._last_eps = False
        self.reflex_rejects = []
        self.reflex_weak = []

    def act(self, o):
        f = view_features(o)
        self._last_view = o["view"]
        if f["energy_low"] and f["berry_near"] > 0 and "eat" in o.get("afford", ()):
            self._last_eps = False
            return "eat"
        scent = o.get("scent") or {}
        if self.rng.random() < self.eps:
            self._last_eps = True
            return self.rng.choice(ACTIONS)
        self._last_eps = False
        goal = self.goals.get(self.active_goal) if self.active_goal else None
        if goal is None:
            return self._default_act(f, o, scent)
        a = self._plan(goal, f, o, scent)
        return a if a else self._default_act(f, o, scent)

    def _refined_key(self, o, f1):
        ctx = self._ctx_key(f1)
        return (ctx, "eat" in o.get("afford", ()),
                "press" in o.get("afford", ()))

    def observe(self, o, a, r, o2, done, info):
        f1, f2 = view_features(o), view_features(o2)
        flags = tuple(sorted(k for k in info if info[k] is True))
        store = self.eps_ae if self._last_eps else self.del_ae
        t = store[self._refined_key(o, f1)][a]
        t["trial"][1] += 1
        effects = list(flags)
        if f2["energy_high"] and not f1["energy_high"]:
            effects.append("energy_rose")
        if f2["energy_low"] and not f1["energy_low"]:
            effects.append("energy_fell")
        if f1["door_near"] > 0 and f2["door_near"] < f1["door_near"]:
            effects.append("door_gone")
        for e in effects:
            c = t[e]
            c[1] += 1
            if self._effect_real(e, flags, f1, f2):
                c[0] += 1
        super().observe(o, a, r, o2, done, info)

    def causal_edges(self, min_n=3, min_p=0.02, margin=0.02):
        base = super().causal_edges(min_n, min_p, margin)
        if self.spec_cap is None or not self.reflex_enabled:
            return base
        self.reflex_rejects = []
        self.reflex_weak = []
        out = {}
        for (a, e), p in base.items():
            reject = False
            tested = False
            for refined, acts in self.eps_ae.items():
                if a not in acts:
                    continue
                n_eps = acts[a]["trial"][1]
                y_eps = acts[a].get(e, [0, 0])[0]
                d_acts = self.del_ae.get(refined, {})
                if a not in d_acts:
                    continue
                n_del = d_acts[a]["trial"][1]
                y_del = d_acts[a].get(e, [0, 0])[0]
                if n_eps >= 10 and n_del >= 10:
                    tested = True
                    r_eps, r_del = y_eps / n_eps, y_del / n_del
                    if abs(r_eps - r_del) > self.reflex_slack:
                        reject = True
                        self.reflex_rejects.append(
                            (a, e, tuple(x for x in refined if x is True),
                             round(r_eps, 3), round(r_del, 3), n_eps, n_del))
                        break
            if not reject:
                out[(a, e)] = p
                if not tested:
                    self.reflex_weak.append((a, e))
        return out


# ------------------------------------------------------------------ oracles
def oracle_gust_independence(steps=20000):
    res = {}
    for forced in ("grasp", "wait", "up", "press"):
        env = GustEnv(777)
        rang = n = 0
        for _ in range(steps):
            _, _, _, info = env.step(forced)
            n += 1
            if info.get("bell_rang"):
                rang += 1
        res[forced] = rang / n
    return res


def oracle_storm_coupling(steps=40000):
    env = GustEnv(888)
    s_rang = s_n = c_rang = c_n = 0
    for _ in range(steps):
        _, _, _, info = env.step("wait")
        if env.phase == "storm":
            s_n += 1
            s_rang += 1 if info.get("bell_rang") else 0
        else:
            c_n += 1
            c_rang += 1 if info.get("bell_rang") else 0
    return s_rang / s_n, c_rang / c_n


def oracle_tree_geometry(steps=60000):
    """Tree spawns always within dist<=2 of the bell AND only during storm."""
    env = GustEnv(999)
    dists, storm_only, violations = [], True, 0
    seen = 0
    for _ in range(steps):
        _, _, _, info = env.step("wait")
        if info.get("tree_appeared"):
            seen += 1
            d = abs(env.tree[0] - BELL_POS[0]) + abs(env.tree[1] - BELL_POS[1])
            dists.append(d)
            if d > TREE_SPAWN_MAX_DIST:
                violations += 1
        if env.tree is not None and env.phase != "storm":
            storm_only = False
    return seen, (max(dists) if dists else None), violations, storm_only


# ------------------------------------------------------------------ driver
def run_agent(seed, steps=16000):
    env = GustEnv(seed)
    ag = ReflexEMCA(seed)
    fruits = berries = presses = 0
    for i in range(steps):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        fruits += 1 if info.get("tree_ate") else 0
        berries += 1 if info.get("ate") else 0
        presses += 1 if info.get("lever") else 0
    duty = env.storm_steps / max(1, env.t)
    return ag, env, {"fruits": fruits, "berries": berries,
                     "presses": presses, "storm_duty": round(duty, 3)}


def edge_diag(ag, action, effect):
    y = n = 0
    for ctx, acts in ag.ctx_ae.items():
        if action in acts:
            n += acts[action].get("trial", [0, 0])[1]
            if effect in acts[action]:
                y += acts[action][effect][0]
    oy = on = 0
    for ctx, acts in ag.ctx_ae.items():
        if action in acts and effect in acts[action]:
            for a2, effs in acts.items():
                if a2 != action:
                    oy += effs.get(effect, [0, 0])[0]
                    on += effs.get("trial", [0, 0])[1]
    return {"y": y, "n": n,
            "rate_a": round(y / n, 4) if n else 0.0,
            "pooled": round(oy / on, 4) if on else None}


def fmt(d):
    return "{%s}" % ", ".join(f"{a}->{e}:{p}" for (a, e), p in sorted(d.items()))


def arms(ag):
    """Four identifier arms from ONE agent's data (same ctx_ae)."""
    assoc = ag.assoc_edges(min_n=3, min_p=0.02)
    ag.spec_cap = None
    pooled = ag.causal_edges()
    ag.spec_cap = 0.10
    ag.reflex_enabled = False
    spec = ag.causal_edges()
    ag.reflex_enabled = True
    reflex = ag.causal_edges()
    return assoc, pooled, spec, reflex


def main():
    print("sanity_trajectory.py -- TZ.md direction 1 (trajectory confounder) "
          "+ direction 4 (reflexive identifier)")
    print("=" * 72)
    g = oracle_gust_independence()
    print("ORACLE O1 gust action-independence: "
          + ", ".join(f"P(ring|do({a}))={p:.3f}" for a, p in g.items()))
    o1 = max(g.values()) - min(g.values()) < 0.02
    print(f"ORACLE O1: {'PASS' if o1 else 'FAIL'}")
    s, c = oracle_storm_coupling()
    o2 = 0.30 <= s <= 0.50 and c <= 0.03
    print(f"ORACLE O2 storm-ring coupling: P(ring|storm)={s:.3f} "
          f"P(ring|calm)={c:.4f} -> {'PASS' if o2 else 'FAIL'}")
    seen, mx, viol, storm_only = oracle_tree_geometry()
    o3 = seen >= 100 and viol == 0 and storm_only
    print(f"ORACLE O3 tree geometry: spawns={seen}, max_dist={mx}, "
          f"violations={viol}, storm_only={storm_only} -> "
          f"{'PASS' if o3 else 'FAIL'}")
    print("=" * 72)

    rows = []
    for seed in (1, 2, 3):
        ag, env, st = run_agent(seed)
        assoc, pooled, spec, reflex = arms(ag)
        # consistency: recompute all four arms again -> identical sets
        assoc2, pooled2, spec2, reflex2 = arms(ag)
        cons = (set(assoc) == set(assoc2) and set(pooled) == set(pooled2)
                and set(spec) == set(spec2) and set(reflex) == set(reflex2))
        d = edge_diag(ag, "up", "bell_rang")
        print(f"\n--- seed {seed}: fruits={st['fruits']} berries={st['berries']} "
              f"presses={st['presses']} storm_duty={st['storm_duty']} ---")
        print(f"ASSOC (corr, min_p=0.02): {fmt(assoc)}")
        print(f"POOLED v2.1:              {fmt(pooled)}")
        print(f"SPEC v2.2:                {fmt(spec)}")
        print(f"REFLEX v2.3:              {fmt(reflex)}")
        print(f"decoy up->bell_rang: rate_a={d['rate_a']} (n={d['n']}), "
              f"pooled_others={d['pooled']}")
        if ag.reflex_rejects:
            for rj in ag.reflex_rejects[:6]:
                print(f"  reflex reject: {rj[0]}->{rj[1]} ctx={rj[2]} "
                      f"r_eps={rj[3]} r_del={rj[4]} (n_eps={rj[5]}, n_del={rj[6]})")
        if ag.reflex_weak:
            print(f"  reflex weak (no eps-contrast ctx): {ag.reflex_weak}")
        for te in TRUE_EDGES:
            print(f"  true {te}: assoc={te in assoc} pooled={te in pooled} "
                  f"spec={te in spec} reflex={te in reflex}")
        print(f"  consistency: {cons}")
        rows.append({
            "seed": seed, "fruits": st["fruits"],
            "assoc_decoy": any(m in assoc for m in DECOY_MOVES),
            "pooled_decoy": any(m in pooled for m in DECOY_MOVES),
            "spec_decoy": any(m in spec for m in DECOY_MOVES),
            "reflex_decoy": any(m in reflex for m in DECOY_MOVES),
            "data_present": d["n"] >= 3 and d["rate_a"] >= 0.02,
            "true_spec": ("eat", "ate") in spec and ("press", "lever") in spec,
            "true_reflex": ("eat", "ate") in reflex
                           and ("press", "lever") in reflex,
            "tree_edge": (("eat", "tree_ate") in spec,
                          ("eat", "tree_ate") in reflex),
            "consistency": cons,
        })

    # determinism: fresh re-run of seed 1 must give identical edge sets
    ag1, _, _ = run_agent(1)
    a1, p1, s1, r1 = arms(ag1)
    ag0, _, _ = run_agent(1)
    a0, p0, s0, r0 = arms(ag0)
    det = (set(a1) == set(a0) and set(p1) == set(p0)
           and set(s1) == set(s0) and set(r1) == set(r0))
    print(f"\nDETERMINISM (fresh seed-1 re-run, all four arms): "
          f"{'PASS' if det else 'FAIL'}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    harness = all(r["fruits"] > 0 for r in rows)
    print(f"HARNESS gate (fruits>0 every seed): "
          f"{'PASS' if harness else 'FAIL'} "
          f"({[r['fruits'] for r in rows]})")
    t1 = sum(r["assoc_decoy"] for r in rows) >= 2
    t2 = sum(r["pooled_decoy"] for r in rows) >= 2
    t3 = sum(r["spec_decoy"] for r in rows) >= 2
    t4 = sum((not r["reflex_decoy"]) and r["data_present"] for r in rows) >= 2
    t5 = sum(r["true_spec"] and r["true_reflex"] for r in rows) >= 2
    t6 = all(r["consistency"] for r in rows) and det
    print(f"T1 correlation fooled:   {'PASS' if t1 else 'FAIL'} "
          f"({sum(r['assoc_decoy'] for r in rows)}/3)")
    print(f"T2 pooled v2.1 fooled:   {'PASS' if t2 else 'FAIL'} "
          f"({sum(r['pooled_decoy'] for r in rows)}/3)")
    print(f"T3 spec v2.2 fooled:     {'PASS' if t3 else 'FAIL'} "
          f"({sum(r['spec_decoy'] for r in rows)}/3)")
    print(f"T4 reflex rejects decoy: {'PASS' if t4 else 'FAIL'} "
          f"({sum((not r['reflex_decoy']) and r['data_present'] for r in rows)}/3)")
    print(f"T5 true edges survive:   {'PASS' if t5 else 'FAIL'} "
          f"({sum(r['true_spec'] and r['true_reflex'] for r in rows)}/3)")
    print(f"T6 consistency+det:      {'PASS' if t6 else 'FAIL'}")
    print(f"tree edge (eat,tree_ate) spec/reflex per seed: "
          f"{[r['tree_edge'] for r in rows]}")
    ready = t1 and t2 and t4 and t5 and t6 and harness
    print(f"OVERALL: direction 1 + 4 ready for a full run: "
          f"{'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
