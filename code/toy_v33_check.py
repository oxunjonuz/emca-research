"""Toy check for the v3.3 world (TerrariumV33) -- TZ.md rule: before the
full matrix, verify with the REAL agents that the world does what the
turn-102 directive requires. Lives are 8000 steps (half the matrix).

PRE-REGISTERED CRITERIA (before the first run of this file):

  W1 deficit is real but survivable: AgentV33 (v2.5c planner) deaths
     <= 30 in >=2/3 seeds (v3.2 at 8000 steps: 10-13; scarcity must
     bite harder but not kill the competent)
  W2 the dynamic grasp cost bites: the believer's (v2.1 pooled)
     grasp-at-bell WITHOUT a tree in reach costs it -- v2.1 reward
     <= v2.5c reward in >=2/3 seeds (the v3.2 toy had the believer
     winning 1/3; scarcity + the 1.8 storm price should tip it)
  W3 identifier question unchanged: decoy (grasp, bell_rang) in v2.1
     causal in >=2/3 seeds AND NOT in v2.5c causal in >=2/3 seeds;
     true edges (eat->ate, grasp->tree_gather) in v2.5c in >=2/3
  W4 prober survives the offering: prober deaths <= 40 in >=2/3 seeds
     AND reaches >=1 verdict in >=2/3 seeds
  W5 curious_surv dominance survives scarcity: curious_surv deaths <=
     20 in >=2/3 seeds AND curious_surv reward >= v2.5c reward in
     >=2/3 seeds (the v3.2 dominance was +82%; scarcity cuts the
     roaming dividend -- the honest question is whether it survives)
  W6 chain-curious arm works mechanically: AgentCuriousChain produces
     >=1 lever press AND >=1 key pickup in every seed (the object-
     directed novelty layer functions); treasures >=1 in >=1 seed at
     8000 steps would be a bonus, not a criterion (the 12-step window
     is hard; the matrix at 16000 is the real test)
  W7 pure novelty still dies (the honest ablation): curious_pure
     deaths > curious_surv deaths in >=2/3 seeds
  W8 determinism: seed-1 re-runs reproduce edge sets + behavioural
     counters for v2.1, v2.5c, chain

READY = W1..W8.
"""
import sys

from run_life_v33 import run

DECOY = ("grasp", "bell_rang")
TRUE = [("eat", "ate"), ("grasp", "tree_gather")]


def edges_of(log):
    return {(a, e) for a, e, p in log["causal_edges"]}


def main():
    print("toy_v33_check.py -- real agents on TerrariumV33, 8000 steps, "
          "3 seeds")
    print("=" * 72)
    rows = []
    for seed in (1, 2, 3):
        v21 = run("emca_v21", seed, 8000)
        v25c = run("emca_v25c", seed, 8000)
        prober = run("prober", seed, 8000)
        cs = run("curious_surv", seed, 8000)
        cp = run("curious_pure", seed, 8000)
        ch = run("curious_chain", seed, 8000)
        e21, e25 = edges_of(v21), edges_of(v25c)
        pv = prober.get("probe_verdicts") or {}
        rows.append({
            "seed": seed,
            "deaths": v25c["deaths"],
            "v21_decoy": DECOY in e21,
            "v25c_decoy": DECOY in e25,
            "v25c_true": all(te in e25 for te in TRUE),
            "sign": v25c["total_reward"] - v21["total_reward"],
            "r21": v21["total_reward"], "r25": v25c["total_reward"],
            "d21": v21["deaths"],
            "prober_deaths": prober["deaths"],
            "prober_ran": len(pv) >= 1,
            "cs_deaths": cs["deaths"], "cs_r": cs["total_reward"],
            "cp_deaths": cp["deaths"],
            "ch_levers": ch["lever_presses"],
            "ch_keys": ch["keys_picked"],
            "ch_treasures": ch["treasures"],
            "ch_deaths": ch["deaths"],
        })
        print(f"\n--- seed {seed} ---")
        print(f"v25c: deaths={v25c['deaths']} reward={v25c['total_reward']:.0f} "
              f"fruits={v25c['tree_fruits']} grasp@bell={v25c['grasp_at_bell']}")
        print(f"v21:  deaths={v21['deaths']} reward={v21['total_reward']:.0f} "
              f"fruits={v21['tree_fruits']} grasp@bell={v21['grasp_at_bell']}")
        print(f"prober: deaths={prober['deaths']} "
              f"verdicts={ {k: v['verdict'] for k, v in pv.items()} }")
        print(f"curious_surv: deaths={cs['deaths']} "
              f"reward={cs['total_reward']:.0f} fruits={cs['tree_fruits']}")
        print(f"curious_pure: deaths={cp['deaths']}")
        print(f"chain: deaths={ch['deaths']} levers={ch['lever_presses']} "
              f"keys={ch['keys_picked']} treasures={ch['treasures']} "
              f"reward={ch['total_reward']:.0f}")

    # determinism: fresh re-runs of seed 1
    a1 = run("emca_v21", 1, 8000)
    a2 = run("emca_v21", 1, 8000)
    b1 = run("emca_v25c", 1, 8000)
    b2 = run("emca_v25c", 1, 8000)
    c1 = run("curious_chain", 1, 8000)
    c2 = run("curious_chain", 1, 8000)
    det = (edges_of(a1) == edges_of(a2)
           and a1["total_reward"] == a2["total_reward"]
           and a1["grasp_at_bell"] == a2["grasp_at_bell"]
           and edges_of(b1) == edges_of(b2)
           and b1["total_reward"] == b2["total_reward"]
           and c1["total_reward"] == c2["total_reward"]
           and c1["treasures"] == c2["treasures"]
           and c1["lever_presses"] == c2["lever_presses"])

    print("\n================ PRE-REGISTERED VERDICTS ================")
    w1 = sum(r["deaths"] <= 30 for r in rows) >= 2
    w2 = sum(r["sign"] >= 0 for r in rows) >= 2
    w3 = sum(r["v21_decoy"] for r in rows) >= 2 and \
        sum(not r["v25c_decoy"] for r in rows) >= 2 and \
        sum(r["v25c_true"] for r in rows) >= 2
    w4 = sum(r["prober_deaths"] <= 40 for r in rows) >= 2 and \
        sum(r["prober_ran"] for r in rows) >= 2
    w5 = sum(r["cs_deaths"] <= 20 for r in rows) >= 2 and \
        sum(r["cs_r"] >= r["r25"] for r in rows) >= 2
    w6 = all(r["ch_levers"] >= 1 and r["ch_keys"] >= 1 for r in rows)
    w7 = sum(r["cp_deaths"] > r["cs_deaths"] for r in rows) >= 2
    print(f"W1 deficit survivable (v25c deaths<=30):  {'PASS' if w1 else 'FAIL'} "
          f"{[r['deaths'] for r in rows]}")
    print(f"W2 dynamic cost bites (v25c>=v21):       {'PASS' if w2 else 'FAIL'} "
          f"per-seed diff={[round(r['sign']) for r in rows]}")
    print(f"W3 identifier unchanged (decoy/true):    {'PASS' if w3 else 'FAIL'} "
          f"v21_decoy={[r['v21_decoy'] for r in rows]} "
          f"v25c_decoy={[r['v25c_decoy'] for r in rows]} "
          f"true={[r['v25c_true'] for r in rows]}")
    print(f"W4 prober survives the offering:         {'PASS' if w4 else 'FAIL'} "
          f"deaths={[r['prober_deaths'] for r in rows]} "
          f"ran={[r['prober_ran'] for r in rows]}")
    print(f"W5 curious_surv dominance survives:      {'PASS' if w5 else 'FAIL'} "
          f"cs_deaths={[r['cs_deaths'] for r in rows]} "
          f"cs_r-r25={[round(r['cs_r'] - r['r25']) for r in rows]}")
    print(f"W6 chain arm functions (levers+keys):    {'PASS' if w6 else 'FAIL'} "
          f"levers={[r['ch_levers'] for r in rows]} "
          f"keys={[r['ch_keys'] for r in rows]} "
          f"treasures={[r['ch_treasures'] for r in rows]}")
    print(f"W7 pure novelty dies (honest ablation):  {'PASS' if w7 else 'FAIL'} "
          f"cp={[r['cp_deaths'] for r in rows]} cs={[r['cs_deaths'] for r in rows]}")
    print(f"W8 determinism:                          {'PASS' if det else 'FAIL'}")
    ready = all((w1, w2, w3, w4, w5, w6, w7, det))
    print(f"OVERALL: v3.3 ready for the matrix: {'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
