#!/usr/bin/env python3
"""Run 5: the STRATIFIED contrast identifier (v2.5-candidate) vs the linger
decoy -- the principled fix suggested by run 4's audit.

Run 4 (sanity_reflex2.py, corrected denominators) measured with adequate n:
  * the raw eps/deliberate gap for (eat,bell_rang) is real and large
    (pooled 0.114 vs 0.340, gap 0.225) -- but the location audit shows the
    mechanism: AT THE TREE the ring rate is mode-INVARIANT (eps 0.420 vs
    deliberate 0.394-0.397, n=591/26371). The gap lives in WHERE/WHEN the
    agent eats, not in the eating. Run 3's 3/3 reflex rejection was
    small-sample noise amplified by the any-context-rejects rule.
  * true edges show the same raw gap (eat->ate: 0.030 vs 0.149) -- a raw
    mode-contrast gate would kill true edges too. Action-level eps
    randomisation has NO POWER against a location-coupled confounder.
    Direction 4 (as instrumented) is dead; the structural reason: the
    linger confounder is EXISTENTIAL (the tree exists only in storms), so
    every tree-visit is a storm-visit however motivated.

What run 4's audit ALSO shows: within the at-tree context OTHER actions
ring at the same ~0.40 rate. So a STRATIFIED contrast -- compare the
action's effect rate to the others' rate WITHIN each context, then average
with the action's own exposure weights (a Mantel-Haenszel-style common
contrast) -- should reject the decoy (contrast ~ 0.02 << margin) while
keeping true edges (press->lever: contrast 1.0 inside the lever context)
and without the small-context junk that flooded the max-over-contexts
variant (v2.4/v2.4b: press->bell_rang 0.833 from n=6 contexts).

PRE-REGISTERED CRITERIA (before the first run of this file):
  H1 replication: decoy (eat,bell_rang) in pooled v2.1 in >=2/3 seeds
     (third independent replication: runs 2, 3 measured 3/3)
  H2 replication: decoy in spec v2.2 in >=2/3 seeds (runs 2,3: 3/3, 2/3)
  H3 MAIN:        decoy NOT in stratified v2.5 in >=2/3 seeds, decoy data
     present (n>=3, rate>=0.02)
  H4 true edges:  (eat,ate) and (eat,tree_ate) in v2.5 in >=2/3 seeds.
     (press,lever) is DATA-LIMITED in LingerEnv (2-5 presses per life) and
     is REPORTED, not counted: pre-registered as informative-only here;
     its fate is decided by the regression environments where presses are
     plentiful.
  H5 regression:  on TerrariumV2 AND Terrarium v1 (real agent, 8000 steps,
     seeds 1-3): v2.5 keeps every true edge v2.2 keeps; v2.5 emits NO
     world-event edges (bell_rang, tree_appeared, key_appeared) and NO
     artifact edges (died, door_gone).
  H6 consistency + determinism (recomputed arms identical; fresh seed-1
     re-run identical).
  READY (for a v3 full run) = H1 & H2 & H3 & H4 & H5 & H6.

v2.5 rule (stratified contrast):
  For each (a,e): over contexts ctx where a was tried:
    n_a = trials of a in ctx; y_a = effects e by a in ctx
    n_o = trials of other actions in ctx; y_o = effects e by others in ctx
  Require Σn_a >= min_n and Σn_o >= min_o (data on both sides).
  rate_a = Σy_a / Σn_a
  rate_o = Σ_ctx (n_a,ctx * y_o,ctx / n_o,ctx) / Σn_a    (exposure-weighted)
  Edge stands iff rate_a >= min_p AND rate_a - rate_o >= margin.
  Contexts with n_o = 0 are excluded from the weighted sum (no others-data
  there); if ALL of a's contexts lack others-data the edge is reported as
  data-limited, not accepted.
"""
import sys
from collections import defaultdict

from agent_emca_v2 import view_features
from env_terrarium_v2 import ACTIONS
from env_terrarium_v2 import TerrariumV2
from sanity_reflex import AgentV23
from sanity_linger import LingerEnv, edge_diag, fmt, TRUE_EDGES

MOVES = ("up", "down", "left", "right")


class AgentV25(AgentV23):
    """v2.5: stratified (exposure-weighted within-context) contrast.

    Inherits AgentV23's observe() (with the door_gone artifact fix:
    door_gone filed only for non-move actions) and EMCA's act().
    causal_edges() implements the stratified rule above.
    """

    IDENTIFIER_VERSION = "v2.5-stratified"

    def __init__(self, *args, margin=0.10, min_o=3, **kw):
        super().__init__(*args, **kw)
        self.identifier_mode = "v25"
        self.margin = margin
        self.min_o = min_o
        self.identifier_version = self.IDENTIFIER_VERSION
        self.strat_report = {}

    def causal_edges(self, min_n=3, min_p=0.02, margin=None):
        out = {}
        self.strat_report = {}
        effects = {e for acts in self.ctx_ae.values()
                   for effs in acts.values() for e in effs if e != "trial"}
        for e in effects:
            # per-action stratified accumulators
            acc = defaultdict(lambda: {"y_a": 0, "n_a": 0, "w": 0.0,
                                       "y_w": 0.0, "n_o_tot": 0})
            for ctx, acts in self.ctx_ae.items():
                for a, effs in acts.items():
                    n_a = effs.get("trial", [0, 0])[1]
                    if n_a == 0:
                        continue
                    y_a = effs.get(e, [0, 0])[0] if e in effs else 0
                    n_o = sum(effs2.get("trial", [0, 0])[1]
                              for a2, effs2 in acts.items() if a2 != a)
                    y_o = sum(effs2[e][0] for a2, effs2 in acts.items()
                              if a2 != a and e in effs2)
                    A = acc[a]
                    A["y_a"] += y_a
                    A["n_a"] += n_a
                    if n_o > 0:
                        A["w"] += n_a
                        A["y_w"] += n_a * (y_o / n_o)
                        A["n_o_tot"] += n_o
            for a, A in acc.items():
                if A["n_a"] < min_n or A["n_o_tot"] < self.min_o:
                    continue
                rate_a = A["y_a"] / A["n_a"]
                if rate_a < min_p:
                    continue
                rate_o = A["y_w"] / A["w"] if A["w"] > 0 else None
                if rate_o is None:
                    continue
                m = margin if margin is not None else self.margin
                if rate_a - rate_o >= m:
                    out[(a, e)] = round(rate_a, 3)
                    self.strat_report[(a, e)] = {
                        "rate_a": round(rate_a, 3),
                        "rate_o": round(rate_o, 3),
                        "n_a": A["n_a"], "n_o": A["n_o_tot"]}
        return out


def run_agent(seed, steps=16000, env_cls=LingerEnv, agent_cls=AgentV25):
    env = env_cls(seed)
    ag = agent_cls(seed)
    for i in range(steps):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if done:
            env = env_cls(seed + 1000 + i)
    return ag


def arms(ag):
    # NOTE (run-5 harness bug, fixed): AgentV25.causal_edges ignores
    # identifier_mode, so the v2.1/v2.2 arms MUST call the EMCA implementation
    # directly -- otherwise all four arms silently measure v2.5.
    from agent_emca_v2 import EMCA
    assoc = ag.assoc_edges(min_n=3, min_p=0.02)
    ag.spec_cap = None
    pooled = EMCA.causal_edges(ag)          # global pooled, no spec gate
    ag.spec_cap = 0.10
    spec = EMCA.causal_edges(ag)            # v2.2 (global pooled + spec)
    strat = ag.causal_edges()               # this class's v2.5
    return assoc, pooled, spec, strat


def regression(env_name, seed, steps=8000):
    if env_name == "v2":
        env = TerrariumV2(seed)
    else:
        from env_terrarium import Terrarium
        env = Terrarium(seed)
    ag = AgentV25(seed)
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
    _, _, spec, strat = arms(ag)
    return spec, strat


WORLD_EVENT_EFFECTS = ("bell_rang", "tree_appeared", "key_appeared")
ARTIFACT_EFFECTS = ("died", "door_gone")


def main():
    print("sanity_stratified.py -- run 5: stratified contrast (v2.5) vs the "
          "linger decoy; regression guard")
    print("=" * 72)
    rows = []
    for seed in (1, 2, 3):
        ag = run_agent(seed)
        assoc, pooled, spec, strat = arms(ag)
        a2, p2, s2, st2 = arms(ag)
        cons = all(set(x) == set(y) for x, y in
                   ((assoc, a2), (pooled, p2), (spec, s2), (strat, st2)))
        d = edge_diag(ag, "eat", "bell_rang")
        print(f"\n--- seed {seed} ---")
        print(f"POOLED v2.1:  {fmt(pooled)}")
        print(f"SPEC v2.2:    {fmt(spec)}")
        print(f"STRAT v2.5:   {fmt(strat)}")
        print(f"decoy eat->bell_rang: rate_a={d['rate_a']} (n={d['n']}), "
              f"pooled_others={d['pooled']}")
        for k, v in ag.strat_report.items():
            print(f"  strat detail {k[0]}->{k[1]}: rate_a={v['rate_a']} "
                  f"rate_o={v['rate_o']} (n_a={v['n_a']}, n_o={v['n_o']})")
        for te in TRUE_EDGES:
            print(f"  true {te}: pooled={te in pooled} spec={te in spec} "
                  f"strat={te in strat}")
        print(f"  consistency: {cons}")
        rows.append({
            "seed": seed,
            "pooled_decoy": ("eat", "bell_rang") in pooled,
            "spec_decoy": ("eat", "bell_rang") in spec,
            "strat_decoy": ("eat", "bell_rang") in strat,
            "data_present": d["n"] >= 3 and d["rate_a"] >= 0.02,
            "true_strat": ("eat", "ate") in strat
                          and ("eat", "tree_ate") in strat,
            "press_strat": ("press", "lever") in strat,
            "consistency": cons,
        })

    ag1 = run_agent(1)
    ar1 = arms(ag1)
    ag0 = run_agent(1)
    ar0 = arms(ag0)
    det = all(set(x) == set(y) for x, y in zip(ar1, ar0))
    print(f"\nDETERMINISM (fresh seed-1 re-run, four arms): "
          f"{'PASS' if det else 'FAIL'}")

    print("\n--- REGRESSION: TerrariumV2 + Terrarium v1 (real agent) ---")
    reg_keep = True
    reg_clean = True
    for env_name in ("v2", "v1"):
        for seed in (1, 2, 3):
            spec, strat = regression(env_name, seed)
            true_edges = [te for te in TRUE_EDGES
                          if env_name == "v2" or te[1] != "tree_ate"]
            keep = all((te not in spec) or (te in strat) for te in true_edges)
            bad = [k for k in strat if k[1] in WORLD_EVENT_EFFECTS
                   or k[1] in ARTIFACT_EFFECTS]
            print(f"  {env_name} seed {seed}:")
            print(f"    spec v2.2: {fmt(spec)}")
            print(f"    strat v2.5: {fmt(strat)}  keep={keep} bad={bad}")
            reg_keep &= keep
            reg_clean &= not bad
    print(f"REGRESSION: keep={reg_keep} clean={reg_clean}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    h1 = sum(r["pooled_decoy"] for r in rows) >= 2
    h2 = sum(r["spec_decoy"] for r in rows) >= 2
    h3 = sum((not r["strat_decoy"]) and r["data_present"] for r in rows) >= 2
    h4 = sum(r["true_strat"] for r in rows) >= 2
    h5 = reg_keep and reg_clean
    h6 = det and all(r["consistency"] for r in rows)
    print(f"H1 decoy in pooled v2.1 (replication):  "
          f"{'PASS' if h1 else 'FAIL'} ({sum(r['pooled_decoy'] for r in rows)}/3)")
    print(f"H2 decoy in spec v2.2 (replication):    "
          f"{'PASS' if h2 else 'FAIL'} ({sum(r['spec_decoy'] for r in rows)}/3)")
    print(f"H3 MAIN stratified rejects decoy:       "
          f"{'PASS' if h3 else 'FAIL'} "
          f"({sum((not r['strat_decoy']) and r['data_present'] for r in rows)}/3)")
    print(f"H4 true edges survive stratified:       "
          f"{'PASS' if h4 else 'FAIL'} "
          f"({sum(r['true_strat'] for r in rows)}/3)")
    print(f"    (informative: press->lever in strat per seed: "
          f"{[r['press_strat'] for r in rows]} -- data-limited in LingerEnv)")
    print(f"H5 regression keep+clean:               "
          f"{'PASS' if h5 else 'FAIL'}")
    print(f"H6 consistency + determinism:           "
          f"{'PASS' if h6 else 'FAIL'}")
    ready = h1 and h2 and h3 and h4 and h5 and h6
    print(f"OVERALL: linger confounder + stratified identifier ready for a "
          f"v3 full run: {'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
