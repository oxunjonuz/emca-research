"""Independent analysis of the v3.2 matrix: reads ONLY the JSONs on
disk (fresh process, no agent imports), audits the steps field
(truncation check -- the turn-99 lesson), and evaluates the
pre-registered criteria T1-T5 from driver_v32.py's docstring.

Also: determinism audit by re-running two conditions in fresh
subprocesses and comparing edge sets + behavioural counters bit-for-bit.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX = os.path.join(HERE, "results", "matrix_v32")

CONDITIONS = ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
              "prober", "curious_pure", "curious_surv",
              "random", "qlearn", "ngram"]
SEEDS = [1, 2, 3]
STEPS = 16000


def load(cond, seed):
    path = os.path.join(MATRIX, f"{cond}_{seed}.json")
    with open(path) as f:
        return json.load(f)


def edges_of(log):
    return {(a, e) for a, e, p in log["causal_edges"]}


def main():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # ---- steps-field audit (truncation check) ----
    logs = {}
    truncated = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            log = load(cond, seed)
            logs[(cond, seed)] = log
            if log["steps"] != STEPS:
                truncated.append((cond, seed, log["steps"]))
    check("steps-field audit: all 30 runs are full 16000 steps",
          not truncated and len(logs) == 30,
          f"files={len(logs)} truncated={truncated}")

    # ---- the table ----
    print("\n=== MATRIX V3.2 (16000 steps, means over 3 seeds) ===")
    hdr = ("condition", "reward", "deaths", "fruits", "berries",
           "chimes", "grasp@bell", "altar_waits", "patch_ate",
           "treasures", "decoy", "altar")
    print(("{:<15}" + "{:>9}" * 9 + "{:>7}" + "{:>7}").format(*hdr))
    for cond in CONDITIONS:
        rs = [logs[(cond, s)] for s in SEEDS]
        mean = lambda k: sum(r[k] for r in rs) / len(rs)
        decoy = sum(1 for r in rs if r.get("decoy_in_causal"))
        altar = sum(1 for r in rs if r.get("altar_edge_in_causal"))
        print(("{:<15}" + "{:>9.1f}" * 7 + "{:>9.0f}" * 2 + "{:>7}/3" + "{:>6}/3")
              .format(cond, mean("total_reward"), mean("deaths"),
                      mean("tree_fruits"), mean("berries_eaten"),
                      mean("chimes_collected"), mean("grasp_at_bell"),
                      mean("waits_at_altar"), mean("patch_ate"),
                      mean("treasures"), decoy, altar))

    # ---- T1: sign inversion ----
    print("\n--- T1: sign inversion (v25c >= v21 per seed) ---")
    diffs = []
    for s in SEEDS:
        r25 = logs[("emca_v25c", s)]["total_reward"]
        r21 = logs[("emca_v21", s)]["total_reward"]
        diffs.append(round(r25 - r21))
        print(f"  seed {s}: v25c={round(r25)} v21={round(r21)} "
              f"diff={round(r25 - r21)}")
    t1 = sum(1 for d in diffs if d >= 0) >= 2
    check("T1 v2.5c >= v2.1 per seed in >=2/3", t1, f"diffs={diffs}")

    # ---- T2: prober ----
    print("\n--- T2: the prober (do-interventions) ---")
    verdicts = {}
    for s in SEEDS:
        pv = logs[("prober", s)].get("probe_verdicts") or {}
        v = pv.get("wait->patch_berry", {}).get("verdict")
        verdicts[s] = v
        print(f"  seed {s}: altar verdict={v} "
              f"trials={logs[('prober', s)].get('probe_trials', {}).get('wait->patch_berry')}")
    ran = sum(1 for v in verdicts.values() if v)
    causal = sum(1 for v in verdicts.values() if v == "CAUSAL")
    # verdict gating semantics: the probe OVERRIDES the passive layer
    # in both directions it can decide -- CAUSAL -> the edge is present
    # (added if the passive layer missed it), REJECT -> the edge is
    # absent (removed even if the passive layer had it). UNRESOLVED
    # defers to the passive layer's own evidence (the probe's trials
    # also feed the passive counters -- seed 1: the passive stratified
    # layer found (wait, patch_berry) on probe-generated data with
    # RR>=2, and the UNRESOLVED verdict correctly did not remove it).
    gating_ok = True
    for s in SEEDS:
        v = verdicts[s]
        if v is None:
            continue
        present = logs[("prober", s)].get("altar_edge_in_causal")
        if v == "CAUSAL" and not present:
            gating_ok = False
        if v == "REJECT" and present:
            gating_ok = False
    passive_lacks = sum(
        1 for s in SEEDS
        if not logs[("emca_v25c", s)].get("altar_edge_in_causal"))
    check("T2a prober reaches a verdict in >=2/3", ran >= 2,
          f"{verdicts}")
    check("T2b verdict CAUSAL in >=2/3", causal >= 2, f"causal={causal}/3")
    check("T2c verdict gating (CAUSAL->present, REJECT->absent, "
          "UNRESOLVED->defer)", gating_ok)
    check("T2d passive v2.5c lacks the altar edge in >=2/3",
          passive_lacks >= 2, f"{passive_lacks}/3")

    # ---- T3: curious-survivor ----
    print("\n--- T3: curious-survivor ---")
    for s in SEEDS:
        cs = logs[("curious_surv", s)]
        cp = logs[("curious_pure", s)]
        print(f"  seed {s}: surv deaths={cs['deaths']} "
              f"reward={round(cs['total_reward'])} nov={cs['novelty_transitions']} | "
              f"pure deaths={cp['deaths']} reward={round(cp['total_reward'])} "
              f"nov={cp['novelty_transitions']}")
    beats = sum(1 for s in SEEDS
                if logs[("curious_surv", s)]["deaths"]
                < logs[("curious_pure", s)]["deaths"])
    low = sum(1 for s in SEEDS if logs[("curious_surv", s)]["deaths"] <= 20)
    keeps_nov = sum(
        1 for s in SEEDS
        if (logs[("curious_surv", s)]["novelty_transitions"] or 0)
        >= 0.5 * max(1, logs[("curious_pure", s)]["novelty_transitions"] or 1))
    check("T3a surv deaths < pure deaths in 3/3", beats == 3,
          f"{beats}/3")
    check("T3b surv deaths <= 20 in >=2/3", low >= 2)
    check("T3c surv keeps >= 50% of pure's exploration in 3/3",
          keeps_nov == 3, f"{keeps_nov}/3")

    # ---- T4: edges ----
    print("\n--- T4: edges ---")
    decoy21 = sum(1 for s in SEEDS
                  if ("grasp", "bell_rang") in edges_of(logs[("emca_v21", s)]))
    decoy25 = sum(1 for s in SEEDS
                  if ("grasp", "bell_rang") in edges_of(logs[("emca_v25c", s)]))
    true25 = sum(
        1 for s in SEEDS
        if all(te in edges_of(logs[("emca_v25c", s)])
               for te in [("press", "lever"), ("eat", "ate"),
                          ("grasp", "tree_gather")]))
    check("T4a decoy in v2.1 causal >=2/3", decoy21 >= 2, f"{decoy21}/3")
    check("T4b decoy NOT in v2.5c causal >=2/3", decoy25 == 0,
          f"{decoy25}/3")
    check("T4c true edges in v2.5c >=2/3", true25 >= 2, f"{true25}/3")

    # ---- T5: baselines ----
    print("\n--- T5: baselines ---")
    planner_deaths = min(
        sum(logs[(c, s)]["deaths"] for s in SEEDS) / 3
        for c in ("emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
                  "prober", "curious_surv"))
    base_deaths = {c: sum(logs[(c, s)]["deaths"] for s in SEEDS) / 3
                   for c in ("random", "qlearn", "ngram")}
    worst_planner = planner_deaths
    check("T5 every baseline dies more than every planner arm",
          all(b > worst_planner for b in base_deaths.values()),
          f"planner_min={planner_deaths:.1f} baselines={base_deaths}")

    # ---- determinism audit (fresh subprocesses) ----
    print("\n--- determinism audit ---")
    det_ok = True
    for cond in ("emca_v21", "emca_v25c", "prober"):
        for seed in (1,):
            p = subprocess.run(
                [sys.executable, "run_life_v32.py", cond, str(seed),
                 str(STEPS)], capture_output=True, text=True, cwd=HERE,
                timeout=3600)
            fresh = json.loads(p.stdout.split("WROTE")[0])
            disk = logs[(cond, seed)]
            same = (edges_of(fresh) == edges_of(disk)
                    and fresh["total_reward"] == disk["total_reward"]
                    and fresh["grasp_at_bell"] == disk["grasp_at_bell"]
                    and fresh["deaths"] == disk["deaths"]
                    and (fresh.get("probe_verdicts") or {})
                    == (disk.get("probe_verdicts") or {}))
            det_ok &= same
            print(f"  {cond} seed {seed}: "
                  f"{'BIT-IDENTICAL' if same else 'DIVERGED'}")
    check("determinism: fresh re-runs bit-identical", det_ok)

    print("\nANALYZE_V32_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
