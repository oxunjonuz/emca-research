#!/usr/bin/env python3
"""Run 3: does the REFLEXIVE identifier (direction 4, v2.3-candidate) reject
the linger decoy that defeated v2.1 and v2.2? Plus a fixed per-context arm
(v2.4b) as control, and a regression guard on the matrix environments.

Run 2 (sanity_linger.py) measured, from its printed per-seed tables:
  * the linger form of TZ.md direction 1 BITES the real agent: decoy
    (eat, bell_rang) accepted by pooled v2.1 in 3/3 seeds (rate 0.26-0.27
    vs pooled_others 0.09) and by the spec gate v2.2 in 2/3 seeds. The
    agent's own tree-goal makes it linger at the bell through storms
    (fruits 1105-1208 per 16k steps; ring rate near the tree 0.39-0.40).
  * per-context contrast v2.4 (margin 0.02) did NOT reject the decoy
    (1/3) and, on TerrariumV2, flooded junk edges (down->bell_rang 1.0,
    left->door_gone 1.0, up->died 0.333...): the on==0 branch accepted
    edges without any contrast whenever a rare context had one action
    tried, and the door_gone effect conflates "the door opened" with "I
    walked away" (a view-motion artifact, the v1 lesson).
  * run 2's script crashed at its own verdict block (KeyError) and the
    pipe masked the exit code; its verdicts above were derived by hand
    from the printed raw tables. This file re-derives them independently.

THE REFLEXIVE IDENTIFIER (direction 4, proposed by the agent, not TZ.md):
  an edge (a,e) accepted by v2.2 stands only if the effect rate is the
  same whether the agent took `a` DELIBERATELY (policy) or by its OWN EPS
  (random exploration) -- within the same refined context (base ctx +
  affordance flags). A true cause does not care why you acted; a
  trajectory confounder lives in the deliberation. eps is the agent's own
  built-in randomized trial: the nuisance that saved v2 (RESULTS_V2.md
  negative result 1) turned into the instrument.

PRE-REGISTERED PREDICTIONS (before the first run of this file; calibrated
by run 1/run 2 data):
  R1 replication:  decoy (eat,bell_rang) in pooled v2.1 in >=2/3 seeds
     (run 2: 3/3, rate ~0.27 vs others ~0.09)
  R2 replication:  decoy in spec v2.2 in >=2/3 seeds (run 2: 2/3)
  R3 MAIN:         reflex rejects the decoy in >=2/3 seeds, decoy data
     present. Predicted mechanism: rate(eat->ring | eps-eat) ~ 0.10
     (eps-eats are spread over all positions and phases) vs
     rate(eat->ring | deliberate-eat) ~ 0.30 (deliberate eats concentrate
     at the storm tree) -> gap > slack 0.10 -> rejected.
  R4 reflex keeps true edges: (eat,ate) and (press,lever) in reflex in
     >=2/3 seeds (predicted: eps-eat and deliberate-eat both ~1.0 for
     ate; presses mostly eps -> edge kept as 'weak' if n_del<10, which is
     the conservative direction for true edges and is REPORTED, not hidden)
  R5 control arm v2.4b (per-ctx, margin 0.10, others n>=min_n required,
     no unconditional on==0 accept): rejects decoy >=2/3 AND keeps true
     edges >=2/3 (informative either way)
  R6 regression on TerrariumV2 AND Terrarium v1 (real agent, 8000 steps,
     seeds 1-3): reflex keeps every true edge v2.2 keeps; reflex accepts
     NO world-event edges (bell_rang/tree_appeared/key_appeared) and no
     view-artifact door_gone; v2.4b likewise
  R7 determinism + arm consistency
  READY (for a v3 full run) = R1 & R2 & R3 & R4 & R6 & R7.
  If R3 FAILS, direction 4 is dead as instrumented -- report honestly.

Harness fixes carried from run 2: verdicts computed inside the script from
the same rows it prints; exit code captured without a masking pipe; the
door_gone view-artifact is fixed in this file's agent (door_gone counts
only when the action was NOT a move -- walking away must not "cause" the
door to leave the view; the door-opening effect of the lever is preserved
because pressing is not a move).
"""
import sys
from collections import defaultdict

from agent_emca_v2 import EMCA, view_features
from env_terrarium_v2 import ACTIONS
from env_terrarium_v2 import TerrariumV2
from sanity_linger import LingerEnv, edge_diag, fmt, TRUE_EDGES, DECOY_EDGES

MOVES = ("up", "down", "left", "right")


class AgentV23(EMCA):
    """EMCA + reflexive identifier (v2.3-candidate) + door_gone artifact fix.

    act() is EMCA.act verbatim except one instrumentation line
    (self._last_eps). observe() is ReflexEMCA.observe (run 2) with the
    door_gone fix: door_gone is filed only when the action was not a move.
    causal_edges() dispatches by self.identifier_mode:
      "v22"    -> parent EMCA.causal_edges (global pooled + spec gate)
      "reflex" -> v22 base + eps/deliberate contrast gate (slack, n>=10)
      "v24b"   -> per-context contrast, margin 0.10, others n >= min_n
    """

    IDENTIFIER_VERSION = "v2.3-reflex"

    def __init__(self, *args, reflex_slack=0.10, identifier_mode="reflex",
                 **kw):
        super().__init__(*args, **kw)
        self.reflex_slack = reflex_slack
        self.identifier_mode = identifier_mode
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
        # door_gone artifact fix (run-2 lesson): only when NOT moving --
        # walking away must not "cause" the door to leave the 3x3 view
        if a not in MOVES and f1["door_near"] > 0 and f2["door_near"] < f1["door_near"]:
            effects.append("door_gone")
        for e in effects:
            c = t[e]
            c[1] += 1
            if self._effect_real(e, flags, f1, f2):
                c[0] += 1
        super().observe(o, a, r, o2, done, info)

    def causal_edges(self, min_n=3, min_p=0.02, margin=0.02):
        if self.identifier_mode == "v24b":
            out = {}
            for ctx, acts in self.ctx_ae.items():
                for a, effs in acts.items():
                    n = effs.get("trial", [0, 0])[1]
                    if n < min_n:
                        continue
                    # others in THIS context must also have data
                    on = sum(effs2.get("trial", [0, 0])[1]
                             for a2, effs2 in acts.items() if a2 != a)
                    if on < min_n:
                        continue
                    for e in effs:
                        if e == "trial":
                            continue
                        y = effs[e][0]
                        rate_a = y / n
                        if rate_a < min_p:
                            continue
                        oy = sum(effs2[e][0] for a2, effs2 in acts.items()
                                 if a2 != a and e in effs2)
                        pooled_ctx = oy / on
                        if rate_a - pooled_ctx >= 0.10:
                            out[(a, e)] = max(out.get((a, e), 0), rate_a)
            return {k: round(v, 3) for k, v in out.items()}
        base = super().causal_edges(min_n, min_p, margin)
        if self.identifier_mode != "reflex" or self.spec_cap is None:
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
                            (a, e, round(r_eps, 3), round(r_del, 3),
                             n_eps, n_del))
                        break
            if not reject:
                out[(a, e)] = p
                if not tested:
                    self.reflex_weak.append((a, e))
        return out


def run_agent(seed, steps=16000, env_cls=LingerEnv):
    env = env_cls(seed)
    ag = AgentV23(seed)
    fruits = berries = presses = 0
    for i in range(steps):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        fruits += 1 if info.get("tree_ate") else 0
        berries += 1 if info.get("ate") else 0
        presses += 1 if info.get("lever") else 0
        if done:
            env = env_cls(seed + 1000 + i)
    return ag, env, {"fruits": fruits, "berries": berries,
                     "presses": presses}


def arms(ag):
    """Five identifier arms from ONE agent's data (same ctx_ae)."""
    assoc = ag.assoc_edges(min_n=3, min_p=0.02)
    ag.spec_cap = None
    ag.identifier_mode = "v22"
    pooled = ag.causal_edges()               # global pooled, no spec gate
    ag.spec_cap = 0.10
    spec = ag.causal_edges()                 # v2.2 (global pooled + spec)
    ag.identifier_mode = "reflex"
    reflex = ag.causal_edges()               # v2.3 (v2.2 + eps/del gate)
    ag.identifier_mode = "v24b"
    perctxb = ag.causal_edges()              # per-ctx, margin 0.10
    return assoc, pooled, spec, reflex, perctxb


def regression(env_name, seed, steps=8000):
    if env_name == "v2":
        env = TerrariumV2(seed)
    else:
        from env_terrarium import Terrarium
        env = Terrarium(seed)
    ag = AgentV23(seed)
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
    _, _, spec, reflex, perctxb = arms(ag)
    return spec, reflex, perctxb


WORLD_EVENT_EFFECTS = ("bell_rang", "tree_appeared", "key_appeared")
ARTIFACT_EFFECTS = ("died", "door_gone")


def main():
    print("sanity_reflex.py -- run 3: reflexive identifier (direction 4) "
          "vs the linger decoy; v2.4b control; regression guard")
    print("=" * 72)
    rows = []
    for seed in (1, 2, 3):
        ag, env, st = run_agent(seed)
        assoc, pooled, spec, reflex, perctxb = arms(ag)
        a2, p2, s2, r2, c2 = arms(ag)
        cons = all(set(x) == set(y) for x, y in
                   ((assoc, a2), (pooled, p2), (spec, s2),
                    (reflex, r2), (perctxb, c2)))
        d = edge_diag(ag, "eat", "bell_rang")
        print(f"\n--- seed {seed}: fruits={st['fruits']} "
              f"berries={st['berries']} presses={st['presses']} ---")
        print(f"ASSOC (corr):     {fmt(assoc)}")
        print(f"POOLED v2.1:      {fmt(pooled)}")
        print(f"SPEC v2.2:        {fmt(spec)}")
        print(f"REFLEX v2.3:      {fmt(reflex)}")
        print(f"PERCTX v2.4b:     {fmt(perctxb)}")
        print(f"decoy eat->bell_rang: rate_a={d['rate_a']} (n={d['n']}), "
              f"pooled_others={d['pooled']}")
        if ag.reflex_rejects:
            for rj in ag.reflex_rejects[:8]:
                print(f"  reflex reject: {rj[0]}->{rj[1]} r_eps={rj[2]} "
                      f"r_del={rj[3]} (n_eps={rj[4]}, n_del={rj[5]})")
        if ag.reflex_weak:
            print(f"  reflex weak (kept, no eps-contrast ctx): "
                  f"{ag.reflex_weak}")
        for te in TRUE_EDGES:
            print(f"  true {te}: pooled={te in pooled} spec={te in spec} "
                  f"reflex={te in reflex} perctxb={te in perctxb}")
        print(f"  consistency: {cons}")
        rows.append({
            "seed": seed, "fruits": st["fruits"],
            "pooled_decoy": ("eat", "bell_rang") in pooled,
            "spec_decoy": ("eat", "bell_rang") in spec,
            "reflex_decoy": ("eat", "bell_rang") in reflex,
            "perctxb_decoy": ("eat", "bell_rang") in perctxb,
            "data_present": d["n"] >= 3 and d["rate_a"] >= 0.02,
            "true_reflex": ("eat", "ate") in reflex
                           and ("press", "lever") in reflex,
            "true_perctxb": ("eat", "ate") in perctxb
                            and ("press", "lever") in perctxb,
            "consistency": cons,
        })

    ag1, _, _ = run_agent(1)
    ar1 = arms(ag1)
    ag0, _, _ = run_agent(1)
    ar0 = arms(ag0)
    det = all(set(x) == set(y) for x, y in zip(ar1, ar0))
    print(f"\nDETERMINISM (fresh seed-1 re-run, five arms): "
          f"{'PASS' if det else 'FAIL'}")

    print("\n--- REGRESSION: TerrariumV2 + Terrarium v1 (real agent) ---")
    reg = {"reflex_keep": True, "reflex_clean": True,
           "perctxb_keep": True, "perctxb_clean": True}
    for env_name in ("v2", "v1"):
        for seed in (1, 2, 3):
            spec, reflex, perctxb = regression(env_name, seed)
            true_edges = [te for te in TRUE_EDGES
                          if env_name == "v2" or te[1] != "tree_ate"]
            keep_r = all((te not in spec) or (te in reflex)
                         for te in true_edges)
            keep_p = all((te not in spec) or (te in perctxb)
                         for te in true_edges)
            bad_r = [k for k in reflex if k[1] in WORLD_EVENT_EFFECTS
                     or k[1] in ARTIFACT_EFFECTS]
            bad_p = [k for k in perctxb if k[1] in WORLD_EVENT_EFFECTS
                     or k[1] in ARTIFACT_EFFECTS]
            print(f"  {env_name} seed {seed}:")
            print(f"    spec v2.2:   {fmt(spec)}")
            print(f"    reflex:      {fmt(reflex)}  keep={keep_r} "
                  f"bad={bad_r}")
            print(f"    perctxb:     {fmt(perctxb)}  keep={keep_p} "
                  f"bad={bad_p}")
            reg["reflex_keep"] &= keep_r
            reg["reflex_clean"] &= not bad_r
            reg["perctxb_keep"] &= keep_p
            reg["perctxb_clean"] &= not bad_p
    print(f"REGRESSION: reflex keep={reg['reflex_keep']} "
          f"clean={reg['reflex_clean']}; perctxb keep={reg['perctxb_keep']} "
          f"clean={reg['perctxb_clean']}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    r1 = sum(r["pooled_decoy"] for r in rows) >= 2
    r2 = sum(r["spec_decoy"] for r in rows) >= 2
    r3 = sum((not r["reflex_decoy"]) and r["data_present"] for r in rows) >= 2
    r4 = sum(r["true_reflex"] for r in rows) >= 2
    r5a = sum((not r["perctxb_decoy"]) and r["data_present"]
              for r in rows) >= 2
    r5b = sum(r["true_perctxb"] for r in rows) >= 2
    r6 = (reg["reflex_keep"] and reg["reflex_clean"])
    r7 = det and all(r["consistency"] for r in rows)
    print(f"R1 decoy in pooled v2.1 (replication):   "
          f"{'PASS' if r1 else 'FAIL'} "
          f"({sum(r['pooled_decoy'] for r in rows)}/3)")
    print(f"R2 decoy in spec v2.2 (replication):     "
          f"{'PASS' if r2 else 'FAIL'} "
          f"({sum(r['spec_decoy'] for r in rows)}/3)")
    print(f"R3 REFLEX rejects decoy (MAIN):          "
          f"{'PASS' if r3 else 'FAIL'} "
          f"({sum((not r['reflex_decoy']) and r['data_present'] for r in rows)}/3)")
    print(f"R4 reflex keeps true edges:              "
          f"{'PASS' if r4 else 'FAIL'} "
          f"({sum(r['true_reflex'] for r in rows)}/3)")
    print(f"R5 perctxb rejects decoy / keeps true:   "
          f"{'PASS' if r5a else 'FAIL'} / {'PASS' if r5b else 'FAIL'} "
          f"({sum((not r['perctxb_decoy']) and r['data_present'] for r in rows)}/3, "
          f"{sum(r['true_perctxb'] for r in rows)}/3)")
    print(f"R6 regression (reflex keep+clean):       "
          f"{'PASS' if r6 else 'FAIL'}")
    print(f"R7 determinism + consistency:            "
          f"{'PASS' if r7 else 'FAIL'}")
    ready = r1 and r2 and r3 and r4 and r6 and r7
    print(f"OVERALL: linger confounder + reflexive identifier ready for "
          f"a v3 full run: {'YES' if ready else 'NO'}")
    rc = 0 if ready else 1
    sys.exit(rc)


if __name__ == "__main__":
    main()
