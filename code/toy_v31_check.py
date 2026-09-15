"""Toy check for the v3.1 world (TerrariumV31) -- TZ.md rule: before the
full matrix, verify with the REAL agents that the world does what the
turn-100 directive requires.

Directive (op_39d83261dc8e): (1) a world where the decoy is an attractor
or carries a cost, so agents with different identifiers DIFFER
BEHAVIOURALLY; (2) the chain completes (Treasures > 0); (3) direction 3
-- the stratified identifier's rejection survives a curiosity-driven
trajectory generator.

PRE-REGISTERED CRITERIA (before the first run of this file; lives are
8000 steps for the toy -- half the matrix scale, enough for the chain to
complete and the decoy data to accumulate):

  W1 world works:      emca_v25c arm survives: deaths <= 25 in >=2/3 seeds
  W2 chain completes:  treasures >= 1 in >=2/3 seeds for the v25c arm
                       (the turn-99 defect: 0/21; the v3.1 fixes are
                       info['key'], treasure scent, wanting-refresh)
  W3 decoy delivered:  decoy (grasp,bell_rang) in v2.1 causal in >=2/3
                       seeds AND in assoc (p002 view) in >=2/3 seeds
  W4 new way rejects:  decoy NOT in v2.5c causal in >=2/3 seeds
  W5 true edges kept:  eat->ate AND grasp->tree_gather in v2.5c in >=2/3
                       seeds (press->lever reported, not gated: the 16k
                       dilution boundary from turn 99 stands)
  W6 BEHAVIOURAL DIVERGENCE (the directive's core): the identifier arms
                       are NOT behaviourally identical: across seeds,
                       grasp_at_bell or chimes_collected or total_reward
                       differ between v2.1 and v2.5c in >=2/3 seeds
                       (turn-99 honest negative: all arms identical)
  W7 curiosity arm:    the curious agent (v2.5c identifier, novelty
                       generator) rejects the decoy too (0/3) with decoy
                       data present (assoc rate for grasp->bell_rang
                       exceeds the min_p floor)
  W8 determinism:      seed-1 re-run reproduces the edge sets and the
                       behavioural counters for v2.1 and v2.5c

READY = W1..W8.
"""
import sys

from run_life_v31 import run

DECOY = ("grasp", "bell_rang")
TRUE = [("eat", "ate"), ("grasp", "tree_gather")]


def edges_of(log):
    return {(a, e) for a, e, p in log["causal_edges"]}


def main():
    print("toy_v31_check.py -- real agents on TerrariumV31, 8000 steps, "
          "3 seeds, 5 arms")
    print("=" * 72)
    rows = []
    for seed in (1, 2, 3):
        v21 = run("emca_v21", seed, 8000)
        v25c = run("emca_v25c", seed, 8000)
        cur = run("curious", seed, 8000)
        e21, e25 = edges_of(v21), edges_of(v25c)
        assoc21 = {(a, e) for a, e, p in v21["assoc_edges_p002"]}
        assoc_cur = {(a, e) for a, e, p in cur["assoc_edges_p002"]}
        cur_rate = next((p for a, e, p in cur["assoc_edges_p002"]
                         if (a, e) == DECOY), 0.0)
        print(f"\n--- seed {seed} ---")
        print(f"v25c life: deaths={v25c['deaths']} fruits={v25c['tree_fruits']} "
              f"berries={v25c['berries_eaten']} chimes={v25c['chimes_collected']} "
              f"grasp@bell={v25c['grasp_at_bell']} treasures={v25c['treasures']} "
              f"reward={v25c['total_reward']:.0f}")
        print(f"v21  life: deaths={v21['deaths']} fruits={v21['tree_fruits']} "
              f"chimes={v21['chimes_collected']} grasp@bell={v21['grasp_at_bell']} "
              f"treasures={v21['treasures']} reward={v21['total_reward']:.0f}")
        print(f"curious:   deaths={cur['deaths']} fruits={cur['tree_fruits']} "
              f"grasp@bell={cur['grasp_at_bell']} decoy_causal={cur['decoy_in_causal']} "
              f"decoy_assoc_rate={cur_rate}")
        beh = (v21["grasp_at_bell"] != v25c["grasp_at_bell"]
               or v21["chimes_collected"] != v25c["chimes_collected"]
               or abs(v21["total_reward"] - v25c["total_reward"]) > 1e-9)
        rows.append({
            "seed": seed,
            "deaths": v25c["deaths"],
            "treasures": v25c["treasures"],
            "v21_decoy": DECOY in e21,
            "assoc_decoy": DECOY in assoc21,
            "v25c_decoy": DECOY in e25,
            "v25c_true": all(te in e25 for te in TRUE),
            "beh_diverge": beh,
            "cur_decoy": DECOY in edges_of(cur),
            "cur_data": cur_rate >= 0.02,
        })

    r21 = run("emca_v21", 1, 8000)
    r25 = run("emca_v25c", 1, 8000)
    det = (edges_of(r21) == edges_of(rows[0] and run("emca_v21", 1, 8000))
           and r21["grasp_at_bell"] == rows[0]["beh_diverge"] or True)
    # determinism: recompute and compare directly
    a1 = run("emca_v21", 1, 8000)
    a2 = run("emca_v21", 1, 8000)
    b1 = run("emca_v25c", 1, 8000)
    b2 = run("emca_v25c", 1, 8000)
    det = (edges_of(a1) == edges_of(a2)
           and a1["grasp_at_bell"] == a2["grasp_at_bell"]
           and a1["total_reward"] == a2["total_reward"]
           and edges_of(b1) == edges_of(b2)
           and b1["grasp_at_bell"] == b2["grasp_at_bell"]
           and b1["total_reward"] == b2["total_reward"])

    print("\n================ PRE-REGISTERED VERDICTS ================")
    w1 = sum(r["deaths"] <= 25 for r in rows) >= 2
    w2 = sum(r["treasures"] >= 1 for r in rows) >= 2
    w3 = sum(r["v21_decoy"] for r in rows) >= 2 and \
        sum(r["assoc_decoy"] for r in rows) >= 2
    w4 = sum(not r["v25c_decoy"] for r in rows) >= 2
    w5 = sum(r["v25c_true"] for r in rows) >= 2
    w6 = sum(r["beh_diverge"] for r in rows) >= 2
    w7 = sum((not r["cur_decoy"]) and r["cur_data"] for r in rows) >= 2
    print(f"W1 world works (deaths<=25):       {'PASS' if w1 else 'FAIL'} "
          f"{[r['deaths'] for r in rows]}")
    print(f"W2 chain completes (treasures>=1): {'PASS' if w2 else 'FAIL'} "
          f"{[r['treasures'] for r in rows]}")
    print(f"W3 decoy bites v2.1 + assoc:       {'PASS' if w3 else 'FAIL'} "
          f"v21={[r['v21_decoy'] for r in rows]} assoc={[r['assoc_decoy'] for r in rows]}")
    print(f"W4 v2.5c rejects decoy:            {'PASS' if w4 else 'FAIL'} "
          f"{[r['v25c_decoy'] for r in rows]}")
    print(f"W5 v2.5c keeps true edges:         {'PASS' if w5 else 'FAIL'} "
          f"{[r['v25c_true'] for r in rows]}")
    print(f"W6 behavioural divergence:         {'PASS' if w6 else 'FAIL'} "
          f"{[r['beh_diverge'] for r in rows]}")
    print(f"W7 curious arm rejects too:        {'PASS' if w7 else 'FAIL'} "
          f"{[r['cur_decoy'] for r in rows]} data={[r['cur_data'] for r in rows]}")
    print(f"W8 determinism:                    {'PASS' if det else 'FAIL'}")
    ready = all((w1, w2, w3, w4, w5, w6, w7, det))
    print(f"OVERALL: v3.1 ready for the matrix: {'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
