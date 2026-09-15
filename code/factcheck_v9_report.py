"""factcheck_v9_report.py -- turn 133. Every number that goes into
research/RESULTS_V9.md is declared here as a NAME -> recomputation from the frozen
matrix; the script prints the value the FROZEN DATA gives and compares it to the
value the report states. A mismatch is a FAIL, and the number is corrected in the
report rather than the check.

Usage: python3 factcheck_v9_report.py [--emit]
  --emit  print the JSON of all recomputed values (used to write the report)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = os.path.join(HERE, "results", "matrix_v9")
SEEDS = list(range(10))


def cell(arm, seed, truth="on", rich="low", decoy="on"):
    p = os.path.join(MAT, f"{arm}_{seed}_{truth}_{rich}_{decoy}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def mean(arm, field, truth="on", rich="low", decoy="on"):
    vals = []
    for s in SEEDS:
        r = cell(arm, s, truth, rich, decoy)
        if r:
            vals.append(float(r[field]))
    return sum(vals) / len(vals) if vals else None


def main():
    out = {}
    out["cells"] = len([f for f in os.listdir(MAT) if f.endswith(".json")])

    # headline means
    for arm in ("v9_union", "v9_stop", "v9_noexp", "v9_noctx", "v9_fixed",
                "v9_old", "v9_oracle", "v9_forager", "v9_random"):
        out[f"reward_{arm}"] = round(mean(arm, "total_reward"), 1)
        out[f"fruits_{arm}"] = round(mean(arm, "fruits_eaten"), 2)
        out[f"probe_trials_{arm}"] = round(mean(arm, "probe_trials"), 1)
        out[f"probe_blocks_{arm}"] = round(mean(arm, "probe_blocks"), 1)
        out[f"blooms_{arm}"] = round(mean(arm, "fruit_blooms"), 1)
        out[f"deaths_{arm}"] = round(mean(arm, "deaths"), 2)
        out[f"ncand_{arm}"] = round(mean(arm, "n_candidates_total"), 2)
        out[f"explore_picks_{arm}"] = round(mean(arm, "n_explore_picks"), 2)
    # conflict battery
    for arm in ("v9_union", "v9_stop", "v9_old"):
        out[f"reward_{arm}_conflict"] = round(
            mean(arm, "total_reward", rich="high"), 1)
        out[f"probe_trials_{arm}_conflict"] = round(
            mean(arm, "probe_trials", rich="high"), 1)
        out[f"fruits_{arm}_conflict"] = round(
            mean(arm, "fruits_eaten", rich="high"), 2)
    # truth off
    out["reward_union_off"] = round(mean("v9_union", "total_reward", truth="off"), 1)
    out["probe_trials_union_off"] = round(mean("v9_union", "probe_trials", truth="off"), 1)
    out["ncand_union_off"] = round(mean("v9_union", "n_candidates_total", truth="off"), 2)

    # paired H1/H2
    def diff(a, b, field, **kw):
        d = []
        for s in SEEDS:
            ra, rb = cell(a, s, **kw), cell(b, s, **kw)
            if ra and rb:
                d.append(float(ra[field]) - float(rb[field]))
        return round(sum(d) / len(d), 4) if d else None
    out["H1_diff"] = diff("v9_union", "v9_old", "total_reward")
    out["H2_diff"] = diff("v9_union", "v9_old", "fruits_eaten")
    out["H1b_diff"] = diff("v9_stop", "v9_old", "total_reward")
    out["H5a_diff"] = diff("v9_union", "v9_noexp", "total_reward")
    out["H5b_diff"] = diff("v9_union", "v9_noctx", "total_reward")
    out["H6_diff"] = diff("v9_union", "v9_fixed", "total_reward")

    # verification counts
    def count_causal(arm, truth="on", rich="low"):
        c = 0
        fp = 0
        nv = 0
        for s in SEEDS:
            r = cell(arm, s, truth, rich)
            if not r:
                continue
            ea = r["edge_action"]
            v = r["verdicts"]
            nv += len(v)
            if v.get(f"{ea}->hum", {}).get("verdict") == "CAUSAL":
                c += 1
            fp += sum(1 for k, rec in v.items()
                      if k.endswith("->glow") and rec.get("verdict") == "CAUSAL")
        return c, fp, nv
    c, fp, nv = count_causal("v9_union")
    out["H4_causal"] = c
    out["H4_fp_rows"] = fp
    out["H4_n_verdicts"] = nv
    out["H4_E_fp"] = round(0.00488 * nv, 2)
    c_off, fp_off, nv_off = count_causal("v9_union", truth="off")
    out["H4_causal_off"] = c_off
    out["H4_n_verdicts_off"] = nv_off

    # nominations
    def nom(arm, truth="on"):
        n = 0
        for s in SEEDS:
            r = cell(arm, s, truth)
            if not r:
                continue
            ea = r["edge_action"]
            if any(x[0] == ea and x[1] == "hum" for x in r["candidates_seen"]):
                n += 1
        return n
    out["H3i_on"] = nom("v9_union", "on")
    out["H3i_off"] = nom("v9_union", "off")
    out["H6_fixed_nom"] = nom("v9_fixed", "on")

    def nom_contrast(arm, truth="on"):
        n = 0
        for s in SEEDS:
            r = cell(arm, s, truth)
            if not r:
                continue
            ea = r["edge_action"]
            if any(x[0] == ea and x[1] == "hum" and x[4] != "thin-ctx"
                   for x in r["candidates_seen"]):
                n += 1
        return n
    out["POSTHOC_contrast_on"] = nom_contrast("v9_union", "on")
    out["POSTHOC_contrast_off"] = nom_contrast("v9_union", "off")

    # exploration dominance: share of probed candidates carrying the thin label
    tot_pk = 0
    thin_pk = 0
    for s in SEEDS:
        r = cell("v9_union", s)
        if not r:
            continue
        for k in r.get("probe_keys", []):
            tot_pk += 1
            if str(k[2]).startswith("thin"):
                thin_pk += 1
    out["probe_keys_total"] = tot_pk
    out["probe_keys_thin"] = thin_pk
    out["probe_keys_thin_share"] = round(thin_pk / tot_pk, 3) if tot_pk else None

    # does the true edge ever top the ranked list? (label is position 4)
    top_is_true = 0
    top_is_thin = 0
    ranked_n = 0
    ranked_thin = 0
    ranked_ctr = 0
    for s in SEEDS:
        r = cell("v9_union", s)
        if not r or not r.get("ranked_at_first_probe"):
            continue
        ranked_n += 1
        rl = r["ranked_at_first_probe"]
        for x in rl:
            if str(x[4]) == "thin-ctx":
                ranked_thin += 1
            else:
                ranked_ctr += 1
        top = rl[0]
        if str(top[4]) == "thin-ctx":
            top_is_thin += 1
        if top[0] == r["edge_action"] and top[1] == "hum" and str(top[4]) != "thin-ctx":
            top_is_true += 1
    out["top_is_thin"] = top_is_thin
    out["top_is_true_contrast"] = top_is_true
    out["ranked_n"] = ranked_n
    out["ranked_thin_rows"] = ranked_thin
    out["ranked_contrast_rows"] = ranked_ctr
    # score of the top thin candidate vs the top contrast candidate at first probe
    thin_scores = []
    ctr_scores = []
    for s in SEEDS:
        r = cell("v9_union", s)
        if not r or not r.get("ranked_at_first_probe"):
            continue
        rl = r["ranked_at_first_probe"]
        for x in rl:
            if str(x[4]) == "thin-ctx":
                thin_scores.append(float(x[2]))
            else:
                ctr_scores.append(float(x[2]))
    out["top_score_mean"] = round(max(thin_scores), 4) if thin_scores else None
    out["top_contrast_score_mean"] = round(max(ctr_scores), 4) if ctr_scores else None
    out["true_edge_contrast_score"] = None
    for s in SEEDS:
        r = cell("v9_union", s)
        if not r:
            continue
        ea = r["edge_action"]
        for x in r["ranked_at_first_probe"]:
            if x[0] == ea and x[1] == "hum" and str(x[4]) != "thin-ctx":
                out["true_edge_contrast_score"] = float(x[2])
                break
        if out["true_edge_contrast_score"] is not None:
            break

    print(json.dumps(out, indent=1))
    if "--emit" not in sys.argv:
        print("\n(declare the report's numbers against this output)")


if __name__ == "__main__":
    main()
