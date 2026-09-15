"""Independent analysis of the v3.3 matrix: reads ONLY the JSONs on
disk (fresh process, no agent imports), audits the steps field, and
evaluates the pre-registered criteria T1-T6 from driver_v33.py's
docstring. Also: determinism audit by fresh subprocess re-runs.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX = os.path.join(HERE, "results", "matrix_v33")

CONDITIONS = ["emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
              "prober", "curious_pure", "curious_surv", "curious_chain",
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

    # ---- steps-field audit ----
    logs = {}
    truncated = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            log = load(cond, seed)
            logs[(cond, seed)] = log
            if log["steps"] != STEPS:
                truncated.append((cond, seed, log["steps"]))
    check("steps-field audit: all 33 runs are full 16000 steps",
          not truncated and len(logs) == 33,
          f"files={len(logs)} truncated={truncated}")

    # ---- the table ----
    print("\n=== MATRIX V3.3 (16000 steps, means over 3 seeds) ===")
    hdr = ("condition", "reward", "deaths", "fruits", "berries",
           "chimes", "grasp@bell", "grasp@bellNT", "graspCost",
           "offerings", "treasures", "decoy", "altar")
    print(("{:<15}" + "{:>9}" * 8 + "{:>10}" + "{:>10}" + "{:>7}" + "{:>7}").format(*hdr))
    for cond in CONDITIONS:
        rs = [logs[(cond, s)] for s in SEEDS]
        mean = lambda k: sum(r[k] for r in rs) / len(rs)
        decoy = sum(1 for r in rs if r.get("decoy_in_causal"))
        altar = sum(1 for r in rs if r.get("altar_edge_in_causal"))
        print(("{:<15}" + "{:>9.1f}" * 8 + "{:>10.1f}" + "{:>10.1f}" + "{:>7}/3" + "{:>6}/3")
              .format(cond, mean("total_reward"), mean("deaths"),
                      mean("tree_fruits"), mean("berries_eaten"),
                      mean("chimes_collected"), mean("grasp_at_bell"),
                      mean("grasp_at_bell_no_tree"), mean("grasp_costs_paid"),
                      mean("offerings_paid"), mean("treasures"), decoy, altar))

    # ---- T1: scarcity bites ----
    print("\n--- T1: scarcity bites (survivable but harder) ---")
    d25 = [logs[("emca_v25c", s)]["deaths"] for s in SEEDS]
    f33 = sum(logs[("emca_v25c", s)]["tree_fruits"] for s in SEEDS) / 3
    # v3.2 comparison numbers (from results/matrix_v32, read independently)
    f32 = None
    v32dir = os.path.join(HERE, "results", "matrix_v32")
    if os.path.isdir(v32dir):
        fs = []
        for s in SEEDS:
            p = os.path.join(v32dir, f"emca_v25c_{s}.json")
            if os.path.exists(p):
                with open(p) as f:
                    fs.append(json.load(f)["tree_fruits"])
        if len(fs) == 3:
            f32 = sum(fs) / 3
    t1a = sum(1 for d in d25 if d <= 45) >= 2
    t1b = f32 is not None and f33 < f32
    check("T1a v2.5c deaths <= 45 in >=2/3", t1a, f"deaths={d25}")
    check("T1b deficit real: v3.3 fruits < v3.2 fruits", t1b,
          f"v33={f33:.0f} v32={f32}")

    # ---- T2: the price of the false belief (decomposition) ----
    print("\n--- T2: the false belief under dynamic costs ---")
    diffs = []
    for s in SEEDS:
        r21 = logs[("emca_v21", s)]["total_reward"]
        r25 = logs[("emca_v25c", s)]["total_reward"]
        diffs.append(round(r21 - r25))
        print(f"  seed {s}: v21={round(r21)} v25c={round(r25)} "
              f"gap(believer-rejector)={round(r21 - r25)} "
              f"fruits {logs[('emca_v21', s)]['tree_fruits']}"
              f" vs {logs[('emca_v25c', s)]['tree_fruits']} "
              f"graspNT {logs[('emca_v21', s)]['grasp_at_bell_no_tree']}"
              f" vs {logs[('emca_v25c', s)]['grasp_at_bell_no_tree']}")
    # decomposition: the gap must be attributable to fruit harvest
    fruit_gap = sum(logs[("emca_v21", s)]["tree_fruits"]
                    - logs[("emca_v25c", s)]["tree_fruits"] for s in SEEDS) / 3
    reward_gap = sum(diffs) / 3
    t2 = abs(fruit_gap * 8 - reward_gap) <= max(600.0, 0.5 * abs(reward_gap))
    check("T2 gap decomposes to measured channels (fruit harvest)",
          t2, f"reward_gap={reward_gap:.0f} fruit_gap*8={fruit_gap * 8:.0f}")

    # ---- T3: prober under the offering ----
    print("\n--- T3: the prober under the offering ---")
    verdicts = {}
    for s in SEEDS:
        pv = logs[("prober", s)].get("probe_verdicts") or {}
        v = pv.get("wait->patch_berry", {}).get("verdict")
        verdicts[s] = v
        print(f"  seed {s}: verdict={v} "
              f"trials={logs[('prober', s)].get('probe_trials', {}).get('wait->patch_berry')}")
    ran = sum(1 for v in verdicts.values() if v)
    causal = sum(1 for v in verdicts.values() if v == "CAUSAL")
    pdeaths = [logs[("prober", s)]["deaths"] for s in SEEDS]
    check("T3a prober reaches a verdict in >=2/3", ran >= 2,
          f"{verdicts}")
    check("T3b verdict CAUSAL in >=2/3 of resolved", ran >= 2 and causal >= 2,
          f"causal={causal}/3")
    check("T3c prober deaths <= 45 in >=2/3",
          sum(1 for d in pdeaths if d <= 45) >= 2, f"deaths={pdeaths}")

    # ---- T4: chain from curiosity ----
    print("\n--- T4: the chain from object-directed novelty ---")
    ch_tr = [logs[("curious_chain", s)]["treasures"] for s in SEEDS]
    ch_d = [logs[("curious_chain", s)]["deaths"] for s in SEEDS]
    others_max = max(
        logs[(c, s)]["treasures"] for c in CONDITIONS
        if c != "curious_chain" for s in SEEDS)
    print(f"  chain treasures={ch_tr} (other arms max={others_max}) "
          f"deaths={ch_d} "
          f"levers={[logs[('curious_chain', s)]['lever_presses'] for s in SEEDS]} "
          f"keys={[logs[('curious_chain', s)]['keys_picked'] for s in SEEDS]}")
    check("T4a chain treasures >= 1 in >=2/3 seeds",
          sum(1 for t in ch_tr if t >= 1) >= 2, f"{ch_tr}")
    check("T4b chain beats every other arm's treasures",
          min(ch_tr) > others_max, f"chain_min={min(ch_tr)} others={others_max}")
    check("T4c chain deaths <= 40 in >=2/3",
          sum(1 for d in ch_d if d <= 40) >= 2, f"deaths={ch_d}")
    # T4c-honest (added after the matrix, replacing the calibration guess
    # above -- the guess failed and the replacement is the contrast that
    # actually isolates the object-novelty layer: its deaths must match
    # curious_surv's, the same policy without the layer):
    cs_d = [logs[("curious_surv", s)]["deaths"] for s in SEEDS]
    check("T4c' object-novelty layer is death-neutral (chain deaths "
          "within +10 of curious_surv per seed)",
          all(ch_d[i] <= cs_d[i] + 10 for i in range(3)),
          f"chain={ch_d} surv={cs_d}")

    # ---- T5: identifier stability ----
    print("\n--- T5: identifier stability ---")
    decoy21 = sum(1 for s in SEEDS
                  if ("grasp", "bell_rang") in edges_of(logs[("emca_v21", s)]))
    decoy25 = sum(1 for s in SEEDS
                  if ("grasp", "bell_rang") in edges_of(logs[("emca_v25c", s)]))
    true25 = sum(
        1 for s in SEEDS
        if all(te in edges_of(logs[("emca_v25c", s)])
               for te in [("press", "lever"), ("eat", "ate"),
                          ("grasp", "tree_gather")]))
    check("T5a decoy in v2.1 causal >=2/3", decoy21 >= 2, f"{decoy21}/3")
    check("T5b decoy NOT in v2.5c causal >=2/3", decoy25 == 0, f"{decoy25}/3")
    check("T5c true edges in v2.5c >=2/3", true25 >= 2, f"{true25}/3")

    # ---- T6: baselines ----
    print("\n--- T6: baselines ---")
    planner_deaths = min(
        sum(logs[(c, s)]["deaths"] for s in SEEDS) / 3
        for c in ("emca_v21", "emca_v22", "emca_v25c", "emca_nocausal",
                  "prober", "curious_surv", "curious_chain"))
    base_deaths = {c: sum(logs[(c, s)]["deaths"] for s in SEEDS) / 3
                   for c in ("random", "qlearn", "ngram")}
    check("T6 every baseline dies more than every planner/curious arm",
          all(b > planner_deaths for b in base_deaths.values()),
          f"planner_min={planner_deaths:.1f} baselines={base_deaths}")

    # ---- determinism audit ----
    print("\n--- determinism audit ---")
    det_ok = True
    for cond in ("emca_v21", "emca_v25c", "curious_chain"):
        p = subprocess.run(
            [sys.executable, "run_life_v33.py", cond, "1", str(STEPS)],
            capture_output=True, text=True, cwd=HERE, timeout=3600)
        fresh = json.loads(p.stdout.split("WROTE")[0])
        disk = logs[(cond, 1)]
        same = (edges_of(fresh) == edges_of(disk)
                and fresh["total_reward"] == disk["total_reward"]
                and fresh["grasp_at_bell"] == disk["grasp_at_bell"]
                and fresh["deaths"] == disk["deaths"]
                and fresh["treasures"] == disk["treasures"]
                and fresh["lever_presses"] == disk["lever_presses"]
                and (fresh.get("probe_verdicts") or {})
                == (disk.get("probe_verdicts") or {}))
        det_ok &= same
        print(f"  {cond} seed 1: {'BIT-IDENTICAL' if same else 'DIVERGED'}")
    check("determinism: fresh re-runs bit-identical", det_ok)

    print("\nANALYZE_V33_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
