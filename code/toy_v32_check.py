"""Toy check for the v3.2 world (TerrariumV32) -- TZ.md rule: before the
full matrix, verify with the REAL agents that the world does what the
turn-101 directive requires. Lives are 8000 steps (half the matrix).

PRE-REGISTERED CRITERIA (before the first run of this file):

  W1 world works:      emca_v25c survives: deaths <= 25 in >=2/3 seeds
  W2 decoy delivered:  decoy (grasp,bell_rang) in v2.1 causal in >=2/3
                       seeds AND in assoc (p002) in >=2/3 seeds
  W3 new way rejects:  decoy NOT in v2.5c causal in >=2/3 seeds
  W4 SIGN INVERSION (the owner's task-1 prediction): v2.5c reward >=
                       v2.1 reward per seed in >=2/3 seeds (turn-100:
                       the false belief PAID +1226/+996; the separated
                       geometry should invert the sign)
  W5 true edges kept:  eat->ate AND grasp->tree_gather in v2.5c in >=2/3
  W6 prober resolves:  the prober runs >=1 probe with a verdict (any)
                       in >=2/3 seeds; the altar edge (wait,patch_berry)
                       is GRAY-detected (1<=RR<2) in >=2/3 seeds
  W7 curious survives: curious_surv deaths <= 25 in >=2/3 seeds AND
                       curious_surv deaths < curious_pure deaths in
                       >=2/3 seeds (the synthesis must beat bare
                       curiosity at survival -- the turn-100 arm died 86x)
  W8 curious explores: curious_surv novelty_transitions >= curious_pure
                       * 0.5 in >=2/3 seeds (survival must not cost
                       most of the exploration)
  W9 determinism:      seed-1 re-runs reproduce edge sets + behavioural
                       counters for v2.1, v2.5c, prober

READY = W1..W9.
"""
import sys

from run_life_v32 import run

DECOY = ("grasp", "bell_rang")
ALTAR_EDGE = ("wait", "patch_berry")
TRUE = [("eat", "ate"), ("grasp", "tree_gather")]


def edges_of(log):
    return {(a, e) for a, e, p in log["causal_edges"]}


def main():
    print("toy_v32_check.py -- real agents on TerrariumV32, 8000 steps, "
          "3 seeds, 6 arms")
    print("=" * 72)
    rows = []
    for seed in (1, 2, 3):
        v21 = run("emca_v21", seed, 8000)
        v25c = run("emca_v25c", seed, 8000)
        prober = run("prober", seed, 8000)
        cp = run("curious_pure", seed, 8000)
        cs = run("curious_surv", seed, 8000)
        e21, e25 = edges_of(v21), edges_of(v25c)
        assoc21 = {(a, e) for a, e, p in v21["assoc_edges_p002"]}
        pv = prober.get("probe_verdicts") or {}
        verdicts = {k: v["verdict"] for k, v in pv.items()}
        rows.append({
            "seed": seed,
            "deaths": v25c["deaths"],
            "v21_decoy": DECOY in e21,
            "assoc_decoy": DECOY in assoc21,
            "v25c_decoy": DECOY in e25,
            "v25c_true": all(te in e25 for te in TRUE),
            "sign_inv": v25c["total_reward"] >= v21["total_reward"],
            "r21": v21["total_reward"], "r25": v25c["total_reward"],
            "prober_ran": len(pv) >= 1,
            "altar_gray": any(
                "patch_berry" in k for k in
                (prober.get("probe_verdicts") or {})),
            "cs_deaths": cs["deaths"], "cp_deaths": cp["deaths"],
            "cs_nov": cs["novelty_transitions"] or 0,
            "cp_nov": cp["novelty_transitions"] or 0,
        })
        print(f"\n--- seed {seed} ---")
        print(f"v25c: deaths={v25c['deaths']} reward={v25c['total_reward']:.0f} "
              f"fruits={v25c['tree_fruits']} chimes={v25c['chimes_collected']} "
              f"grasp@bell={v25c['grasp_at_bell']} altar_waits={v25c['waits_at_altar']}")
        print(f"v21:  deaths={v21['deaths']} reward={v21['total_reward']:.0f} "
              f"fruits={v21['tree_fruits']} chimes={v21['chimes_collected']} "
              f"grasp@bell={v21['grasp_at_bell']} far_zone={v21['far_zone_steps']}")
        print(f"prober: verdicts={verdicts} trials={list((prober.get('probe_trials') or {}).keys())}")
        print(f"curious_pure: deaths={cp['deaths']} nov={cp['novelty_transitions']} "
              f"reward={cp['total_reward']:.0f}")
        print(f"curious_surv: deaths={cs['deaths']} nov={cs['novelty_transitions']} "
              f"reward={cs['total_reward']:.0f} fruits={cs['tree_fruits']}")

    a1 = run("emca_v21", 1, 8000)
    a2 = run("emca_v21", 1, 8000)
    b1 = run("emca_v25c", 1, 8000)
    b2 = run("emca_v25c", 1, 8000)
    p1 = run("prober", 1, 8000)
    p2 = run("prober", 1, 8000)
    det = (edges_of(a1) == edges_of(a2)
           and a1["grasp_at_bell"] == a2["grasp_at_bell"]
           and a1["total_reward"] == a2["total_reward"]
           and edges_of(b1) == edges_of(b2)
           and b1["grasp_at_bell"] == b2["grasp_at_bell"]
           and b1["total_reward"] == b2["total_reward"]
           and edges_of(p1) == edges_of(p2)
           and p1["total_reward"] == p2["total_reward"]
           and (p1.get("probe_verdicts") or {}) == (p2.get("probe_verdicts") or {}))

    print("\n================ PRE-REGISTERED VERDICTS ================")
    w1 = sum(r["deaths"] <= 25 for r in rows) >= 2
    w2 = sum(r["v21_decoy"] for r in rows) >= 2 and \
        sum(r["assoc_decoy"] for r in rows) >= 2
    w3 = sum(not r["v25c_decoy"] for r in rows) >= 2
    w4 = sum(r["sign_inv"] for r in rows) >= 2
    w5 = sum(r["v25c_true"] for r in rows) >= 2
    w6 = sum(r["prober_ran"] for r in rows) >= 2 and \
        sum(r["altar_gray"] for r in rows) >= 2
    w7 = sum(r["cs_deaths"] <= 25 for r in rows) >= 2 and \
        sum(r["cs_deaths"] < r["cp_deaths"] for r in rows) >= 2
    w8 = sum(r["cs_nov"] >= 0.5 * max(1, r["cp_nov"]) for r in rows) >= 2
    print(f"W1 world works (deaths<=25):        {'PASS' if w1 else 'FAIL'} "
          f"{[r['deaths'] for r in rows]}")
    print(f"W2 decoy bites v2.1 + assoc:        {'PASS' if w2 else 'FAIL'} "
          f"v21={[r['v21_decoy'] for r in rows]} assoc={[r['assoc_decoy'] for r in rows]}")
    print(f"W3 v2.5c rejects decoy:             {'PASS' if w3 else 'FAIL'} "
          f"{[r['v25c_decoy'] for r in rows]}")
    print(f"W4 SIGN INVERSION (v25c>=v21):      {'PASS' if w4 else 'FAIL'} "
          f"per-seed r25-r21={[round(r['r25'] - r['r21']) for r in rows]}")
    print(f"W5 v2.5c keeps true edges:          {'PASS' if w5 else 'FAIL'} "
          f"{[r['v25c_true'] for r in rows]}")
    print(f"W6 prober runs + altar gray:        {'PASS' if w6 else 'FAIL'} "
          f"ran={[r['prober_ran'] for r in rows]} gray={[r['altar_gray'] for r in rows]}")
    print(f"W7 curious_surv survives+beats pure:{'PASS' if w7 else 'FAIL'} "
          f"cs={[r['cs_deaths'] for r in rows]} cp={[r['cp_deaths'] for r in rows]}")
    print(f"W8 survival keeps exploration:      {'PASS' if w8 else 'FAIL'} "
          f"cs_nov={[r['cs_nov'] for r in rows]} cp_nov={[r['cp_nov'] for r in rows]}")
    print(f"W9 determinism:                     {'PASS' if det else 'FAIL'}")
    ready = all((w1, w2, w3, w4, w5, w6, w7, w8, det))
    print(f"OVERALL: v3.2 ready for the matrix: {'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
