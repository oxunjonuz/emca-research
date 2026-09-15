"""THE EPISTEMIC LEDGER -- turn 116 (msg_00116, the framing correction).

The owner's directive: the campaign may have silently swapped its
original goal. Separate TWO axes and never let one stand in for the
other:

  AXIS B (EPISTEMIC): can the architecture tell a real cause from a
     coincidence, truth from decoy -- INDEPENDENTLY of whether that
     knowledge pays in reward?
  AXIS A (ECONOMIC): does the knowledge buy reward net of its costs?

This script recomputes BOTH axes from the raw matrix JSONs on disk
(fresh process, no agent/env imports, no report imports). Every number
cited in research/EPISTEMIC_VERDICT.md is produced here.

Epistemic metrics per world x identifier arm:
  * decoy rejection   -- the world's false edge in the arm's causal
    layer (False = the arm is NOT fooled; the decoys: (grasp,bell_rang)
    in v3.x, (grasp,torch_lit) in v4/v5/v6);
  * true-edge retention -- the fraction of the world's true edges the
    arm's causal layer holds at end of life;
  * prober verdicts -- the ACTIVE route: CAUSAL / REJECT / UNRESOLVED
    on the world's grey or hidden true edge, and whether the prober
    ever accepted a decoy (false-positive hygiene);
  * possession-without-contrast -- assoc02 holding the true edge
    (measured, but kept separate: possession is NOT identification).

Economic metrics (recomputed, not copied from the reports):
  * the headline paired contrasts with paired bootstrap 95% CI
    (10000 resamples, fixed seed) and exact two-sided sign tests.

Output: results/epistemic_ledger.txt (frozen).
"""
import glob
import json
import math
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "epistemic_ledger.txt")

BOOT_N = 10000
BOOT_SEED = 12345

# world -> (dir, decoy key, true edges, grey/hidden edge for the prober)
WORLDS = {
    "v3.1": ("results/matrix_v31", "decoy_in_causal",
             ["press->lever", "eat->ate", "grasp->tree_gather"], None),
    "v3.2": ("results/matrix_v32", "decoy_in_causal",
             ["press->lever", "eat->ate", "grasp->tree_gather"],
             "wait->patch_berry"),
    "v3.3": ("results/matrix_v33", "decoy_in_causal",
             ["press->lever", "eat->ate", "grasp->tree_gather"],
             "wait->patch_berry"),
    "v4":   ("results/matrix_v4", "decoy_torch_in_causal",
             ["press->lever", "eat->ate", "grasp->tree_gather",
              "eat->treasury_ate"], None),
    "v5":   ("results/matrix_v5", "decoy_torch_in_causal",
             ["press->lever", "eat->ate", "grasp->tree_gather",
              "eat->treasury_ate"], "wait->spring_flow"),
    "v6":   ("results/matrix_v6", "decoy_torch_in_causal",
             ["press->lever", "eat->ate", "grasp->tree_gather",
              "eat->treasury_ate"], "wait->spring_flow"),
}

IDENTIFIER_ARMS = {
    "v3.1": {"pooled": "emca_v21", "spec": "emca_v22",
             "strat": "emca_v25c"},
    "v3.2": {"pooled": "emca_v21", "spec": "emca_v22",
             "strat": "emca_v25c", "prober": "prober"},
    "v3.3": {"pooled": "emca_v21", "spec": "emca_v22",
             "strat": "emca_v25c", "prober": "prober"},
    "v4":   {"pooled": "v4_believer", "spec": "v4_spec",
             "strat": "v4_rejector", "assoc": "v4_assoc"},
    "v5":   {"pooled": "v5_believer", "spec": "v5_spec",
             "strat": "v5_rejector", "assoc": "v5_assoc",
             "assoc02": "v5_assoc02"},
    "v6":   {"pooled": "v6_believer", "strat": "v6_rejector",
             "assoc": "v6_assoc", "assoc02": "v6_assoc02",
             "prober": "v6_prober", "oracle": "v6_oracle"},
}


def load(world):
    d = WORLDS[world][0]
    rows = defaultdict(dict)
    for path in sorted(glob.glob(os.path.join(HERE, d, "*.json"))):
        with open(path) as f:
            j = json.load(f)
        rows[j["condition"]][j["seed"]] = j
    return rows


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def boot_ci_paired(diffs, n=BOOT_N, seed=BOOT_SEED):
    """Paired bootstrap over seeds: resample seed indices, mean diff."""
    import random
    rng = random.Random(seed)
    m = len(diffs)
    if m == 0:
        return (float("nan"), float("nan"))
    means = []
    for _ in range(n):
        s = [diffs[rng.randrange(m)] for _ in range(m)]
        means.append(mean(s))
    means.sort()
    lo = means[int(0.025 * n)]
    hi = means[int(0.975 * n) - 1]
    return (lo, hi)


def sign_test(diffs):
    """Exact two-sided sign test, zeros excluded."""
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    if n == 0:
        return pos, neg, 1.0
    k = max(pos, neg)
    p = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return pos, neg, min(1.0, 2 * p)


def paired_contrast(rows, arm_a, arm_b):
    """D = reward(a) - reward(b), paired by seed; only seeds both have."""
    common = sorted(set(rows[arm_a]) & set(rows[arm_b]))
    diffs = [rows[arm_a][s]["total_reward"] - rows[arm_b][s]["total_reward"]
             for s in common]
    if not diffs:
        return None
    lo, hi = boot_ci_paired(diffs)
    pos, neg, p = sign_test(diffs)
    return {"n": len(diffs), "mean": mean(diffs), "ci": (lo, hi),
            "sign": (pos, neg), "p": p}


def fmt_c(c):
    return f"[{c[0]:+.0f},{c[1]:+.0f}]"


def main():
    out = []
    say = out.append

    say("=" * 72)
    say("THE EPISTEMIC LEDGER -- both axes, recomputed from raw JSONs")
    say("(fresh process, disk-only; directive msg_00116, turn 116)")
    say("=" * 72)

    # ---------- AXIS B: the epistemic table ----------
    say("")
    say("AXIS B -- EPISTEMIC: truth vs decoy, independent of reward")
    say("-" * 72)
    for world in WORLDS:
        _, decoy_key, true_edges, grey_edge = WORLDS[world]
        rows = load(world)
        say("")
        say(f"### {world}")
        for role, cond in IDENTIFIER_ARMS[world].items():
            runs = rows.get(cond, {})
            if not runs:
                continue
            n = len(runs)
            decoy_n = sum(1 for r in runs.values()
                          if r.get(decoy_key) is True)
            true_frac = mean([
                sum(1 for e in true_edges
                    if r.get("true_in_causal", {}).get(e)) /
                len(true_edges) for r in runs.values()])
            line = (f"  {role:<8} ({cond:<13}) n={n:<3} "
                    f"decoy-in-causal {decoy_n}/{n}   "
                    f"true-edges {true_frac:.0%}")
            if grey_edge:
                if role == "prober":
                    vs = [r.get("probe_verdicts", {})
                          .get(grey_edge, {}).get("verdict")
                          for r in runs.values()]
                    ca = sum(1 for v in vs if v == "CAUSAL")
                    rj = sum(1 for v in vs if v == "REJECT")
                    un = sum(1 for v in vs if v == "UNRESOLVED")
                    fp = sum(1 for r in runs.values()
                             if r.get(decoy_key) is True)
                    line += (f"   probe[{grey_edge}]: "
                             f"C:{ca} R:{rj} U:{un} decoyFP:{fp}")
                elif world in ("v5", "v6"):
                    held = sum(1 for r in runs.values()
                               if r.get("spring_in_causal"))
                    line += f"   spring-in-causal {held}/{n}"
            if world in ("v5", "v6"):
                lot = mean([r.get("lotus_eaten", 0) for r in runs.values()])
                line += f"   lotus {lot:.1f}"
            say(line)

    # ---------- AXIS A: the economic contrasts, recomputed ----------
    say("")
    say("")
    say("AXIS A -- ECONOMIC: the same worlds, reward contrasts")
    say("-" * 72)
    econ = [
        ("v3.3 n=15", "v3.3", "emca_v25c", "emca_v21",
         "strat - pooled (the old primary)"),
        ("v3.3 n=15", "v3.3", "emca_v25c", "emca_nocausal",
         "strat - nocausal (the goal-tax contrast)"),
        ("v4", "v4", "v4_rejector", "v4_believer",
         "honest - fooled (the price of the false edge)"),
        ("v5", "v5", "v5_rejector", "v5_assoc02",
         "selectivity contrast (V2)"),
        ("v6", "v6", "v6_prober", "v6_rejector",
         "discovery NET (G1)"),
        ("v6", "v6", "v6_oracle", "v6_rejector",
         "truth GROSS (G2)"),
        ("v6", "v6", "v6_oracle", "v6_prober",
         "the cost of finding out (G3)"),
    ]
    for label, world, a, b, desc in econ:
        rows = load(world)
        c = paired_contrast(rows, a, b)
        if c is None:
            say(f"{label:<10} {desc}: NO DATA")
            continue
        say(f"{label:<10} {desc}: mean {c['mean']:+.0f} "
            f"CI {fmt_c(c['ci'])} sign {c['sign'][0]}+/{c['sign'][1]}- "
            f"p={c['p']:.3f} (n={c['n']})")

    # ---------- the cross-check against the frozen reports ----------
    say("")
    say("")
    say("CROSS-CHECK vs the frozen analyses (must match)")
    say("-" * 72)
    checks = [
        ("v6 G1 mean +455 CI [-1283,+2204] p=0.754", "v6",
         "v6_prober", "v6_rejector"),
        ("v6 G2 mean +3755 CI [+2338,+5363] p=0.004", "v6",
         "v6_oracle", "v6_rejector"),
        ("v5 V2 mean -1008 CI [-2671,+737] p=1.000", "v5",
         "v5_rejector", "v5_assoc02"),
        ("v3.3 primary mean +178 CI [-1056,+1346] p=0.77", "v3.3",
         "emca_v25c", "emca_v21"),
    ]
    for label, world, a, b in checks:
        rows = load(world)
        c = paired_contrast(rows, a, b)
        say(f"  {label:<46} -> recomputed mean {c['mean']:+.0f} "
            f"CI {fmt_c(c['ci'])} p={c['p']:.3f}")

    # ---------- the founding charter E1, recomputed honestly ----------
    say("")
    say("")
    say("THE FOUNDING CHARTER (HYPOTHESES.md, E1) -- recomputed")
    say("-" * 72)
    say("E1: 'доля рёбер в истинном графе >= 0.5 И доля ложных рёбер")
    say("    <= 0.2. FAIL -> причинный модуль не работает.'")
    say("Edge classification (4-way, from the env source, not vibes):")
    say("  designed-true  -- the world's designed causal edges;")
    say("  mechanically-true -- real action->event mechanics the env")
    say("    emits (tree_bare: the tree IS bare; scorched: the pocket")
    say("    DOES scorch; energy_rose: eating DOES raise energy);")
    say("  decoy -- the designed false edge (grasp->bell_rang in v3.x,")
    say("    grasp->torch_lit in v4-v6; oracle P(effect|do(a)) equal);")
    say("  spurious -- everything else (mostly linger-correlates of")
    say("    world events: X->bell_rang, X->torch_lit for X!=grasp).")

    # the classification table per world
    # TRUE graph = designed edges + GRAY edges (true but weak: the
    #   altar wait->patch_berry RR~1.87 inherited from V33 into all
    #   later worlds; the spring wait->spring_flow in v5/v6);
    # MECHANICALLY-TRUE = real action->event mechanics (not knowledge
    #   anyone designed, but not false either): eating raises energy,
    #   eating clears the patch flag (making the next sprout possible:
    #   eat->patch_berry is thereby causally entailed), waiting at the
    #   altar pays an offering, grasping a capped tree bares it, moves
    #   into the scorch pocket scorch (position-mediated causation);
    # DECOY = the designed false edge (world events: bell_rang,
    #   torch_lit -- oracle P(effect|do(a)) equal for all actions);
    # SPURIOUS = world-false edges: any action->bell_rang/torch_lit
    #   (linger correlates), moves->door_gone (the door is NOT gone;
    #   the agent moved away -- a view artifact filed as an edge).
    CLS = {
        "v3.1": (["press->lever", "eat->ate", "grasp->tree_gather"],
                 []),
        "v3.2": (["press->lever", "eat->ate", "grasp->tree_gather",
                  "eat->patch_ate"],
                 ["wait->patch_berry"]),
        "v3.3": (["press->lever", "eat->ate", "grasp->tree_gather",
                  "eat->patch_ate"],
                 ["wait->patch_berry"]),
        "v4": (["press->lever", "eat->ate", "grasp->tree_gather",
                "eat->treasury_ate"],
               ["wait->patch_berry"]),
        "v5": (["press->lever", "eat->ate", "grasp->tree_gather",
                "eat->treasury_ate"],
               ["wait->patch_berry", "wait->spring_flow"]),
        "v6": (["press->lever", "eat->ate", "grasp->tree_gather",
                "eat->treasury_ate"],
               ["wait->patch_berry", "wait->spring_flow"]),
    }
    # passively-identifiable subset (RR>=2: within the strat gate's
    # design scope): the designed edges; the gray ones are NOT
    # passively identifiable by construction.
    MECH = {"grasp->tree_bare", "up->scorched", "down->scorched",
            "left->scorched", "right->scorched", "wait->scorched",
            "grasp->energy_rose", "eat->energy_rose",
            "press->energy_rose", "grasp->grasp", "eat->tree_ate",
            "eat->patch_ate", "eat->patch_berry", "wait->offering"}

    def classify(edges, world):
        designed, gray = CLS[world]
        true_graph = set(designed) | set(gray)
        decoy_set = {"v3.1": {"grasp->bell_rang"},
                     "v3.2": {"grasp->bell_rang"},
                     "v3.3": {"grasp->bell_rang"},
                     "v4": {"grasp->torch_lit"},
                     "v5": {"grasp->torch_lit"},
                     "v6": {"grasp->torch_lit"}}[world]
        res = {"true": 0, "mech": 0, "decoy": 0, "spur": 0,
               "spur_list": []}
        for e in edges:
            if e in true_graph:
                res["true"] += 1
            elif e in MECH:
                res["mech"] += 1
            elif e in decoy_set:
                res["decoy"] += 1
            else:
                res["spur"] += 1
                res["spur_list"].append(e)
        return res

    say("")
    say("per-arm E1 clauses. sensitivity = designed+gray true edges")
    say("held / |true graph|; 'passive-sens' = over the RR>=2 subset")
    say("(the strat gate's design scope); false = (decoy+spurious)")
    say("/all edges; mechanically-true edges counted in neither.")
    for world in WORLDS:
        rows = load(world)
        designed, gray = CLS[world]
        true_graph = designed + gray
        say("")
        say(f"### {world}  (true graph {len(true_graph)}: "
            f"{len(designed)} designed + {len(gray)} gray)")
        for role, cond in IDENTIFIER_ARMS[world].items():
            runs = rows.get(cond, {})
            if not runs:
                continue
            n = len(runs)
            true_hold = 0
            true_possible = 0
            passive_hold = 0
            passive_possible = 0
            decoy_n = 0
            spurious = 0
            tot = 0
            spur_examples = set()
            for r in runs.values():
                edges = set(f"{a}->{e}" for a, e, _ in
                            r.get("causal_edges", []))
                c = classify(edges, world)
                tot += len(edges)
                decoy_n += 0  # decoy counted below per design
                for e in true_graph:
                    true_possible += 1
                    true_hold += 1 if e in edges else 0
                for e in designed:
                    passive_possible += 1
                    passive_hold += 1 if e in edges else 0
                # decoy: the designed decoy edges of this world
                decoy_edges = {"v3.1": ["grasp->bell_rang"],
                               "v3.2": ["grasp->bell_rang"],
                               "v3.3": ["grasp->bell_rang"],
                               "v4": ["grasp->torch_lit"],
                               "v5": ["grasp->torch_lit"],
                               "v6": ["grasp->torch_lit"]}[world]
                decoy_n += sum(1 for e in decoy_edges if e in edges)
                spurious += c["spur"]
                spur_examples.update(c["spur_list"][:3])
            sens = true_hold / true_possible if true_possible else float("nan")
            psens = passive_hold / passive_possible if passive_possible else float("nan")
            false_rate = (decoy_n + spurious) / tot if tot else float("nan")
            v1 = "PASS" if sens >= 0.5 else "FAIL"
            v2 = "PASS" if false_rate <= 0.2 else "FAIL"
            say(f"  {role:<8} ({cond:<13}) sens {sens:>5.0%} [{v1}] "
                f"passive-sens {psens:>5.0%}   false {false_rate:>5.1%} "
                f"[{v2}]   (decoy {decoy_n}, spur {spurious}, "
                f"edges {tot}; ex: {sorted(spur_examples)[:3]})")

    # ---------- prober calibration vs the oracle ----------
    say("")
    say("")
    say("PROBER CALIBRATION -- measured effect size vs ground truth")
    say("-" * 72)
    calib = [
        ("v6 spring (oracle RR=1.53, P .304/.199)", "results/matrix_v6",
         "v6_prober", "wait->spring_flow", 1.53),
        ("v3.3 altar (design RR~1.87, P .28/.15)", "results/matrix_v33",
         "prober", "wait->patch_berry", 1.87),
        ("v3.2 altar (design RR~1.87)", "results/matrix_v32",
         "prober", "wait->patch_berry", 1.87),
    ]
    for label, d, cond, edge, truth in calib:
        vs = []
        for path in sorted(glob.glob(os.path.join(HERE, d,
                                                  f"{cond}_*.json"))):
            with open(path) as f:
                j = json.load(f)
            v = j.get("probe_verdicts", {}).get(edge)
            if v:
                vs.append(v)
        n = len(vs)
        ca = [v for v in vs if v["verdict"] == "CAUSAL"]
        rj = [v for v in vs if v["verdict"] == "REJECT"]
        un = [v for v in vs if v["verdict"] == "UNRESOLVED"]
        mean_rr = mean([v["rr"] for v in ca]) if ca else float("nan")
        fp = sum(1 for v in vs if v["verdict"] == "CAUSAL"
                 and v["rr"] < 1.0)
        say(f"  {label}: verdicts {n} -> C:{len(ca)} R:{len(rj)} "
            f"U:{len(un)}; mean accepted RR {mean_rr:.3f} vs truth "
            f"{truth} ({(mean_rr/truth-1)*100:+.0f}% selection bias); "
            f"false-positive CAUSAL verdicts: {fp}")
        for v in rj:
            say(f"    REJECT case: p={v['p']:.3f} rr={v['rr']} "
                f"(rate_wait {v['target_yes']}/{v['target_yes']+v['target_no']}"
                f" vs ctrl {v['ctrl_yes']}/{v['ctrl_yes']+v['ctrl_no']})")

    # ---------- possession vs identification (assoc02) ----------
    say("")
    say("")
    say("POSSESSION vs IDENTIFICATION -- the layers, kept apart (v5/v6)")
    say("-" * 72)
    say("identification = the edge in the arm's CAUSAL layer (the")
    say("contrast-based route); possession = the edge above the 0.02")
    say("assoc threshold (no contrast, no discrimination).")
    for world in ("v5", "v6"):
        rows = load(world)
        for role, cond in IDENTIFIER_ARMS[world].items():
            if role not in ("assoc02", "strat"):
                continue
            runs = rows.get(cond, {})
            if not runs:
                continue
            n = len(runs)
            ident = sum(1 for r in runs.values()
                       if r.get("spring_in_causal"))
            poss = sum(1 for r in runs.values()
                       if r.get("spring_in_assoc002"))
            dec_a = sum(1 for r in runs.values()
                        if r.get("decoy_torch_in_assoc"))
            lot = mean([r.get("lotus_eaten", 0) for r in runs.values()])
            say(f"  {world} {role:<8} ({cond}): IDENTIFIED "
                f"(causal layer) {ident}/{n}, POSSESSED (0.02 assoc) "
                f"{poss}/{n}, decoy in its own layer {dec_a}/{n}, "
                f"lotus {lot:.1f}")

    # ---------- the goal-swap evidence ----------
    say("")
    say("")
    say("THE GOAL-SWAP EVIDENCE -- what the campaign's own documents say")
    say("-" * 72)
    say("founding charter (research/HYPOTHESES.md, pre-registered")
    say("2026-09-09, BEFORE any matrix): E1 = epistemic clauses ONLY")
    say("(>=0.5 true, <=0.2 false); E2-E6 = capability clauses; reward")
    say("appears ONLY as a baseline comparison, never as the causal")
    say("module's success bar.")
    say("turn-104+ headline (RESULTS_V33_SEEDS.md): 'the causal model")
    say("does not pay ... the answer is no' -- reward had become the")
    say("verdict axis. The charter was never amended. The owner's")
    say("correction (msg_00116, op_f4dccecb1750) RESTORES the")
    say("pre-registered charter; it does not invent a new one.")

    text = "\n".join(out) + "\n"
    with open(OUT, "w") as f:
        f.write(text)
    print(text)
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
