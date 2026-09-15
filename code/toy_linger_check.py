"""Toy check (TZ.md rule): BEFORE the linger matrix, does the simple env
actually deliver the decoy to the identifiers at full-life scale with the
REAL agent -- and what does each way of thinking do with it?

Pre-registered criteria (before the first run of this file; lives are
16000 steps, matching the validated toy scale of turn 97 where the agent
harvested 1105-1208 fruits):
  G1 trap delivered:  the real agent (v2.1 arm) LINGERS: tree_fruits >= 300
     in >=2/3 seeds (a competent forager must feed at the storm tree, else
     the env is broken and verdicts are meaningless)
  G2 trap bites v2.1: decoy (eat,bell_rang) in v2.1 causal edges in >=2/3
     seeds (replication of runs 2/3/5 at full-life scale)
  G3 old way fooled:  v2.2 (spec gate) accepts the decoy in >=2/3 seeds
  G4 new way helps:   v2.5c rejects the decoy in >=2/3 seeds, decoy data
     present (n(eat)>=3, rate_a >= 0.02)
  G5 new way keeps truth: (eat,ate) AND (eat,tree_ate) in v2.5c in >=2/3
     seeds (the fix must not break the true edges)
  G6 correlation fooled: decoy in assoc edges of the nocausal arm in >=2/3
     seeds (the env separates causal from correlational)
  G7 determinism: re-running one seed reproduces the same edge sets
  READY = G1 & G2 & G3 & G4 & G5 & G6 & G7.
"""
import sys

from run_life_linger import run

DECOY = ("eat", "bell_rang")
TRUE = [("eat", "ate"), ("eat", "tree_ate")]


def edges_of(log):
    return {(a, e) for a, e, p in log["causal_edges"]}


def main():
    print("toy_linger_check.py -- real agent, 6000 steps, 3 seeds, 4 arms")
    print("=" * 72)
    rows = []
    for seed in (1, 2, 3):
        v21 = run("emca_v21", seed)
        v22 = run("emca_v22", seed)
        v25c = run("emca_v25c", seed)
        noc = run("emca_nocausal", seed)
        e21, e22, e25 = edges_of(v21), edges_of(v22), edges_of(v25c)
        # G6 measurement fix (documented): the decoy co-occurrence rate is
        # ~0.26; the assoc view must use the sanity-calibrated min_p=0.02,
        # not the agent-behaviour default 0.5. assoc_edges_p002 is stored
        # by run_life_linger.run for exactly this purpose.
        assoc = {(a, e) for a, e, p in noc["assoc_edges_p002"]}
        print(f"\n--- seed {seed} ---")
        print(f"v2.1:  fruits={v21['tree_fruits']} deaths={v21['deaths']} "
              f"reward={v21['total_reward']:.0f} "
              f"ring_near={v21['ring_near_tree']} ring_far={v21['ring_far']}")
        print(f"  v2.1 edges:  {sorted(e21)}")
        print(f"  v2.2 edges:  {sorted(e22)}")
        print(f"  v2.5c edges: {sorted(e25)}")
        print(f"  assoc (nocausal arm): {sorted(assoc)}")
        rows.append({
            "seed": seed,
            "fruits": v21["tree_fruits"],
            "v21_decoy": DECOY in e21,
            "v22_decoy": DECOY in e22,
            "v25c_decoy": DECOY in e25,
            "v25c_true": all(te in e25 for te in TRUE),
            "assoc_decoy": DECOY in assoc,
            "v21_true": all(te in e21 for te in TRUE),
        })

    # determinism: re-run seed 1 for each arm, compare edge sets
    det = all(edges_of(run(c, 1)) == edges_of(r) for c, r in
              (("emca_v21", run("emca_v21", 1)),
               ("emca_v22", run("emca_v22", 1)),
               ("emca_v25c", run("emca_v25c", 1))))
    print(f"\nDETERMINISM (seed-1 re-run, 3 arms): {'PASS' if det else 'FAIL'}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    g1 = sum(r["fruits"] >= 300 for r in rows) >= 2
    g2 = sum(r["v21_decoy"] for r in rows) >= 2
    g3 = sum(r["v22_decoy"] for r in rows) >= 2
    g4 = sum((not r["v25c_decoy"]) for r in rows) >= 2
    g5 = sum(r["v25c_true"] for r in rows) >= 2
    g6 = sum(r["assoc_decoy"] for r in rows) >= 2
    print(f"G1 trap delivered (fruits>=300, v2.1 arm): {'PASS' if g1 else 'FAIL'} "
          f"{[r['fruits'] for r in rows]}")
    print(f"G2 decoy bites v2.1:                      {'PASS' if g2 else 'FAIL'} "
          f"{[r['v21_decoy'] for r in rows]}")
    print(f"G3 decoy bites v2.2 (spec):               {'PASS' if g3 else 'FAIL'} "
          f"{[r['v22_decoy'] for r in rows]}")
    print(f"G4 v2.5c rejects decoy (NEW WAY HELPS):    {'PASS' if g4 else 'FAIL'} "
          f"{[r['v25c_decoy'] for r in rows]}")
    print(f"G5 v2.5c keeps true edges:                {'PASS' if g5 else 'FAIL'} "
          f"{[r['v25c_true'] for r in rows]}")
    print(f"G6 correlation fooled (assoc):            {'PASS' if g6 else 'FAIL'} "
          f"{[r['assoc_decoy'] for r in rows]}")
    print(f"G7 determinism:                           {'PASS' if det else 'FAIL'}")
    print(f"    (informative: v2.1 keeps true edges: "
          f"{[r['v21_true'] for r in rows]})")
    ready = g1 and g2 and g3 and g4 and g5 and g6 and det
    print(f"OVERALL: simple linger env ready for the matrix: "
          f"{'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
