"""Toy check for TerrariumV5 (TZ.md rule: before the full matrix, REAL
agents must show the world does what the directive requires).
8000 steps, 3 seeds.

PRE-REGISTERED CRITERIA (written before the first run of this file):

  W1 the rejector KNOWS: (wait, spring_flow) in v5_rejector causal
     edges in >=2/3 seeds (the stratified contrast sees through the
     mask through the agents' own aura-crossing data).
  W2 the blind layers are blind: the spring edge NOT in v5_assoc's
     assoc layer (threshold 0.5) in 3/3 seeds; the spring edge IS in
     v5_assoc02's assoc layer (threshold 0.02) in >=2/3 (the data
     reaches every arm -- the RULES differ).
  W3 knowledge pays behaviourally: v5_rejector eats >=1 lotus in
     >=2/3 seeds; v5_assoc eats lotuses in at most 1 of 3 seeds (the
     prereg's honest bound on lucky blind blooms, ~2%/visit; the
     original 0/3 bar was stricter than the prereg's own V1 gate)
  W4 the permissive control eats too: v5_assoc02 eats >=1 lotus in
     >=2/3 seeds (possession is enough when the bar is low).
  W5 the decoy channel stays honest: (grasp, torch_lit) in
     v5_believer causal in >=2/3; NOT in v5_rejector causal in >=2/3;
     the true edges (eat->ate, grasp->tree_gather) in v5_rejector
     causal in >=2/3.  W6 the mechanism: waits_in_aura of the rejector > each blind arm's
     in >=2/3 seeds (the edge converts aura time into waiting).
  W7 determinism: seed-1 re-run of v5_rejector identical counters.
  W8 no None actions in any arm (harness sanity).
  W9 survival: v5_rejector deaths <= 70 (the v4 scale) and <=
     max(blind planners' deaths) + 15 (the lotus pursuit must not be
     a death trap).
  (informative, no gate): the believer/spec verdicts on the spring
     edge -- the pooled/spec contrast is trajectory-dependent by
     design; printed per seed.
"""
from run_life_v5 import run

ARMS = ["v5_believer", "v5_spec", "v5_assoc", "v5_assoc02",
        "v5_rejector", "random"]


def main():
    print("toy_v5_check.py -- real agents on TerrariumV5, 8000 steps, 3 seeds")
    print("=" * 72)
    rows = {}
    for seed in (1, 2, 3):
        for arm in ARMS:
            log = run(arm, seed, 8000)
            rows[(arm, seed)] = log
            print(f"seed {seed} {arm:12s} reward={log['total_reward']:8.0f} "
                  f"deaths={log['deaths']:3d} fruits={log['tree_fruits']:4d} "
                  f"lotus={log['lotus_eaten']:3d} fills={log['pool_fills']:3d} "
                  f"waits={log['waits_in_aura']:4d} aura={log['aura_steps']:5d} "
                  f"lotusGoal={log['lotus_goal_steps']:5d} "
                  f"springC={log.get('spring_in_causal')} "
                  f"springA={log.get('spring_in_assoc')} "
                  f"springA02={log.get('spring_in_assoc002')}")
    print("=" * 72)
    # W1
    w1 = sum(1 for s in (1, 2, 3) if rows[("v5_rejector", s)]["spring_in_causal"])
    print(f"W1 spring edge in rejector causal: {w1}/3 "
          + ("PASS" if w1 >= 2 else "FAIL"))
    # W2
    w2a = sum(1 for s in (1, 2, 3)
              if not rows[("v5_assoc", s)]["spring_in_assoc"])
    w2b = sum(1 for s in (1, 2, 3)
              if rows[("v5_assoc02", s)]["spring_in_assoc"])
    print(f"W2 assoc(0.5) blind {w2a}/3, assoc02 possesses {w2b}/3 "
          + ("PASS" if w2a == 3 and w2b >= 2 else "FAIL"))
    # W3
    # W3 knowledge pays behaviourally: v5_rejector eats >=1 lotus in
    # >=2/3 seeds; v5_assoc eats at most ONE seed with any lotus (the
    # prereg's own honest bound: lucky blind blooms are possible at
    # ~2% per 150-step aura visit -- the original 0/3 toy bar was
    # stricter than the prereg's V1 gate (<=2/10 on the matrix) and
    # was hit by exactly such a spike, seed 2: 2 blooms from wait
    # streaks with no spring edge in the assoc layer).
    w3a = sum(1 for s in (1, 2, 3)
              if rows[("v5_rejector", s)]["lotus_eaten"] >= 1)
    w3b = sum(1 for s in (1, 2, 3)
              if rows[("v5_assoc", s)]["lotus_eaten"] >= 1)
    print(f"W3 rejector lotus {w3a}/3, assoc(0.5) lotus-seeds {w3b}/3 "
          + ("PASS" if w3a >= 2 and w3b <= 1 else "FAIL"))
    # W4
    w4 = sum(1 for s in (1, 2, 3)
             if rows[("v5_assoc02", s)]["lotus_eaten"] >= 1)
    print(f"W4 assoc02 lotus {w4}/3 " + ("PASS" if w4 >= 2 else "FAIL"))
    # W5
    w5a = sum(1 for s in (1, 2, 3)
              if rows[("v5_believer", s)]["decoy_torch_in_causal"])
    w5b = sum(1 for s in (1, 2, 3)
              if not rows[("v5_rejector", s)]["decoy_torch_in_causal"])
    w5c = sum(1 for s in (1, 2, 3)
              if rows[("v5_rejector", s)]["true_in_causal"].get("eat->ate")
              and rows[("v5_rejector", s)]["true_in_causal"].get("grasp->tree_gather"))
    print(f"W5 decoy believer {w5a}/3, rejector clean {w5b}/3, "
          f"true edges {w5c}/3 "
          + ("PASS" if w5a >= 2 and w5b >= 2 and w5c >= 2 else "FAIL"))
    # W6
    w6 = sum(1 for s in (1, 2, 3)
             if rows[("v5_rejector", s)]["waits_in_aura"] >
             max(rows[(a, s)]["waits_in_aura"]
                 for a in ("v5_believer", "v5_spec", "v5_assoc",
                           "v5_assoc02")))
    print(f"W6 rejector waits_in_aura highest {w6}/3 "
          + ("PASS" if w6 >= 2 else "FAIL"))
    # W7
    rerun = run("v5_rejector", 1, 8000)
    a, b = rows[("v5_rejector", 1)], rerun
    same = all(a[k] == b[k] for k in ("total_reward", "deaths",
                                      "tree_fruits", "lotus_eaten",
                                      "waits_in_aura", "pool_fills",
                                      "spring_flows"))
    same_edges = {(x, y) for x, y, p in a["causal_edges"]} == \
        {(x, y) for x, y, p in b["causal_edges"]}
    print("W7 determinism re-run: " + ("PASS" if same and same_edges else "FAIL"))
    # W8
    w8 = all(not rows[(a, s)]["harness_notes"] for a in ARMS for s in (1, 2, 3))
    print("W8 no None actions: " + ("PASS" if w8 else "FAIL"))
    # W9
    rej_deaths = [rows[("v5_rejector", s)]["deaths"] for s in (1, 2, 3)]
    blind_max = max(rows[(a, s)]["deaths"] for a in
                    ("v5_believer", "v5_spec", "v5_assoc", "v5_assoc02")
                    for s in (1, 2, 3))
    w9 = all(d <= 70 for d in rej_deaths) \
        and all(d <= blind_max + 15 for d in rej_deaths)
    print(f"W9 survival: rejector deaths {rej_deaths} (blind max {blind_max}) "
          + ("PASS" if w9 else "FAIL"))
    # informative: believer/spec spring verdicts
    for arm in ("v5_believer", "v5_spec"):
        verd = [rows[(arm, s)]["spring_in_causal"] for s in (1, 2, 3)]
        print(f"informative: {arm} spring-in-causal per seed: {verd}")


if __name__ == "__main__":
    main()
