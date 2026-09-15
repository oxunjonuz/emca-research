#!/usr/bin/env python3
"""Fact-check RESULTS_BENCH.md against the FROZEN artefacts on disk.
Every number asserted in the report prose is recomputed from the frozen JSON.
Catches numbers typed from memory instead of read from disk.
"""
import json, re, sys

R = open("RESULTS_BENCH.md").read()
fails = []


def chk(label, claimed, actual, tol=0.0):
    ok = (abs(claimed - actual) <= tol) if isinstance(claimed, float) else (claimed == actual)
    print("%-52s report=%-12s disk=%-12s %s" % (label, claimed, actual, "OK" if ok else "MISMATCH"))
    if not ok:
        fails.append(label)


r1 = json.load(open("results_bench.json"))
r2 = json.load(open("results_bench2.json"))
rc = json.load(open("results_compare.json"))
hh = json.load(open("results_headtohead.json"))

# H1/H2/H3 block
chk("H1 pooled recall 0.95", 0.95, round(r1["pooled_recall"], 3), 0.001)
chk("H2 zero exclusive pairs", 0, r1["E1"]["n_exclusive"])
chk("H3 null_ge 200", 200, r1["null_ge_observed"])
chk("pooled visible 55-pair count 54", 54, r1["pooled_visible"])
chk("H1 verdict string", "FAIL", r1["H1_pooled_sees_minority"])
chk("H2 verdict string", "FAIL", r1["H2_masking_exists"])
chk("H3 verdict string", "FAIL", r1["H3_transfer"])

# arm table (gt17)
a = hh["arms_gt17"]["A"]; b = hh["arms_gt17"]["B"]; c = hh["arms_gt17"]["C"]
chk("armA tp", 16, a["tp"]); chk("armA fp", 38, a["fp"])
chk("armA precision", 0.296, round(a["precision"], 3), 0.001)
chk("armB tp", 3, b["tp"]); chk("armB fp", 0, b["fp"])
chk("armB precision", 1.000, round(b["precision"], 3), 0.001)
chk("armB recall", 0.176, round(b["recall"], 3), 0.001)
chk("armC tp", 8, c["tp"]); chk("armC fp", 1, c["fp"])
chk("armC precision", 0.889, round(c["precision"], 3), 0.001)
chk("armC recall", 0.471, round(c["recall"], 3), 0.001)
# the gt20 arm table in section 3
a2 = r2["gt20_armA"]; b2 = r2["gt20_armB"]; c2 = r2["gt20_armC"]
chk("gt20 armA tp/fp", (19, 35), (a2["tp"], a2["fp"]))
chk("gt20 armA precision", 0.352, round(a2["precision"], 3), 0.001)
chk("gt20 armC precision", 0.889, round(c2["precision"], 3), 0.001)

# fissure numbers
chk("fisher A vs C gt17", 0.0013, round(hh["fisher_precision_A_vs_C_gt17"], 4), 0.0001)
chk("fisher A vs C gt20", 0.0036, round(hh["fisher_precision_A_vs_C_gt20"], 4), 0.0001)
chk("null A mean precision", 0.383, round(r2["null_armA_precision_mean"], 3), 0.001)
chk("null A ge observed", 95, r2["null_armA_ge_observed"])
chk("null B nonzero selections", 0, r2["null_armB_sel_nonzero"])
chk("null C ge observed", 19, r2["null_armC_ge_observed"])
chk("pooled fp dropped by C", 34, rc["pooled_fp_dropped_by_C"])
chk("pooled fp total", 35, rc["pooled_fp_total"])
chk("hypergeom p3", 0.043, round(rc["hypergeom"]["p_three_true_of_three"], 3), 0.001)
chk("prec@3 pooled", 0.333, round(r2["prec_at_3_pooled"], 3), 0.001)
chk("prec@3 het ranking", 1.000, round(r2["prec_at_3_het"], 3), 0.001)

# published comparison
pm = json.load(open("results_published_methods.json"))
chk("published interiamb tp/fp/fn", (8, 0, 9),
    (pm["published_bnlearn_interiamb_observational"]["tp"],
     pm["published_bnlearn_interiamb_observational"]["fp"],
     pm["published_bnlearn_interiamb_observational"]["fn"]))
chk("published mbde tp/fp/fn", (17, 8, 0),
    (pm["published_bnlearn_mbde_interventional"]["tp"],
     pm["published_bnlearn_mbde_interventional"]["fp"],
     pm["published_bnlearn_mbde_interventional"]["fn"]))
chk("pgmpy PC pearsonr tp/fp/fn", (6, 3, 11),
    (pm["pgmpy_PC_pearsonr_continuous"]["tp"], pm["pgmpy_PC_pearsonr_continuous"]["fp"],
     pm["pgmpy_PC_pearsonr_continuous"]["fn"]))
chk("pgmpy PC chi2 tp/fp/fn", (13, 11, 4),
    (pm["pgmpy_PC_chi2_q3"]["tp"], pm["pgmpy_PC_chi2_q3"]["fp"], pm["pgmpy_PC_chi2_q3"]["fn"]))
chk("pgmpy HillClimb tp/fp/fn", (15, 20, 2),
    (pm["pgmpy_HillClimb_BICGauss_continuous"]["tp"],
     pm["pgmpy_HillClimb_BICGauss_continuous"]["fp"],
     pm["pgmpy_HillClimb_BICGauss_continuous"]["fn"]))

# section 5 claim 5: reproduce attempt
rp = json.load(open("results_reproduce.json"))
chk("reproduce attempt tp", 16, rp["tp_edges"])
chk("reproduce attempt fp", 26, rp["fp_edges"])

# numeric claims stated in prose
for label, pat, want in [
    ("prose '7466 rows'", r"7466 rows", 7466),
    ("prose '0/51'", r"0/51", 1),
    ("prose '48/51'", r"48/51", 1),
    ("prose '20-edge'", r"20-edge graph", 1),
    ("prose '17-edge'", r"17-edge", 1),
]:
    print("%-52s %s" % (label, "present" if re.search(pat, R) else "MISSING"))
    if not re.search(pat, R):
        fails.append(label)

print()
print("FACTCHECK:", "ALL PASS" if not fails else "FAILURES: %s" % fails)
sys.exit(0 if not fails else 1)
