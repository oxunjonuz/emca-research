#!/usr/bin/env python3
"""Run EXTERNAL published causal-discovery implementations (pgmpy) on the
external Sachs benchmark, so the comparison is against methods nobody here
wrote. pgmpy implements the published PC / GES / HillClimb algorithms with
their standard CPDAG output. Same data, same ground truth, same file.
"""
import csv, json, warnings
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

OBS = "ds/sachs.2005.continuous.txt"
EXPER = "ds/sachs.experimental.mixed.txt"

GT17 = [("pkc","pka"),("pkc","raf"),("pka","raf"),("pkc","mek"),("pka","mek"),
        ("raf","mek"),("mek","erk"),("pka","erk"),("erk","akt"),("pka","akt"),
        ("pkc","p38"),("pka","p38"),("pkc","jnk"),("pka","jnk"),("plc","pip3"),
        ("plc","pip2"),("pip3","pip2")]


def key(a, b):
    return (a, b) if a < b else (b, a)


def skeleton_of(edges):
    return {key(a, b) for a, b in edges}


def score(skel, gt):
    tp = len(skel & gt); fp = len(skel - gt); fn = len(gt - skel)
    return dict(tp=tp, fp=fp, fn=fn,
                precision=(tp / len(skel) if skel else 0.0),
                recall=(tp / len(gt) if gt else 0.0))


def load_discrete():
    rows = list(csv.reader(open(OBS), delimiter="\t"))
    df = pd.DataFrame(rows[1:], columns=rows[0])
    return df.astype(float)


def main():
    from pgmpy.estimators import PC, HillClimbSearch
    from pgmpy.structure_score import BICGauss, BIC

    # bnlearn discretised the data with Hartemink's information-preserving
    # method into 3 levels; pgmpy's chi_square test needs discrete data, so
    # I use quantile 3-level binning (DECLARED ADAPTATION - not the same
    # discretisation as the published bnlearn run).
    df = load_discrete()
    d3 = df.apply(lambda c: pd.qcut(c, 3, labels=[0, 1, 2]).astype("category"))
    gt = {key(a, b) for a, b in GT17}
    out = {}

    # ---- PC (constraint-based, the family inter.iamb belongs to) ----
    pc = PC(d3)
    m = pc.estimate(ci_test="chi_square", return_type="cpdag", show_progress=False)
    edges = [e for e in m.edges()]
    out["pgmpy_PC_chi2_q3"] = score(skeleton_of(edges), gt)
    out["pgmpy_PC_chi2_q3"]["n_edges"] = len(edges)

    # ---- HillClimb with BIC on the discretised data (declared adaptation) ----
    hc = HillClimbSearch(df)
    best = hc.estimate(scoring_method='bic-g', show_progress=False)
    edges = [e for e in best.edges()]
    out["pgmpy_HillClimb_BICGauss_continuous"] = score(skeleton_of(edges), gt)
    out["pgmpy_HillClimb_BICGauss_continuous"]["n_edges"] = len(edges)
    # ---- PC on the CONTINUOUS data with Fisher-z (the closest external
    # analogue of bnlearn's inter.iamb with test='cor') ----
    pc2 = PC(df)
    m2 = pc2.estimate(ci_test="pearsonr", return_type="cpdag", show_progress=False)
    e3 = [e for e in m2.edges()]
    out["pgmpy_PC_pearsonr_continuous"] = score(skeleton_of(e3), gt)
    out["pgmpy_PC_pearsonr_continuous"]["n_edges"] = len(e3)

    # ---- the published external numbers, restated ----
    out["published_bnlearn_interiamb_observational"] = dict(
        tp=8, fp=0, fn=9, precision=1.0, recall=8 / 17,
        note="skeleton of the DAG inter.iamb returns on the raw continuous "
             "file with test='cor'; 8 arcs, only 2 directed")
    out["published_bnlearn_mbde_interventional"] = dict(
        tp=17, fp=8, fn=0, precision=17 / 25, recall=1.0,
        note="intervention-aware model averaging vs the validated network")

    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
