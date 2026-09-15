"""Toy check for TerrariumV6 (TZ.md rule: before the full matrix, REAL
agents must show the world does what the design requires).
8000 steps, 3 seeds.

PRE-REGISTERED CRITERIA (frozen in research/PREREG_V6.md before the
first run of this file):

  W1 the prober RESOLVES: verdict CAUSAL on (wait, spring_flow) in
     >=2/3 seeds by 8000 steps (the alternated aura blocks resolve the
     grey edge; power check: 0.30 vs 0.20 needs ~250/arm).
  W2 knowledge pays behaviourally: v6_prober eats >=1 lotus in >=2/3
     seeds; v6_rejector eats at most 1 lotus across the 3 seeds (the
     lucky-blind bound; the blind cadence never fills -- peaks 4/24).
  W3 possession farms too: v6_assoc02 eats >=1 lotus in >=2/3 (the H4
     control: possession without contrast suffices for the plan).
  W4 the decoy channel stays honest: (grasp, torch_lit) in
     v6_believer causal >=2/3; NOT in v6_rejector causal 3/3; NOT in
     v6_prober causal 3/3 (verdict-gated or never accepted).
  W5 survival: deaths(v6_prober) <= max(deaths rejector, assoc02)+10
     (probing in the cold aura must not be a death trap).
  W6 no None actions in any arm (harness sanity).
  W7 determinism: seed-1 re-run of v6_prober identical counters+edges.
  W8 (informative, no gate): the believer's spring verdicts; the
     oracle's lotus count (the gross-value device).
"""
from run_life_v6 import run

ARMS = ["v6_prober", "v6_oracle", "v6_rejector", "v6_assoc02",
        "v6_assoc", "v6_believer", "v6_nocausal", "random"]


def main():
    print("toy_v6_check.py -- real agents on TerrariumV6, 8000 steps, 3 seeds")
    print("=" * 76)
    rows = {}
    for seed in (1, 2, 3):
        for arm in ARMS:
            log = run(arm, seed, 8000)
            rows[(arm, seed)] = log
            pv = log.get("probe_verdicts") or {}
            verdict = pv.get("wait->spring_flow", {}).get("verdict", "-")
            print(f"seed {seed} {arm:13s} reward={log['total_reward']:8.0f} "
                  f"deaths={log['deaths']:3d} fruits={log['tree_fruits']:4d} "
                  f"lotus={log['lotus_eaten']:3d} waits={log['waits_in_aura']:5d} "
                  f"aura={log['aura_steps']:5d} lotusGoal={log['lotus_goal_steps']:5d} "
                  f"probe={log['probe_steps']:5d} verdict={verdict:10s} "
                  f"springC={log.get('spring_in_causal')}")
    print("=" * 76)
    # W1
    def verd(arm, s):
        pv = rows[(arm, s)].get("probe_verdicts") or {}
        return pv.get("wait->spring_flow", {}).get("verdict")
    w1 = sum(1 for s in (1, 2, 3) if verd("v6_prober", s) == "CAUSAL")
    print(f"W1 prober spring verdict CAUSAL: {w1}/3 "
          + ("PASS" if w1 >= 2 else "FAIL"))
    # W2
    w2a = sum(1 for s in (1, 2, 3)
              if rows[("v6_prober", s)]["lotus_eaten"] >= 1)
    w2b = sum(rows[("v6_rejector", s)]["lotus_eaten"] for s in (1, 2, 3))
    print(f"W2 prober lotus {w2a}/3, rejector total lotuses {w2b} "
          + ("PASS" if w2a >= 2 and w2b <= 1 else "FAIL"))
    # W3
    w3 = sum(1 for s in (1, 2, 3)
             if rows[("v6_assoc02", s)]["lotus_eaten"] >= 1)
    print(f"W3 assoc02 lotus {w3}/3 " + ("PASS" if w3 >= 2 else "FAIL"))
    # W4
    w4a = sum(1 for s in (1, 2, 3)
              if rows[("v6_believer", s)]["decoy_torch_in_causal"])
    w4b = sum(1 for s in (1, 2, 3)
              if not rows[("v6_rejector", s)]["decoy_torch_in_causal"])
    w4c = sum(1 for s in (1, 2, 3)
              if not rows[("v6_prober", s)]["decoy_torch_in_causal"])
    print(f"W4 decoy believer {w4a}/3, rejector clean {w4b}/3, "
          f"prober clean {w4c}/3 "
          + ("PASS" if w4a >= 2 and w4b == 3 and w4c == 3 else "FAIL"))
    # W5
    p_deaths = [rows[("v6_prober", s)]["deaths"] for s in (1, 2, 3)]
    ctrl_max = max(max(rows[("v6_rejector", s)]["deaths"],
                      rows[("v6_assoc02", s)]["deaths"]) for s in (1, 2, 3))
    w5 = all(d <= ctrl_max + 10 for d in p_deaths)
    print(f"W5 survival: prober deaths {p_deaths} (ctrl max {ctrl_max}) "
          + ("PASS" if w5 else "FAIL"))
    # W6
    w6 = all(not rows[(a, s)]["harness_notes"]
             for a in ARMS for s in (1, 2, 3))
    print("W6 no None actions: " + ("PASS" if w6 else "FAIL"))
    # W7
    rerun = run("v6_prober", 1, 8000)
    a, b = rows[("v6_prober", 1)], rerun
    same = all(a[k] == b[k] for k in ("total_reward", "deaths",
                                      "tree_fruits", "lotus_eaten",
                                      "waits_in_aura", "pool_fills",
                                      "spring_flows", "probe_steps"))
    same_edges = {(x, y) for x, y, p in a["causal_edges"]} == \
        {(x, y) for x, y, p in b["causal_edges"]}
    same_verd = a.get("probe_verdicts") == b.get("probe_verdicts")
    print("W7 determinism re-run: "
          + ("PASS" if same and same_edges and same_verd else "FAIL"))
    # W8 informative
    for arm in ("v6_believer", "v6_oracle"):
        ls = [rows[(arm, s)]["lotus_eaten"] for s in (1, 2, 3)]
        sc = [rows[(arm, s)]["spring_in_causal"] for s in (1, 2, 3)]
        print(f"informative: {arm} lotuses {ls}, spring-in-causal {sc}")


if __name__ == "__main__":
    main()
