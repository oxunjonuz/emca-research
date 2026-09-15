#!/usr/bin/env python3
"""Run 7: v2.5c -- v2.5b with the door_gone view-artifact fixed IN THE DATA
(ctx_ae), not hidden by a threshold.

Run 6 (sanity_stratified2.py) measured: v2.5b (stratified + RR>=2) rejects
the linger decoy 3/3, keeps ALL true edges including the rare ones
(press->lever 0.03, eat->tree_ate 0.044) -- but emits one systematic
artifact edge in the TerrariumV2 regression: (left, door_gone) 0.059-0.087
in 3/3 seeds, RR=inf. Root cause (found by reading the code, not guessing):
AgentV23's door_gone fix applied only to the eps/del stores; the parent
EMCA.observe still files door_gone into ctx_ae for MOVE actions. Moving
away from the door makes it leave the 3x3 view -- a sensory artifact of
the agent's own motion, not a world event (the v1 lesson). The global
contrast hid it (all moves share the artifact, contrast ~ 0); the
stratified RR gate exposed it (within left's contexts, others rarely move
away).

Fix (v2.5c): door_gone is filed ONLY for non-move actions. Standing still
while the door leaves the view IS a world change (the door opened /
vanished); walking away is not. This is a data-pipeline fix, documented in
the identifier lineage, not a threshold tuned to hide a failure.

PRE-REGISTERED CRITERIA (identical to run 6's B1-B4; the fix targets the
known artifact only):
  B1 decoy rejected: (eat,bell_rang) NOT in v2.5c in >=2/3 seeds, decoy
     data present
  B2 true edges in LingerEnv: (eat,ate) and (eat,tree_ate) in v2.5c in
     >=2/3 seeds; press->lever reported (data-limited in LingerEnv)
  B3 regression (TerrariumV2 + Terrarium v1, real agent, 8000 steps,
     seeds 1-3): keeps every true edge v2.2 keeps AND emits no world-event
     (bell_rang/tree_appeared/key_appeared) or artifact (died/door_gone)
     edges
  B4 consistency + determinism
  READY (for a v3 full run) = B1 & B2 & B3 & B4.
"""
import sys
from collections import defaultdict

from agent_emca_v2 import EMCA, view_features
from env_terrarium_v2 import TerrariumV2
from sanity_stratified import run_agent, fmt
from sanity_stratified2 import AgentV25b, arms
from sanity_linger import edge_diag, TRUE_EDGES

MOVES = ("up", "down", "left", "right")
WORLD_EVENT_EFFECTS = ("bell_rang", "tree_appeared", "key_appeared")
ARTIFACT_EFFECTS = ("died", "door_gone")


class AgentV25c(AgentV25b):
    """v2.5c: v2.5b + door_gone filed only for non-move actions (ctx_ae).

    observe() is EMCA.observe verbatim except one condition (a not in MOVES
    for the door_gone view-effect). The eps/del instrumentation of the
    AgentV23 lineage is not used by the stratified identifier and is
    dropped here for clarity.
    """

    IDENTIFIER_VERSION = "v2.5c-stratified-RR-doorgonefix"

    def observe(self, o, a, r, o2, done, info):
        self.t += 1
        f1, f2 = view_features(o), view_features(o2)
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
        # v2.5c fix: door_gone only when NOT moving -- walking away must not
        # "cause" the door to leave the 3x3 view (v1 lesson, run-6 artifact)
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


def main():
    print("sanity_stratified3.py -- run 7: v2.5c (door_gone artifact fixed "
          "in data) vs the linger decoy; regression guard")
    print("=" * 72)
    rows = []
    for seed in (1, 2, 3):
        ag = run_agent(seed, agent_cls=AgentV25c)
        assoc, pooled, spec, stratc = arms(ag)
        a2, p2, s2, sc2 = arms(ag)
        cons = all(set(x) == set(y) for x, y in
                   ((assoc, a2), (pooled, p2), (spec, s2), (stratc, sc2)))
        d = edge_diag(ag, "eat", "bell_rang")
        print(f"\n--- seed {seed} ---")
        print(f"POOLED v2.1:  {fmt(pooled)}")
        print(f"SPEC v2.2:    {fmt(spec)}")
        print(f"STRAT v2.5c:  {fmt(stratc)}")
        print(f"decoy eat->bell_rang: rate_a={d['rate_a']} (n={d['n']}), "
              f"pooled_others={d['pooled']}")
        for te in TRUE_EDGES:
            print(f"  true {te}: pooled={te in pooled} spec={te in spec} "
                  f"stratc={te in stratc}")
        print(f"  consistency: {cons}")
        rows.append({
            "seed": seed,
            "pooled_decoy": ("eat", "bell_rang") in pooled,
            "spec_decoy": ("eat", "bell_rang") in spec,
            "stratc_decoy": ("eat", "bell_rang") in stratc,
            "data_present": d["n"] >= 3 and d["rate_a"] >= 0.02,
            "true_stratc": ("eat", "ate") in stratc
                           and ("eat", "tree_ate") in stratc,
            "press_stratc": ("press", "lever") in stratc,
            "consistency": cons,
        })

    ag1 = run_agent(1, agent_cls=AgentV25c)
    ar1 = arms(ag1)
    ag0 = run_agent(1, agent_cls=AgentV25c)
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
            ag = AgentV25c(seed)
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
            assoc, pooled, spec, stratc = arms(ag)
            true_edges = [te for te in TRUE_EDGES
                          if env_name == "v2" or te[1] != "tree_ate"]
            keep = all((te not in spec) or (te in stratc) for te in true_edges)
            bad = [k for k in stratc if k[1] in WORLD_EVENT_EFFECTS
                   or k[1] in ARTIFACT_EFFECTS]
            print(f"  {env_name} seed {seed}:")
            print(f"    spec v2.2:  {fmt(spec)}")
            print(f"    strat v2.5c: {fmt(stratc)}  keep={keep} bad={bad}")
            reg_keep &= keep
            reg_clean &= not bad
    print(f"REGRESSION: keep={reg_keep} clean={reg_clean}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    b1 = sum((not r["stratc_decoy"]) and r["data_present"] for r in rows) >= 2
    b2 = sum(r["true_stratc"] for r in rows) >= 2
    b3 = reg_keep and reg_clean
    b4 = det and all(r["consistency"] for r in rows)
    print(f"B1 stratified-RR rejects decoy:   "
          f"{'PASS' if b1 else 'FAIL'} "
          f"({sum((not r['stratc_decoy']) and r['data_present'] for r in rows)}/3)")
    print(f"B2 true edges survive:            "
          f"{'PASS' if b2 else 'FAIL'} ({sum(r['true_stratc'] for r in rows)}/3)")
    print(f"    (informative: press->lever in v2.5c per seed: "
          f"{[r['press_stratc'] for r in rows]})")
    print(f"B3 regression keep+clean:         "
          f"{'PASS' if b3 else 'FAIL'}")
    print(f"B4 consistency + determinism:     "
          f"{'PASS' if b4 else 'FAIL'}")
    ready = b1 and b2 and b3 and b4
    print(f"OVERALL: linger confounder + v2.5c identifier ready for a v3 "
          f"full run: {'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
