"""analyze_v9.py -- turn 133. The V9 verdicts, computed from the frozen matrix.

Reads results/matrix_v9/*.json only. Emits a JSON summary (results/analysis_v9.json)
and a human-readable text (results/analysis_v9.txt). Every verdict threshold is
the one declared in research/PREREG_V9.md §3; none is chosen after the fact.

Paired contrasts are per SEED (the same seed is a world and both arms see it),
bootstrap 20000 resamples over seeds, plus a sign test on the number of seeds
where the difference is positive.
"""
import glob
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = os.path.join(HERE, "results", "matrix_v9")
SEEDS = list(range(10))
BOOT = 20000
PROBE_VOCAB = ("grasp", "press", "wait")   # the protocol's declared vocabulary


def load(arm, seed, truth="on", rich="low", decoy="on"):
    p = os.path.join(MAT, f"{arm}_{seed}_{truth}_{rich}_{decoy}.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def paired(arm_a, arm_b, field, truth="on", rich="low", decoy="on"):
    a, b = [], []
    for s in SEEDS:
        ra = load(arm_a, s, truth, rich, decoy)
        rb = load(arm_b, s, truth, rich, decoy)
        if ra is None or rb is None:
            continue
        a.append(float(ra[field]))
        b.append(float(rb[field]))
    d = [x - y for x, y in zip(a, b)]
    if not d:
        return None
    rng = random.Random(20260912)
    n = len(d)
    boots = []
    for _ in range(BOOT):
        boots.append(sum(d[rng.randrange(n)] for _ in range(n)) / n)
    boots.sort()
    lo = boots[int(0.025 * BOOT)]
    hi = boots[int(0.975 * BOOT) - 1]
    pos = sum(1 for x in d if x > 0)
    neg = sum(1 for x in d if x < 0)
    return {"mean_a": sum(a) / n, "mean_b": sum(b) / n,
            "mean_diff": sum(d) / n, "ci": [lo, hi], "n": n,
            "pos": pos, "neg": neg, "diffs": d}


def verdict_advantage(p):
    """H1/H2 gate (prereg V9 §3): the difference must be POSITIVE -- CI excludes
    0 with a positive lower bound, or a sign test with >= 8/10 SEEDS in favour.
    DEFECT FIXED (found while reading the first output of this very script): the
    first version tested only "the CI excludes zero", which labels a significant
    LOSS as ADVANTAGE. The gate is directional in the prereg; the code now is too.
    The buggy version is preserved in git history / this turn's status note, and
    the fix is reported rather than silently applied."""
    if p is None:
        return "NO DATA"
    if p["ci"][0] > 0:
        return "ADVANTAGE"
    if p["pos"] >= 8:
        return "ADVANTAGE (sign)"
    if p["ci"][1] < 0:
        return "SIGNIFICANT LOSS"
    return "NO ADVANTAGE"


def main():
    out = {"cells": 0, "verdicts": {}, "contrasts": {}, "diagnostics": {}}
    files = sorted(glob.glob(os.path.join(MAT, "*.json")))
    out["cells"] = len(files)

    # ---------------- H1 / H2: the owner's question -------------------
    for field, tag in (("total_reward", "H1_reward"), ("fruits_eaten", "H2_fruits")):
        p = paired("v9_union", "v9_old", field)
        out["contrasts"][tag] = p
        out["verdicts"][tag] = verdict_advantage(p)
    # the stop variant, against the same frozen comparator
    for field, tag in (("total_reward", "H1b_reward_stop"),
                       ("fruits_eaten", "H2b_fruits_stop")):
        p = paired("v9_stop", "v9_old", field)
        out["contrasts"][tag] = p
        out["verdicts"][tag] = verdict_advantage(p)

    # ---------------- H5: ablations -----------------------------------
    for field, tag in (("total_reward", "H5a_union_vs_noexp"),
                       ("total_reward", "H5b_union_vs_noctx")):
        other = "v9_noexp" if "noexp" in tag else "v9_noctx"
        p = paired("v9_union", other, field)
        out["contrasts"][tag] = p
        out["verdicts"][tag] = verdict_advantage(p)

    # ---------------- H3: generation & choice -------------------------
    nom_on = 0
    nom_off = 0
    first_follows = 0
    first_total = 0
    for s in SEEDS:
        r = load("v9_union", s, "on", "low", "on")
        if r:
            ea = r["edge_action"]
            if any(c[0] == ea and c[1] == "hum" for c in r["candidates_seen"]):
                nom_on += 1
            if r.get("first_probe") and r.get("ranked_at_first_probe"):
                top = r["ranked_at_first_probe"][0]
                first_total += 1
                if tuple(r["first_probe"]) == (top[0], top[1]):
                    first_follows += 1
        ro = load("v9_union", s, "off", "low", "on")
        if ro:
            ea = ro["edge_action"]
            if any(c[0] == ea and c[1] == "hum" for c in ro["candidates_seen"]):
                nom_off += 1
    out["verdicts"]["H3i_nominate_on"] = f"{nom_on}/10"
    out["verdicts"]["H3i_nominate_off"] = f"{nom_off}/10"
    out["verdicts"]["H3i_PASS"] = (nom_on >= 8 and nom_off <= 2)
    out["verdicts"]["H3ii_first_follows"] = f"{first_follows}/{first_total}"
    out["verdicts"]["H3ii_PASS"] = (first_total > 0 and first_follows >= 8)

    # ---- POST-HOC supplementary readings (NOT verdict flips) ----------------
    # Declared as post-hoc in the report: they were written AFTER the
    # preregistered H3 readings came back FAIL, and they do not change any
    # verdict above. They are reported because the preregistered form of H3i/H3ii
    # was inherited from v7, where the candidate list was NOT deliberately
    # permissive; the union's exploration source nominates every unresolved item,
    # so both tests answer "is the list permissive?" instead of "is the
    # nomination computed?". Reporting both keeps the distinction visible.
    first_follows_pb = 0
    first_total_pb = 0
    for s in SEEDS:
        r = load("v9_union", s, "on", "low", "on")
        if not r or not r.get("first_probe") or not r.get("ranked_at_first_probe"):
            continue
        pb = [c for c in r["ranked_at_first_probe"] if c[0] in PROBE_VOCAB]
        if not pb:
            continue
        first_total_pb += 1
        if tuple(r["first_probe"]) == (pb[0][0], pb[0][1]):
            first_follows_pb += 1
    out["verdicts"]["POSTHOC_H3ii_first_follows_probeable"] = \
        f"{first_follows_pb}/{first_total_pb}"
    nom_on_ctr = 0
    nom_off_ctr = 0
    for s in SEEDS:
        r = load("v9_union", s, "on", "low", "on")
        if r:
            ea = r["edge_action"]
            if any(c[0] == ea and c[1] == "hum" and c[2] != "thin-ctx"
                   for c in r["candidates_seen"]):
                nom_on_ctr += 1
        ro = load("v9_union", s, "off", "low", "on")
        if ro:
            ea = ro["edge_action"]
            if any(c[0] == ea and c[1] == "hum" and c[2] != "thin-ctx"
                   for c in ro["candidates_seen"]):
                nom_off_ctr += 1
    out["verdicts"]["POSTHOC_H3i_contrast_only_on"] = f"{nom_on_ctr}/10"
    out["verdicts"]["POSTHOC_H3i_contrast_only_off"] = f"{nom_off_ctr}/10"

    # ---------------- H4: verification --------------------------------
    caus_on = 0
    fp_glow = 0
    n_verdicts = 0
    for s in SEEDS:
        r = load("v9_union", s, "on", "low", "on")
        if not r:
            continue
        ea = r["edge_action"]
        v = r["verdicts"]
        n_verdicts += len(v)
        if v.get(f"{ea}->hum", {}).get("verdict") == "CAUSAL":
            caus_on += 1
        for k, rec in v.items():
            if k.endswith("->glow") and rec.get("verdict") == "CAUSAL":
                fp_glow += 1
    out["verdicts"]["H4_causal_true"] = f"{caus_on}/10"
    out["verdicts"]["H4_PASS"] = (caus_on >= 8)
    out["verdicts"]["H4_fp_glow_rows"] = fp_glow
    out["verdicts"]["H4_n_verdicts"] = n_verdicts
    # metrology from turn 124/125: nominal null rate 0.488% per test
    out["verdicts"]["H4_E_fp"] = round(0.00488 * n_verdicts, 3)

    # ---------------- H6: hidden-hardcode control ---------------------
    fixed_nom_on = 0
    fixed_nom_wait_seeds = 0
    for s in SEEDS:
        r = load("v9_fixed", s, "on", "low", "on")
        if not r:
            continue
        ea = r["edge_action"]
        if ea == "wait":
            fixed_nom_wait_seeds += 1
        if any(c[0] == ea and c[1] == "hum" for c in r["candidates_seen"]):
            fixed_nom_on += 1
    p = paired("v9_union", "v9_fixed", "total_reward")
    out["contrasts"]["H6_union_vs_fixed"] = p
    out["verdicts"]["H6_union_vs_fixed_verdict"] = verdict_advantage(p)
    out["verdicts"]["H6_fixed_nominates_true"] = f"{fixed_nom_on}/10"
    out["verdicts"]["H6_seeds_where_edge_is_wait"] = fixed_nom_wait_seeds
    out["verdicts"]["H6_PASS"] = bool(
        (p and (p["ci"][0] > 0 or p["pos"] >= 8)) or
        (fixed_nom_on == fixed_nom_wait_seeds))

    # ---------------- diagnostics (no verdict force) ------------------
    diag = {}
    for arm in ("v9_union", "v9_stop", "v9_noexp", "v9_noctx", "v9_fixed",
                "v9_old", "v9_oracle", "v9_forager", "v9_random"):
        rows = [load(arm, s, "on", "low", "on") for s in SEEDS]
        rows = [r for r in rows if r]
        if not rows:
            continue
        diag[arm] = {
            "reward": round(sum(r["total_reward"] for r in rows) / len(rows), 1),
            "fruits": round(sum(r["fruits_eaten"] for r in rows) / len(rows), 2),
            "blooms": round(sum(r["fruit_blooms"] for r in rows) / len(rows), 1),
            "probe_trials": round(sum(r["probe_trials"] for r in rows) / len(rows), 1),
            "probe_blocks": round(sum(r["probe_blocks"] for r in rows) / len(rows), 1),
            "deaths": round(sum(r["deaths"] for r in rows) / len(rows), 2),
            "n_candidates": round(sum(r["n_candidates_total"] for r in rows) / len(rows), 2),
            "explore_picks": round(sum(r.get("n_explore_picks", 0) for r in rows) / len(rows), 2),
            "skipped_not_probeable": round(sum(r.get("n_skipped_not_probeable", 0) for r in rows) / len(rows), 2),
            "first_causal_t": [r.get("first_causal_t") for r in rows],
        }
    out["diagnostics"] = diag

    # the conflict battery: does the union still probe when the alternative pays?
    for arm in ("v9_union", "v9_stop", "v9_old"):
        rows = [load(arm, s, "on", "high", "on") for s in SEEDS]
        rows = [r for r in rows if r]
        if rows:
            out["diagnostics"][arm + "_conflict"] = {
                "reward": round(sum(r["total_reward"] for r in rows) / len(rows), 1),
                "probe_trials": round(sum(r["probe_trials"] for r in rows) / len(rows), 1),
                "probe_blocks": round(sum(r["probe_blocks"] for r in rows) / len(rows), 1),
                "fruits": round(sum(r["fruits_eaten"] for r in rows) / len(rows), 2),
            }
    # truth=off: does the union nominate a false edge?
    off_rows = [load("v9_union", s, "off", "low", "on") for s in SEEDS]
    off_rows = [r for r in off_rows if r]
    if off_rows:
        out["diagnostics"]["v9_union_off"] = {
            "reward": round(sum(r["total_reward"] for r in off_rows) / len(off_rows), 1),
            "n_candidates": round(sum(r["n_candidates_total"] for r in off_rows) / len(off_rows), 2),
            "probe_trials": round(sum(r["probe_trials"] for r in off_rows) / len(off_rows), 1),
        }

    with open(os.path.join(HERE, "results", "analysis_v9.json"), "w") as f:
        json.dump(out, f, indent=1)

    # ---- human-readable ----
    lines = []
    lines.append("V9 analysis -- %d cells" % out["cells"])
    lines.append("")
    lines.append("=== VERDICTS (prereg V9 §3) ===")
    for k in ("H1_reward", "H2_fruits", "H1b_reward_stop", "H2b_fruits_stop",
              "H5a_union_vs_noexp", "H5b_union_vs_noctx"):
        p = out["contrasts"].get(k)
        if p:
            lines.append(f"{k:24s} {out['verdicts'][k]:22s} "
                         f"diff={p['mean_diff']:+.4f} CI=[{p['ci'][0]:+.4f},{p['ci'][1]:+.4f}] "
                         f"sign {p['pos']}+/{p['neg']}-")
    for k in ("H3i_nominate_on", "H3i_nominate_off", "H3i_PASS",
              "H3ii_first_follows", "H3ii_PASS",
              "POSTHOC_H3i_contrast_only_on", "POSTHOC_H3i_contrast_only_off",
              "POSTHOC_H3ii_first_follows_probeable",
              "H4_causal_true", "H4_PASS", "H4_fp_glow_rows", "H4_n_verdicts",
              "H4_E_fp", "H6_fixed_nominates_true",
              "H6_seeds_where_edge_is_wait", "H6_PASS",
              "H6_union_vs_fixed_verdict"):
        lines.append(f"{k:24s} {out['verdicts'][k]}")
    lines.append("")
    lines.append("=== DIAGNOSTICS (BASE, mean over 10 seeds) ===")
    for arm, d in out["diagnostics"].items():
        lines.append(f"{arm:22s} {json.dumps(d)}")
    txt = "\n".join(lines)
    with open(os.path.join(HERE, "results", "analysis_v9.txt"), "w") as f:
        f.write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()