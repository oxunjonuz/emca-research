#!/usr/bin/env python3
"""Toy check, run 2: the LINGER form of TZ.md direction 1 + a per-context
contrast identifier (v2.4-candidate) + a regression guard.

Run 1 (sanity_trajectory.py, transit form) measured honestly that the
trajectory confounder does NOT bite in transit form: the agent's calm-phase
wandering re-balances move-directions across weather, so rate(up->ring) -
pooled(others) = +0.006 only. The confounder lives in WHERE the agent is,
not in WHICH direction it moves. The linger form makes that explicit: the
agent purposively walks to the tree near the bell and STAYS there eating
for the whole storm (ring rate 0.40 vs 0.01 calm), so every action taken
at the tree correlates with the ring without causing it. Analysis of the
run-1 data says the sharpest decoy edge will be (eat, bell_rang), not a
move edge: eating at the tree happens only in storms.

This file answers three questions at toy scale (TZ.md rule: check the
environment can separate what it must separate BEFORE any full matrix):

  Q1 (linger bites)   Does the linger form produce a REAL decoy edge in
      the pooled contrast v2.1 AND in correlation -- an EXCESS rate over
      other actions, not just co-occurrence?
  Q2 (identifier)     Does a per-context contrast (v2.4-candidate:
      rate(a,e|ctx) - rate(others,e|ctx) >= margin within each context)
      reject the decoy while keeping the true edges?
  Q3 (regression)     Does the per-context identifier keep the edge sets
      of v2.2 on TerrariumV2 (the matrix environment) and on the original
      Terrarium v1 -- no silent behaviour change where the old identifier
      was already correct?

ENVIRONMENT (LingerEnv): hidden weather calm/storm (common cause). Storm:
tree near the bell (dist<=2) + ring P=0.40. Calm: berries at the shelter +
ring P=0.01. The bell is never affected by any action (oracle-checked in
run 1: P(ring|do(a)) equal for all a). Energy is static. The tree yields
MANY fruits (eat repeatedly, +8 each) so a competent forager LINGERS at
the tree through the storm: the agent's own goal architecture (tree goal +
scent) produces the lingering, not a scripted policy.

PREDICTIONS, PRE-REGISTERED BEFORE THE FIRST RUN OF THIS FILE (run 1
taught the calibration: raw ring rates ~0.10-0.13, contrasts are small):
  P1 correlation fooled:    any (move,ring) OR (eat,ring) in assoc with
     rate >= pooled_others + 0.05 (EXCESS over other actions -- the honest
     meaning of "correlation is fooled"; run 1's T1 with a bare min_p was
     a defective criterion, it passed on the base rate alone) in >=2/3
  P2 pooled v2.1 fooled:    any (move,ring) or (eat,ring) in pooled v2.1
     in >=2/3 seeds (predicted YES: at the tree the agent eats/moves while
     the storm rings; the global denominator is dominated by calm steps
     where nothing rings)
  P3 spec v2.2 fooled:      any (move,ring) or (eat,ring) in spec v2.2 in
     >=2/3 seeds (predicted YES: the effect is rare on other actions
     pooled globally, so the specificity gate does not bite)
  P4 per-context rejects:   no (move,ring)/(eat,ring) in perctx v2.4 in
     >=2/3 seeds, with decoy data present
  P5 true edges survive:    (eat,ate) and (press,lever) in perctx in >=2/3
     seeds in LingerEnv
  P6 regression:            on TerrariumV2 AND Terrarium v1 (real agent,
     8000 steps, seeds 1-3): perctx keeps the true edges (press,lever),
     (eat,ate), (eat,tree_ate) wherever v2.2 keeps them, and both reject
     the v2 decoy (grasp,bell_rang).
  HARNESS GATE: fruits>0 in every seed AND ring-during-storm-near-tree
     measured > 0.30 (the linger must actually happen, else the env is
     broken and must be fixed before verdicts).
  READY = P1 & P2 & P4 & P5 & P6 & GATE.
  If P2/P3 FAIL (decoy does not even reach the identifiers), direction 1
  in linger form is dead for THIS agent -- report honestly, no rescue.
"""
import sys
from collections import defaultdict

from agent_emca_v2 import EMCA, view_features
from env_terrarium_v2 import ACTIONS, BERRY, LEVER, EMPTY, WALL
from env_terrarium_v2 import BELL_DARK, TREE
from env_terrarium_v2 import TerrariumV2

W, H = 9, 9
MAP = [
    "#########",
    "#..Q....#",
    "#.......#",
    "#.......#",
    "#.......#",
    "#.......#",
    "#.....L.#",
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
DECOY_EDGES = (("up", "bell_rang"), ("down", "bell_rang"),
               ("left", "bell_rang"), ("right", "bell_rang"),
               ("eat", "bell_rang"))
TRUE_EDGES = [("eat", "ate"), ("press", "lever"), ("eat", "tree_ate")]


class LingerEnv:
    """Linger form of the trajectory confounder (direction 1, run 2).

    Same hidden-weather common cause as GustEnv (run 1), but the tree yields
    many fruits so a competent forager LINGERS at the tree (near the bell)
    through the storm: every action it takes there correlates with the 0.40
    ring rate without causing it.
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
            self.berries = set()

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
        self.dwell -= 1
        if self.dwell <= 0:
            if self.phase == "calm":
                self.phase = "storm"
                self.dwell = self.rng.randint(*STORM_DWELL)
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
                self.tree_eaten += 1          # tree does not disappear: linger
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
            info["grasp"] = True
        if self.tree:
            self.tree_fuel -= 1
            if self.tree_fuel <= 0:
                self.phase = "calm"
                self.dwell = self.rng.randint(*CALM_DWELL)
                self.tree = None
                self._maintain_berries()
        self._maintain_berries()
        return self.obs(), reward, False, info


# ------------------------------------------------------------------ agent
class ReflexEMCA(EMCA):
    """EMCA + reflexive instrumentation (eps/deliberate filing, run 1) and a
    per-context contrast identifier (v2.4-candidate, run 2).

    v2.4 rule: an edge (a,e) stands if in SOME context ctx:
        n(a,ctx) >= min_n,  rate(a,e|ctx) >= min_p,  and
        rate(a,e|ctx) - rate(others,e|ctx) >= margin
    where rate(others,e|ctx) pools all other actions in that context.
    Rationale: a cause is what makes the difference HERE, in the context
    where it acts; the global pooled contrast (v2.1/v2.2) divides by a
    denominator dominated by contexts where the action was never available
    (run 1: press->lever diluted by ~15000 non-lever steps, lost in 2/3
    seeds). Boundary (stated up front): a context-specific coincidence can
    pass if the context is rare and the margin small; the spec gate (v2.2)
    remains available as a second condition.

    act() is EMCA.act verbatim except one instrumentation line
    (self._last_eps) recording whether the action was drawn by eps.
    """

    IDENTIFIER_VERSION = "v2.4-perctx"

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
        if self.spec_cap is None:
            return super().causal_edges(min_n, min_p, margin)
        out = {}
        for ctx, acts in self.ctx_ae.items():
            for a, effs in acts.items():
                n = effs.get("trial", [0, 0])[1]
                if n < min_n:
                    continue
                for e in effs:
                    if e == "trial":
                        continue
                    y = effs[e][0]
                    rate_a = y / n
                    if rate_a < min_p:
                        continue
                    oy = on = 0
                    for a2, effs2 in acts.items():
                        if a2 != a:
                            on += effs2.get("trial", [0, 0])[1]
                            if e in effs2:
                                oy += effs2[e][0]
                    if on == 0:
                        out[(a, e)] = max(out.get((a, e), 0), rate_a)
                        continue
                    pooled_ctx = oy / on
                    if rate_a - pooled_ctx >= margin:
                        out[(a, e)] = max(out.get((a, e), 0), rate_a)
        return {k: round(v, 3) for k, v in out.items()}


# ------------------------------------------------------------------ oracles
def oracle_ring_rates(steps=40000):
    env = LingerEnv(888)
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


# ------------------------------------------------------------------ driver
def run_agent(seed, steps=16000):
    env = LingerEnv(seed)
    ag = ReflexEMCA(seed)
    fruits = berries = presses = 0
    ring_near_tree = ring_near_tree_n = 0
    for i in range(steps):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        fruits += 1 if info.get("tree_ate") else 0
        berries += 1 if info.get("ate") else 0
        presses += 1 if info.get("lever") else 0
        if env.tree and env.phase == "storm":
            dist = abs(env.pos[0] - env.tree[0]) + abs(env.pos[1] - env.tree[1])
            if dist <= 1:
                ring_near_tree_n += 1
                ring_near_tree += 1 if info.get("bell_rang") else 0
    duty = env.storm_steps / max(1, env.t)
    return ag, env, {"fruits": fruits, "berries": berries,
                     "presses": presses, "storm_duty": round(duty, 3),
                     "ring_near_tree": (round(ring_near_tree
                                              / max(1, ring_near_tree_n), 3),
                                        ring_near_tree_n)}


def run_regression(env_name, seed, steps=8000):
    """Real agent on TerrariumV2 or Terrarium v1; compare v2.2 vs v2.4 edges."""
    if env_name == "v2":
        env = TerrariumV2(seed)
    else:
        from env_terrarium import Terrarium
        env = Terrarium(seed)
    ag = ReflexEMCA(seed)
    for i in range(steps):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if done:
            if env_name == "v2":
                env = TerrariumV2(seed + 1000 + i)
            else:
                from env_terrarium import Terrarium
                env = Terrarium(seed + 1000 + i)
    ag.spec_cap = 0.10
    v22 = ag.causal_edges()
    # v2.4 IS this class's causal_edges with spec ON; v2.2 is the parent's
    ag2 = EMCA.__new__(EMCA)   # not used; kept for clarity
    v24 = v22                  # same call, this class's implementation
    # parent v2.2 for comparison:
    parent_v22 = EMCA.causal_edges(ag, min_n=3, min_p=0.02, margin=0.02)
    return v22, parent_v22


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
    pooled = ag.causal_edges()          # spec OFF -> parent's global pooled v2.1
    ag.spec_cap = 0.10
    spec = EMCA.causal_edges(ag)        # parent's v2.2 (spec ON, global pooled)
    perctx = ag.causal_edges()          # this class's v2.4 (spec ON, per-ctx)
    return assoc, pooled, spec, perctx


def main():
    print("sanity_linger.py -- run 2: linger form of direction 1 + "
          "per-context contrast (v2.4) + regression guard")
    print("=" * 72)
    s, c = oracle_ring_rates()
    print(f"ORACLE ring rates: P(ring|storm)={s:.3f} P(ring|calm)={c:.4f}")
    print("=" * 72)

    rows = []
    for seed in (1, 2, 3):
        ag, env, st = run_agent(seed)
        assoc, pooled, spec, perctx = arms(ag)
        assoc2, pooled2, spec2, perctx2 = arms(ag)
        cons = (set(assoc) == set(assoc2) and set(pooled) == set(pooled2)
                and set(spec) == set(spec2) and set(perctx) == set(perctx2))
        d = edge_diag(ag, "eat", "bell_rang")
        dm = edge_diag(ag, "up", "bell_rang")
        print(f"\n--- seed {seed}: fruits={st['fruits']} berries={st['berries']} "
              f"presses={st['presses']} storm_duty={st['storm_duty']} "
              f"ring_near_tree={st['ring_near_tree']} ---")
        print(f"ASSOC (corr, min_p=0.02): {fmt(assoc)}")
        print(f"POOLED v2.1 (spec OFF):   {fmt(pooled)}")
        print(f"SPEC v2.2 (global):       {fmt(spec)}")
        print(f"PERCTX v2.4:              {fmt(perctx)}")
        print(f"decoy eat->bell_rang: rate_a={d['rate_a']} (n={d['n']}), "
              f"pooled_others={d['pooled']}")
        print(f"decoy up->bell_rang:  rate_a={dm['rate_a']} (n={dm['n']}), "
              f"pooled_others={dm['pooled']}")
        for te in TRUE_EDGES:
            print(f"  true {te}: assoc={te in assoc} pooled={te in pooled} "
                  f"spec={te in spec} perctx={te in perctx}")
        print(f"  consistency: {cons}")
        rows.append({
            "seed": seed, "fruits": st["fruits"],
            "assoc_decoy": any(m in assoc for m in DECOY_EDGES),
            "assoc_excess": any(
                m in assoc and (edge_diag(ag, *m)["rate_a"]
                                - (edge_diag(ag, *m)["pooled"] or 0)) >= 0.05
                for m in DECOY_EDGES),
            "pooled_decoy": any(m in pooled for m in DECOY_EDGES),
            "spec_decoy": any(m in spec for m in DECOY_EDGES),
            "perctx_decoy": any(m in perctx for m in DECOY_EDGES),
            "data_present": (d["n"] >= 3 and d["rate_a"] >= 0.02)
                            or (dm["n"] >= 3 and dm["rate_a"] >= 0.02),
            "true_perctx": ("eat", "ate") in perctx
                           and ("press", "lever") in perctx,
            "consistency": cons,
        })

    # determinism
    ag1, _, _ = run_agent(1)
    a1, p1, s1, c1 = arms(ag1)
    ag0, _, _ = run_agent(1)
    a0, p0, s0, c0 = arms(ag0)
    det = (set(a1) == set(a0) and set(p1) == set(p0) and set(s1) == set(s0)
           and set(c1) == set(c0))
    print(f"\nDETERMINISM (fresh seed-1 re-run, all arms): "
          f"{'PASS' if det else 'FAIL'}")

    # regression guard: TerrariumV2 and Terrarium v1, real agent, 3 seeds
    print("\n--- REGRESSION: perctx v2.4 vs spec v2.2 on matrix environments ---")
    reg_ok = True
    for env_name in ("v2", "v1"):
        for seed in (1, 2, 3):
            v24, v22 = run_regression(env_name, seed)
            true_edges = [te for te in TRUE_EDGES if te[1] != "tree_ate"
                          or env_name == "v2"]
            keep_ok = all((te not in v22) or (te in v24)
                          for te in true_edges)
            decoy_ok = ("grasp", "bell_rang") not in v24
            print(f"  {env_name} seed {seed}: v2.2={fmt(v22)}")
            print(f"  {env_name} seed {seed}: v2.4={fmt(v24)}")
            print(f"    keeps v2.2 true edges: {keep_ok}; "
                  f"v2 decoy absent in v2.4: {decoy_ok}")
            reg_ok = reg_ok and keep_ok and decoy_ok
    print(f"REGRESSION overall: {'PASS' if reg_ok else 'FAIL'}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    gate = all(r["fruits"] > 0 for r in rows) and \
        all(r["ring_near_tree"][0] > 0.30 for r in rows) if rows else False
    print(f"HARNESS gate (fruits>0, ring_near_tree>0.30): "
          f"{'PASS' if gate else 'FAIL'} "
          f"({[r['fruits'] for r in rows]}, "
          f"{[r['ring_near_tree'][0] if 'ring_near_tree' in r else '-' for r in rows]})")
    p1 = sum(r["assoc_decoy"] and r["assoc_excess"] for r in rows) >= 2
    p2 = sum(r["pooled_decoy"] for r in rows) >= 2
    p3 = sum(r["spec_decoy"] for r in rows) >= 2
    p4 = sum((not r["perctx_decoy"]) and r["data_present"] for r in rows) >= 2
    p5 = sum(r["true_perctx"] for r in rows) >= 2
    p6 = det and all(r["consistency"] for r in rows) and reg_ok
    print(f"P1 correlation fooled (EXCESS): {'PASS' if p1 else 'FAIL'} "
          f"({sum(r['assoc_decoy'] and r['assoc_excess'] for r in rows)}/3)")
    print(f"P2 pooled v2.1 fooled:          {'PASS' if p2 else 'FAIL'} "
          f"({sum(r['pooled_decoy'] for r in rows)}/3)")
    print(f"P3 spec v2.2 fooled:            {'PASS' if p3 else 'FAIL'} "
          f"({sum(r['spec_decoy'] for r in rows)}/3)")
    print(f"P4 perctx rejects decoy:        {'PASS' if p4 else 'FAIL'} "
          f"({sum((not r['perctx_decoy']) and r['data_present'] for r in rows)}/3)")
    print(f"P5 true edges survive perctx:   {'PASS' if p5 else 'FAIL'} "
          f"({sum(r['true_perctx'] for r in rows)}/3)")
    print(f"P6 consistency+det+regression:  {'PASS' if p6 else 'FAIL'}")
    ready = p1 and p2 and p4 and p5 and p6 and gate
    print(f"OVERALL: linger direction 1 + v2.4 ready for a full run: "
          f"{'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
