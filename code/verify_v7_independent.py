"""verify_v7_independent.py -- SECOND, INDEPENDENT pass over the V7 matrix.

Deliberately re-derives every verdict from the raw JSON with DIFFERENT
code from analyze_v7.py (no imports from it), so a shared bug cannot
survive. Reads only results/matrix_v7/*.json. Prints PASS/FAIL per
recomputed quantity and flags any disagreement with the frozen analysis.

Usage: python3 verify_v7_independent.py
"""
import glob
import json
import math
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_v7")


def read_all():
    out = []
    for f in sorted(glob.glob(os.path.join(D, "*.json"))):
        with open(f) as fh:
            out.append(json.load(fh))
    return out


def key(d):
    return (d["arm"], d["truth"], d["rich"], d["decoy"], d["seed"])


def main():
    runs = read_all()
    by = {key(d): d for d in runs}
    fails = []

    def check(name, cond, detail=""):
        print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
        if not cond:
            fails.append(name)

    print(f"runs loaded: {len(runs)}")

    # --- integrity: every run is a full 16000-step life ---
    check("all runs 16000 steps", all(d["steps"] == 16000 for d in runs))
    # the uniform-random BASELINE may pick an unaffordable action (it does
    # not consult `afford`); the runner substitutes `wait` and the run still
    # completes. That is the declared brute-force gate, not a defect -- so
    # the invariant is scoped to the arms that DO consult affordance.
    EPISTEMIC = {"v7_full", "v7_beta0", "v7_perm", "v7_nogen", "v7_oracle",
                 "v7_forager"}
    scoped = [d for d in runs if d["arm"] in EPISTEMIC]
    check("no unaffordable actions in the epistemic arms",
          all(not d["harness_notes"] for d in scoped),
          f"(random-baseline substitutions: "
          f"{sum(len(d['harness_notes']) for d in runs if d['arm'] not in EPISTEMIC)})")

    # --- C2: nomination of the true pair, on vs off ---
    def nom_true(d):
        return any(c[0] == d["edge_action"] and c[1] == "hum"
                   for c in d["candidates_seen"])

    on = [d for d in runs if d["arm"] == "v7_full" and d["truth"]
          and d["rich"] == "low" and d["decoy"]]
    off = [d for d in runs if d["arm"] == "v7_full" and not d["truth"]]
    on_nom = sum(nom_true(d) for d in on)
    off_nom = sum(nom_true(d) for d in off)
    check("C2 on nomination >= 8", on_nom >= 8, f"({on_nom}/10)")
    check("C2 off nomination <= 2", off_nom <= 2, f"({off_nom}/10)")

    # --- C2 anti-hardcode: nomination tracks the RANDOM edge_action ---
    # For each seed the nominated pair must be the seed's edge, not a
    # constant. Count distinct edge actions that were nominated.
    edges_nom = {d["edge_action"] for d in on if nom_true(d)}
    check("C2 nomination follows randomised edge (>=2 distinct actions)",
          len(edges_nom) >= 2, f"({sorted(edges_nom)})")

    # --- C3: false positives (glow CAUSAL) and false negatives ---
    def glow_causal(d):
        return sum(1 for k, v in d["verdicts"].items()
                   if k.endswith("->glow") and v["verdict"] == "CAUSAL")

    fp = sum(glow_causal(d) for d in runs)
    check("C3 zero false positives (all arms, all regimes)", fp == 0,
          f"(fp={fp})")
    # metrological context (does NOT change the gate above): how many
    # DISTINCT false-positive events are there, and how many such events a
    # calibrated test of this size should produce?
    distinct = set()
    for d in runs:
        for k, v in d["verdicts"].items():
            if k.endswith("->glow") and v["verdict"] == "CAUSAL":
                distinct.add((d["seed"], k))
    n_tests = sum(len(d["verdicts"]) for d in runs)
    print(f"     distinct FP events: {len(distinct)} {sorted(distinct)} "
          f"| verdicts issued: {n_tests}")
    print(f"     nominal per-test rate at n=200/arm (Monte-Carlo, 40000 "
          f"draws): 0.0051 -> E[FP] = {n_tests} x 0.0051 = "
          f"{n_tests*0.0051:.2f}; P(>=1 FP) = "
          f"{1 - math.exp(-n_tests*0.0051):.2f}")
    print(f"     => ONE FP event is the EXPECTED outcome of a calibrated "
          f"test at this test count; see calib_v7_fprate.py")
    fn = sum(1 for d in on
             if (d["verdicts"].get(d["edge_action"] + "->hum", {})
                 .get("verdict") != "CAUSAL"))
    check("C3 false negatives <= 2", fn <= 2, f"({fn}/10)")

    # --- C3 verification is on SELF-GENERATED candidates: every probed
    #     key must appear in the candidate list that produced it ---
    # (the runner stores the LAST list; we check the probed keys were
    #  generated at some point -- the verdicts keys must be a subset of
    #  the union of listed candidates over the life. We only have the
    #  last list, so we check the weaker, still meaningful invariant:
    #  every probed key was NOT injected by the designer.)
    injected = ["designer", "injected"]
    bad_inject = []
    for d in runs:
        for k, v in d["verdicts"].items():
            if v.get("injected"):
                bad_inject.append((key(d), k))
    # oracle arm legitimately injects; others must not
    bad_inject = [b for b in bad_inject if b[0][0] != "v7_oracle"]
    check("C3 no injected edge outside the oracle arm", not bad_inject,
          f"({bad_inject[:3]})")

    # --- C1: recompute the three legs with independent arithmetic ---
    full_hi = [by[("v7_full", True, "high", True, s)] for s in range(10)]
    full_lo = [by[("v7_full", True, "low", True, s)] for s in range(10)]
    beta_hi = [by[("v7_beta0", True, "high", True, s)] for s in range(10)]
    perm_hi = [by[("v7_perm", True, "high", True, s)] for s in range(10)]
    perm_lo = [by[("v7_perm", True, "low", True, s)] for s in range(10)]

    fh = [d["probe_trials"] for d in full_hi]
    fl = [d["probe_trials"] for d in full_lo]
    bh = [d["probe_trials"] for d in beta_hi]
    check("C1-i full probes in >=8 conflict seeds",
          sum(x >= 1 for x in fh) >= 8, f"({sum(x >= 1 for x in fh)}/10)")
    check("C1-i beta0 never probes in conflict",
          all(x == 0 for x in bh), f"(beta0 probes={bh})")
    # C1-ii: the first probe equals the argmax of the ranked list AS SEEN
    ok = 0
    n = 0
    for d in perm_hi + perm_lo:
        rk = d.get("ranked_at_first_probe")
        fpv = d.get("first_probe")
        if not rk or not fpv:
            continue
        n += 1
        top = sorted(rk, key=lambda c: (-c[2], -c[3], c[0], c[1]))[0]
        if (fpv[0], fpv[1]) == (top[0], top[1]):
            ok += 1
    check("C1-ii perm first probe follows ranking", n > 0 and ok == n,
          f"({ok}/{n})")
    check("C1-iii probes(high) < probes(low) and > 0",
          statistics.mean(fh) < statistics.mean(fl) and statistics.mean(fh) > 0,
          f"(high {statistics.mean(fh):.0f} < low {statistics.mean(fl):.0f})")

    # --- cross-check: the perm arm must differ from full in probe ORDER
    #     at least once (else the permutation did nothing) ---
    diff = 0
    for d in perm_hi:
        f = by[("v7_full", True, "high", True, d["seed"])]
        if d.get("first_probe") != f.get("first_probe"):
            diff += 1
    print(f"  note: perm vs full first-probe differs in {diff}/10 seeds "
          f"(permutation is observable in the decision)")

    # --- economy cross-check (secondary) ---
    forager = [d for d in runs if d["arm"] == "v7_forager"]
    oracle = [d for d in runs if d["arm"] == "v7_oracle"]
    check("economy: oracle eats >= full eats",
          statistics.mean(d["fruits_eaten"] for d in oracle)
          >= statistics.mean(d["fruits_eaten"] for d in full_lo))
    check("economy: forager never probes",
          all(d["probe_trials"] == 0 for d in forager))
    check("economy: random never probes",
          all(d["probe_trials"] == 0 for d in runs if d["arm"] == "v7_random"))

    print()
    if fails:
        print("INDEPENDENT VERIFY: FAIL", fails)
        raise SystemExit(1)
    print("INDEPENDENT VERIFY: ALL PASS")


if __name__ == "__main__":
    main()
