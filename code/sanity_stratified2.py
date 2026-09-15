#!/usr/bin/env python3
"""Run 6: v2.5b -- stratified contrast with a RELATIVE-RISK gate (RR >= 2),
fixing run 5's H5 failure (fixed margin 0.10 killed rare true edges).

Run 5 (sanity_stratified.py, harness-fixed) measured:
  * stratified v2.5 with fixed margin 0.10 rejects the linger decoy 3/3
    (H3 PASS) and emits no junk (clean) -- but loses rare TRUE edges in the
    regression: press->lever (rate_a 0.028-0.032) and eat->tree_ate
    (0.044) fail the absolute margin even though rate_o ~ 0.
  * The data show the structural difference: the decoy SHARES its effect
    (rate_o ~ rate_a, RR ~ 1: at the tree everyone rings at 0.40); true
    edges are EXCLUSIVE (rate_o ~ 0, RR -> inf). An absolute margin
    cannot serve both; a relative one can.

v2.5b rule (pre-registered here, before the first run of this file):
  Same stratified accumulation as v2.5 (exposure-weighted rate_o over the
  action's own contexts; contexts without others-data excluded; total
  n_o >= 10). Edge stands iff:
      n_a >= min_n, rate_a >= min_p, and
      rate_o == 0  (with n_o >= 10: others never produced e where a was
                    tried -- exclusive effect)   OR
      rate_a >= 2 * rate_o   (relative risk >= 2, the epidemiological
                              weak-heuristic threshold; the measured RR is
                              reported per edge so the choice is auditable)
  Stated boundary: a confounder that DOUBLES the base rate would pass;
  multi-cause worlds (shared true effects) still lose true edges -- same
  boundary as S7, now relative.

PRE-REGISTERED CRITERIA:
  B1 decoy rejected: (eat,bell_rang) NOT in v2.5b in >=2/3 seeds, decoy
     data present (third replication of the bite is H1 of run 5: 3/3)
  B2 true edges in LingerEnv: (eat,ate) and (eat,tree_ate) in v2.5b in
     >=2/3 seeds; press->lever reported (data-limited: 2-5 presses/life)
  B3 regression (TerrariumV2 + Terrarium v1, real agent, 8000 steps,
     seeds 1-3): v2.5b keeps EVERY true edge v2.2 keeps (incl.
     press->lever and eat->tree_ate -- reversing run 5's H5 failure) AND
     emits no world-event (bell_rang/tree_appeared/key_appeared) or
     artifact (died/door_gone) edges
  B4 consistency + determinism
  READY (for a v3 full run) = B1 & B2 & B3 & B4.
"""
import sys
from collections import defaultdict

from agent_emca_v2 import EMCA
from env_terrarium_v2 import TerrariumV2
from sanity_stratified import AgentV25, run_agent, regression, fmt
from sanity_linger import edge_diag, TRUE_EDGES

WORLD_EVENT_EFFECTS = ("bell_rang", "tree_appeared", "key_appeared")
ARTIFACT_EFFECTS = ("died", "door_gone")


class AgentV25b(AgentV25):
    """v2.5b: stratified contrast + relative-risk gate (RR >= 2)."""

    IDENTIFIER_VERSION = "v2.5b-stratified-RR"

    def __init__(self, *args, min_o=10, **kw):
        super().__init__(*args, **kw)
        self.min_o = min_o
        self.identifier_version = self.IDENTIFIER_VERSION

    def causal_edges(self, min_n=3, min_p=0.02, margin=None):
        out = {}
        self.strat_report = {}
        effects = {e for acts in self.ctx_ae.values()
                   for effs in acts.values() for e in effs if e != "trial"}
        for e in effects:
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
                if rate_o == 0.0 or rate_a >= 2.0 * rate_o:
                    rr = float("inf") if rate_o == 0.0 else rate_a / rate_o
                    out[(a, e)] = round(rate_a, 3)
                    self.strat_report[(a, e)] = {
                        "rate_a": round(rate_a, 4),
                        "rate_o": round(rate_o, 4),
                        "rr": rr if rr != float("inf") else "inf",
                        "n_a": A["n_a"], "n_o": A["n_o_tot"]}
        return out


def arms(ag):
    assoc = ag.assoc_edges(min_n=3, min_p=0.02)
    ag.spec_cap = None
    pooled = EMCA.causal_edges(ag)
    ag.spec_cap = 0.10
    spec = EMCA.causal_edges(ag)
    stratb = ag.causal_edges()
    return assoc, pooled, spec, stratb


def main():
    print("sanity_stratified2.py -- run 6: v2.5b (stratified + RR>=2) vs "
          "the linger decoy; regression guard")
    print("=" * 72)
    rows = []
    for seed in (1, 2, 3):
        ag = run_agent(seed, agent_cls=AgentV25b)
        assoc, pooled, spec, stratb = arms(ag)
        a2, p2, s2, sb2 = arms(ag)
        cons = all(set(x) == set(y) for x, y in
                   ((assoc, a2), (pooled, p2), (spec, s2), (stratb, sb2)))
        d = edge_diag(ag, "eat", "bell_rang")
        print(f"\n--- seed {seed} ---")
        print(f"POOLED v2.1:  {fmt(pooled)}")
        print(f"SPEC v2.2:    {fmt(spec)}")
        print(f"STRAT v2.5b:  {fmt(stratb)}")
        print(f"decoy eat->bell_rang: rate_a={d['rate_a']} (n={d['n']}), "
              f"pooled_others={d['pooled']}")
        for k, v in ag.strat_report.items():
            print(f"  strat detail {k[0]}->{k[1]}: rate_a={v['rate_a']} "
                  f"rate_o={v['rate_o']} rr={v['rr']} (n_a={v['n_a']}, "
                  f"n_o={v['n_o']})")
        for te in TRUE_EDGES:
            print(f"  true {te}: pooled={te in pooled} spec={te in spec} "
                  f"stratb={te in stratb}")
        print(f"  consistency: {cons}")
        rows.append({
            "seed": seed,
            "pooled_decoy": ("eat", "bell_rang") in pooled,
            "spec_decoy": ("eat", "bell_rang") in spec,
            "stratb_decoy": ("eat", "bell_rang") in stratb,
            "data_present": d["n"] >= 3 and d["rate_a"] >= 0.02,
            "true_stratb": ("eat", "ate") in stratb
                           and ("eat", "tree_ate") in stratb,
            "press_stratb": ("press", "lever") in stratb,
            "consistency": cons,
        })

    ag1 = run_agent(1, agent_cls=AgentV25b)
    ar1 = arms(ag1)
    ag0 = run_agent(1, agent_cls=AgentV25b)
    ar0 = arms(ag0)
    det = all(set(x) == set(y) for x, y in zip(ar1, ar0))
    print(f"\nDETERMINISM (fresh seed-1 re-run): {'PASS' if det else 'FAIL'}")

    print("\n--- REGRESSION: TerrariumV2 + Terrarium v1 (real agent) ---")
    reg_keep = True
    reg_clean = True
    for env_name in ("v2", "v1"):
        for seed in (1, 2, 3):
            if env_name == "v2":
                env = TerrariumV2(seed)
            else:
                from env_terrarium import Terrarium
                env = Terrarium(seed)
            ag = AgentV25b(seed)
            for i in range(8000):
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
            assoc, pooled, spec, stratb = arms(ag)
            true_edges = [te for te in TRUE_EDGES
                          if env_name == "v2" or te[1] != "tree_ate"]
            keep = all((te not in spec) or (te in stratb) for te in true_edges)
            bad = [k for k in stratb if k[1] in WORLD_EVENT_EFFECTS
                   or k[1] in ARTIFACT_EFFECTS]
            print(f"  {env_name} seed {seed}:")
            print(f"    spec v2.2:  {fmt(spec)}")
            print(f"    strat v2.5b: {fmt(stratb)}  keep={keep} bad={bad}")
            reg_keep &= keep
            reg_clean &= not bad
    print(f"REGRESSION: keep={reg_keep} clean={reg_clean}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    b1 = sum((not r["stratb_decoy"]) and r["data_present"] for r in rows) >= 2
    b2 = sum(r["true_stratb"] for r in rows) >= 2
    b3 = reg_keep and reg_clean
    b4 = det and all(r["consistency"] for r in rows)
    print(f"B1 stratified-RR rejects decoy:   "
          f"{'PASS' if b1 else 'FAIL'} "
          f"({sum((not r['stratb_decoy']) and r['data_present'] for r in rows)}/3)")
    print(f"B2 true edges survive:            "
          f"{'PASS' if b2 else 'FAIL'} ({sum(r['true_stratb'] for r in rows)}/3)")
    print(f"    (informative: press->lever in v2.5b per seed: "
          f"{[r['press_stratb'] for r in rows]})")
    print(f"B3 regression keep+clean:         "
          f"{'PASS' if b3 else 'FAIL'}")
    print(f"B4 consistency + determinism:     "
          f"{'PASS' if b4 else 'FAIL'}")
    ready = b1 and b2 and b3 and b4
    print(f"OVERALL: linger confounder + v2.5b identifier ready for a v3 "
          f"full run: {'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
