#!/usr/bin/env python3
"""Toy-scale check of TerrariumV2 BEFORE the full 9x3 matrix (TZ.md rule:
"прежде чем гнать полную матрицу на новой версии среды, сначала маленькой
проверкой убедись, что новая среда действительно способна развести то, что
должна развести").

Question: does v2 + the v2.2 identifier (S7 specificity gate) actually
separate causal from correlational identification IN THE REAL ENVIRONMENT
(not the toy harness of sanity_v2_confounder.py)?

Arms (all driven by the SAME observational data -- one agent instance per
seed, edges computed from identical ctx_ae):
  * spec ON  (v2.2):  decoy (grasp,bell_rang) must be REJECTED
  * spec OFF (v2.1):  decoy must be ACCEPTED (the environment bites)
  * assoc (correlation): decoy must be ACCEPTED (correlation is fooled)
True edges must SURVIVE in spec ON: (eat,ate), (press,lever), (tree_ate,eat).

PRE-REGISTERED CRITERIA (fixed before the first run of this file):
  V1 correlation fooled:   assoc has decoy in >=2/3 seeds
  V2 v2.1 identifier fooled: spec-OFF has decoy in >=2/3 seeds (env bites)
  V3 v2.2 identifier clean: spec-ON lacks decoy in >=2/3 seeds, with decoy
                            data present (n>=3, rate>=0.02) in those seeds
  V4 true edges survive:   spec-ON has (eat,ate) and (press,lever) in >=2/3
  V5 tree edge survives:   spec-ON has (eat,tree_ate) in >=2/3 seeds
OVERALL: v2 ready for the matrix iff V1&V2&V3&V4 (V5 informative for E5).

Driver: the REAL v2.2 agent (act+observe) -- not a scripted policy -- so the
data distribution is the agent's own. 8000 steps, seeds 1,2,3.
"""
import sys
from collections import defaultdict

from agent_emca_v2 import EMCA
from env_terrarium_v2 import TerrariumV2, ACTIONS

DECOY = ("grasp", "bell_rang")
TRUE_EDGES = [("eat", "ate"), ("press", "lever"), ("eat", "tree_ate")]


def run(seed, steps=8000):
    env = TerrariumV2(seed)
    ag = EMCA(seed)          # spec ON by default (v2.2)
    grasp_n = grasp_ring = 0
    for i in range(steps):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if a == "grasp":
            grasp_n += 1
            if info.get("bell_rang"):
                grasp_ring += 1
        if done:
            env = TerrariumV2(seed + 1000 + i)
    return ag, grasp_n, grasp_ring


def edge_diagnostics(ag, action, effect):
    y = n = 0
    for ctx, acts in ag.ctx_ae.items():
        if action in acts:
            n += acts[action].get("trial", [0, 0])[1]
            if effect in acts[action]:
                y += acts[action][effect][0]
    rate_a = y / n if n else 0.0
    oy = on = 0
    for ctx, acts in ag.ctx_ae.items():
        if action in acts and effect in acts[action]:
            for a2, effs in acts.items():
                if a2 != action:
                    oy += effs.get(effect, [0, 0])[0]
                    on += effs.get("trial", [0, 0])[1]
    pooled = oy / on if on else None
    return {"y": y, "n": n, "rate_a": round(rate_a, 4),
            "pooled": round(pooled, 4) if pooled is not None else None}


def fmt(d):
    return "{%s}" % ", ".join(f"{a}->{e}:{p}" for (a, e), p in sorted(d.items()))


def main():
    print("sanity_env_v2.py -- toy check of TerrariumV2 + v2.2 identifier (real agent)")
    rows = []
    for seed in (1, 2, 3):
        ag, gn, gr = run(seed)
        assoc = ag.assoc_edges()
        spec_on = ag.causal_edges()                    # v2.2 (spec_cap=0.10)
        ag.spec_cap = None
        spec_off = ag.causal_edges()                   # v2.1-equivalent, SAME data
        ag.spec_cap = 0.10
        d = edge_diagnostics(ag, *DECOY)
        print(f"\n--- seed {seed}: grasp trials={gn}, rang during grasp={gr} "
              f"(raw rate {gr / gn if gn else 0:.3f}) ---")
        print(f"ASSOC (correlation):        {fmt(assoc)}")
        print(f"CAUSAL spec OFF (v2.1):     {fmt(spec_off)}")
        print(f"CAUSAL spec ON  (v2.2):     {fmt(spec_on)}")
        print(f"decoy diag: rate_a={d['rate_a']} (n={d['n']}), pooled={d['pooled']}")
        for te in TRUE_EDGES:
            print(f"  true {te}: assoc={te in assoc} v21={te in spec_off} "
                  f"v22={te in spec_on}")
        rows.append({
            "seed": seed,
            "assoc_decoy": DECOY in assoc,
            "off_decoy": DECOY in spec_off,
            "on_decoy": DECOY in spec_on,
            "data_present": d["n"] >= 3 and d["rate_a"] >= 0.02,
            "true_on": all(te in spec_on for te in TRUE_EDGES[:2]),
            "tree_on": TRUE_EDGES[2] in spec_on,
        })

    print("\n================ PRE-REGISTERED VERDICTS ================")
    v1 = sum(r["assoc_decoy"] for r in rows) >= 2
    v2 = sum(r["off_decoy"] for r in rows) >= 2
    v3 = sum((not r["on_decoy"]) and r["data_present"] for r in rows) >= 2
    v4 = sum(r["true_on"] for r in rows) >= 2
    v5 = sum(r["tree_on"] for r in rows) >= 2
    print(f"V1 correlation fooled:            {'PASS' if v1 else 'FAIL'} "
          f"({sum(r['assoc_decoy'] for r in rows)}/3)")
    print(f"V2 v2.1 identifier fooled:        {'PASS' if v2 else 'FAIL'} "
          f"({sum(r['off_decoy'] for r in rows)}/3)")
    print(f"V3 v2.2 identifier rejects decoy: {'PASS' if v3 else 'FAIL'} "
          f"({sum((not r['on_decoy']) and r['data_present'] for r in rows)}/3)")
    print(f"V4 true edges survive (v2.2):     {'PASS' if v4 else 'FAIL'} "
          f"({sum(r['true_on'] for r in rows)}/3)")
    print(f"V5 tree edge survives (v2.2):     {'PASS' if v5 else 'FAIL'} "
          f"({sum(r['tree_on'] for r in rows)}/3)")
    ready = v1 and v2 and v3 and v4
    print(f"OVERALL: TerrariumV2 ready for the full matrix: {'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
