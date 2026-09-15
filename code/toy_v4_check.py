"""Toy check for TerrariumV4 (TZ.md rule: before the full matrix,
REAL agents must show the world does what the directive requires).
8000 steps, 3 seeds.

PRE-REGISTERED CRITERIA (written before the first run of this file):

  W1 the decoy baits the believer: (grasp, torch_lit) in v4_believer
     causal edges in >=2/3 seeds (the linger mechanism must reach the
     identifier through the agents' own foraging).
  W2 the rejector rejects: the decoy NOT in v4_rejector causal in
     >=2/3 seeds; true edges (eat->ate, grasp->tree_gather) present
     in >=2/3.
  W3 the false belief is ACTIVE in behaviour: the believer's torch
     goal consumes more steps (goal-monopolisation channel) AND fires
     empty grasps inside the brazier pocket (grasps_near_torch) than
     the rejector. PASS if in >=2/3 seeds the believer's pocket-grasp
     count > the rejector's (the decoy edge firing grasp where the
     flame is) -- reported per-seed with the torch-goal step counts
     (the goal-tax channel) regardless of PASS.
  W4 the chain works through planning: v4_rejector or v4_assoc eats
     >=1 treasury meal in >=1 seed at 8000 steps (the route: torch
     goal -> stand on brazier -> treasury scent; the world must
     let the planner's OWN machinery reach the food).
  W5 curiosity is bitter: v4_pure (pure novelty) deaths > every
     planner arm's deaths in >=2/3 seeds; v4_curious deaths >=
     v4_rejector deaths in >=2/3 (the pocket's novelty pull costs).
  W6 the baselines die: random deaths > all planner arms.
  W7 determinism: seed-1 re-run of v4_believer identical counters.
  W8 no None actions in any arm (harness sanity).
"""
import json

from run_life_v4 import run

ARMS = ["v4_believer", "v4_spec", "v4_assoc", "v4_rejector",
        "v4_curious", "v4_pure", "random"]


def main():
    print("toy_v4_check.py -- real agents on TerrariumV4, 8000 steps, 3 seeds")
    print("=" * 72)
    rows = {}
    for seed in (1, 2, 3):
        for arm in ARMS:
            log = run(arm, seed, 8000)
            rows[(arm, seed)] = log
            print(f"seed {seed} {arm:12s} reward={log['total_reward']:8.0f} "
                  f"deaths={log['deaths']:3d} fruits={log['tree_fruits']:4d} "
                  f"torch={log['torches_collected']:3d} "
                  f"treasury={log['treasury_eaten']:3d} "
                  f"scorch={log['scorch_paid']:7.1f} "
                  f"gnt={log['grasps_near_torch']:4d} "
                  f"decoy_c={log.get('decoy_torch_in_causal')}")
    print("=" * 72)
    # W1
    w1 = sum(1 for s in (1, 2, 3) if rows[("v4_believer", s)]["decoy_torch_in_causal"])
    print(f"W1 decoy in believer causal: {w1}/3 "
          + ("PASS" if w1 >= 2 else "FAIL"))
    # W2
    w2a = sum(1 for s in (1, 2, 3)
              if not rows[("v4_rejector", s)]["decoy_torch_in_causal"])
    w2b = sum(1 for s in (1, 2, 3)
              if rows[("v4_rejector", s)]["true_in_causal"].get("eat->ate")
              and rows[("v4_rejector", s)]["true_in_causal"].get("grasp->tree_gather"))
    print(f"W2 rejector rejects {w2a}/3, true edges {w2b}/3 "
          + ("PASS" if w2a >= 2 and w2b >= 2 else "FAIL"))
    # W3
    diffs = [(s, rows[("v4_believer", s)]["grasps_near_torch"],
              rows[("v4_rejector", s)]["grasps_near_torch"],
              rows[("v4_believer", s)]["scorch_paid"],
              rows[("v4_rejector", s)]["scorch_paid"],
              rows[("v4_believer", s)]["torch_goal_steps"],
              rows[("v4_rejector", s)]["torch_goal_steps"]) for s in (1, 2, 3)]
    w3 = sum(1 for s, b, rj, sb, sr, tb, tr in diffs if b > rj)
    print("W3 belief active (pocket grasps believer vs rejector): "
          + "; ".join(f"s{s}: {b}v{rj} grasps, {sb}v{sr} scorch, "
                      f"torch-goal {tb}v{tr}"
                      for s, b, rj, sb, sr, tb, tr in diffs)
          + f" -> {w3}/3 " + ("PASS" if w3 >= 2 else "FAIL"))
    # W4
    w4 = sum(1 for arm in ("v4_rejector", "v4_assoc")
             for s in (1, 2, 3) if rows[(arm, s)]["treasury_eaten"] >= 1)
    print(f"W4 treasury meal through planning: {w4} arms x seeds with >=1 "
          + ("PASS" if w4 >= 1 else "FAIL"))
    # W5
    w5a = sum(1 for s in (1, 2, 3)
              if rows[("v4_pure", s)]["deaths"] >
              max(rows[(a, s)]["deaths"] for a in
                  ("v4_believer", "v4_rejector", "v4_assoc")))
    w5b = sum(1 for s in (1, 2, 3)
              if rows[("v4_curious", s)]["deaths"] >=
              rows[("v4_rejector", s)]["deaths"])
    print(f"W5 pure novelty dies hardest {w5a}/3, curious >= rejector {w5b}/3 "
          + ("PASS" if w5a >= 2 and w5b >= 2 else "FAIL"))
    # W6
    w6 = sum(1 for s in (1, 2, 3)
             if rows[("random", s)]["deaths"] >
             max(rows[(a, s)]["deaths"] for a in
                 ("v4_believer", "v4_rejector", "v4_assoc")))
    print(f"W6 random dies most {w6}/3 " + ("PASS" if w6 >= 3 else "FAIL"))
    # W7
    rerun = run("v4_believer", 1, 8000)
    a, b = rows[("v4_believer", 1)], rerun
    same = all(a[k] == b[k] for k in ("total_reward", "deaths", "tree_fruits",
                                      "torches_collected", "scorch_paid",
                                      "grasps_near_torch"))
    same_edges = {(x, y) for x, y, p in a["causal_edges"]} == \
        {(x, y) for x, y, p in b["causal_edges"]}
    print("W7 determinism re-run: " + ("PASS" if same and same_edges else "FAIL"))
    # W8
    w8 = all(not rows[(a, s)]["harness_notes"] for a in ARMS for s in (1, 2, 3))
    print("W8 no None actions: " + ("PASS" if w8 else "FAIL"))


if __name__ == "__main__":
    main()
