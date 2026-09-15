#!/usr/bin/env python3
"""verify_turn160.py -- independent verification of the turn-160 corrections.

Fresh process. Reads ONLY the disk: the raw fresh-seed cells, the frozen reports, the
editorial layer and the compiled PDF. Imports no producer, no analyzer, no verifier.
Recomputes the two corrected numbers from the raw data by code written here, and checks
that the editorial layer and the PDF now agree with the raw data.

The two corrections:
  erratum 10 -- the n=40 replication count. Stated "26 of 27"; the analyzer's printed
                line counts its own meta-row as a verdict. Honest count: 25 of 26.
  erratum 11 -- the abstract's "learns its world to within 10% of an oracle ceiling".
                The frozen numbers are 0.0364 against 0.0327 -- 11.3% ABOVE the ceiling.
"""
import json
import os
import re
import subprocess
import sys

PKG = "/work/Shopify/audit-work/agent_arch/PUBLICATION_V1_V16"
RAW = os.path.join(PKG, "evidence", "results", "replicate_n40")

fails, checks = [], 0


def check(name, cond, detail=""):
    global checks
    checks += 1
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"  {detail}" if not cond else ""))
    if not cond:
        fails.append(name)


def read(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def cell(tag, seed):
    p = os.path.join(RAW, f"{tag}_{seed}.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


# ---------- erratum 10: the replication count, from the raw cells ----------
print("=== erratum 10: the replication count, recomputed from raw cells ===")
SEEDS = list(range(10, 40))
verdicts = [
    ("v10 B2", lambda: {json.dumps(cell("v10_s2_given_rule_low_c0", s)["commons_left"])
                        for s in SEEDS} == {"9"}),
    ("v10 B3 c0", lambda: {json.dumps(cell("v10_s3_victim_keyed_low_c0", s)["commons_left"])
                           for s in SEEDS} == {"0"}),
    ("v10 B3 c1", lambda: {json.dumps(cell("v10_s3_victim_keyed_low_c1", s)["commons_left"])
                           for s in SEEDS} == {"17"}),
    ("v10 B4 low", lambda: {json.dumps(cell("v10_s4_internalized_low_c0", s)["commons_left"])
                            for s in SEEDS} == {"25"}),
    ("v10 B4 high", lambda: {json.dumps(cell("v10_s4_internalized_high_c0", s)["commons_left"])
                             for s in SEEDS} == {"0"}),
    ("v11 harm 5", lambda: {json.dumps(cell("v11_n_none", s)["commons_drains"])
                            for s in SEEDS} == {"5"}),
    ("v11 inflate g6", lambda: {json.dumps(cell("v11_n_inflate_g6", s)["commons_drains"])
                                for s in SEEDS} == {"30"}),
    ("v11 inflate g10", lambda: {json.dumps(cell("v11_n_inflate_g10", s)["commons_drains"])
                                 for s in SEEDS} == {"30"}),
    ("v12 t0.24", lambda: {json.dumps(cell("v12_v_price_rich_t0.24", s)["commons_drains"])
                           for s in SEEDS} == {"5"}),
    ("v12 t0.25", lambda: {json.dumps(cell("v12_v_price_rich_t0.25", s)["commons_drains"])
                           for s in SEEDS} == {"5"}),
    ("v12 t0.26", lambda: {json.dumps(cell("v12_v_price_rich_t0.26", s)["commons_drains"])
                           for s in SEEDS} == {"30"}),
    ("v12 t0.3", lambda: {json.dumps(cell("v12_v_price_rich_t0.3", s)["commons_drains"])
                          for s in SEEDS} == {"30"}),
    ("v13 lie", lambda: {json.dumps(cell("v13_l_ledger_lie", s)["commons_drains"])
                         for s in SEEDS} == {"30"}),
    ("v13 honest", lambda: {json.dumps(cell("v13_l_ledger_honest", s)["commons_drains"])
                            for s in SEEDS} == {"5"}),
    ("v14 live", lambda: {json.dumps(cell("v14_a_believe_lie_live", s)["commons_drains"])
                          for s in SEEDS} == {"5"}),
    ("v14 none", lambda: {json.dumps(cell("v14_a_believe_lie_none", s)["commons_drains"])
                          for s in SEEDS} == {"30"}),
    ("v16 t0.25", lambda: {json.dumps(cell("v16_w_price_rich_t0.25", s)["commons_drains"])
                           for s in SEEDS} == {"5"}),
    ("v16 t0.26", lambda: {json.dumps(cell("v16_w_price_rich_t0.26", s)["commons_drains"])
                           for s in SEEDS} == {"30"}),
    ("v16 doctor NEVER (absolute form)",
     lambda: {json.dumps(cell("v16_n_doctor_rich_t0.30", s)["commons_drains"])
              for s in SEEDS} == {"0"}),
    ("v17 flip", lambda: {json.dumps(cell("v17_a_believe_flip", s)["commons_drains"])
                          for s in SEEDS} == {"30"}),
    ("v17 silent", lambda: {json.dumps(cell("v17_a_failclosed_silent", s)["commons_drains"])
                            for s in SEEDS} == {"5"}),
    ("v18 station", lambda: {json.dumps(cell("v18_w_price_station", s)["commons_drains"])
                             for s in SEEDS} == {"0"}),
    ("v18 widen", lambda: {json.dumps(cell("v18_w_widen_none", s)["commons_drains"])
                           for s in SEEDS} == {"30"}),
]


def a0share(tag):
    out = []
    for s in SEEDS:
        r = cell(tag, s)
        if r is None:
            continue
        tr = r["trace"]
        out.append(sum(1 for x in tr if x["action"] == "a0") / len(tr))
    return out


import statistics
_ctx, _rel, _rnd = a0share("v15_ig_ctx"), a0share("v15_ig_relevant"), a0share("v15_rand")
verdicts += [
    ("v15 H2 information gain indifferent",
     lambda: abs(statistics.mean(_ctx) - 0.25) < 0.02),
    ("v15 H3 criterion restores preference",
     lambda: statistics.mean(_rel) > 0.95),
    ("v15 H6 random at the coin floor",
     lambda: abs(statistics.mean(_rnd) - 0.25) < 0.02),
]
hold = sum(1 for _, f in verdicts if f())
check("the replication has 26 verdicts", len(verdicts) == 26, str(len(verdicts)))
check("25 of 26 hold", hold == 25, f"{hold} hold")
check("the single failure is v16's absolute claim",
      not dict(verdicts)["v16 doctor NEVER (absolute form)"]())

n_doc = sum(1 for s in SEEDS
            if (cell("v16_n_doctor_rich_t0.30", s) or {}).get("commons_drains", 0) > 0)
check("the doctor drains on 2 of 30 fresh seeds", n_doc == 2, str(n_doc))

# the analyzer's own artifact must still record 27 checks / 26 pass (the meta-row)
aj = json.load(open(os.path.join(PKG, "evidence", "results", "analyze_n40.json")))
check("the analyzer artifact records 27 checks, 26 pass",
      len(aj["verdicts"]) == 27 and sum(1 for x in aj["verdicts"] if x["holds"]) == 26)
check("exactly one analyzer row is a meta-row (not a verdict)",
      sum(1 for x in aj["verdicts"] if x["claim"].startswith("REPLICATION FINDING")) == 1)

# ---------- erratum 11: the v15 learning claim ----------
print("\n=== erratum 11: the v15 learning claim ===")
v15 = read(os.path.join(PKG, "reports", "RESULTS_V15.md"))
check("the frozen report gives err 0.0364 and ceiling 0.0327",
      "0.0364" in v15 and "0.0327" in v15)
ratio = 0.0364 / 0.0327
check("the ratio is above 1.10 (so 'within 10%' is false)", ratio > 1.10,
      f"ratio {ratio:.4f}")
tex = read(os.path.join(PKG, "paper", "emca_preprint.tex"))
check("the paper states the claim with the report's numbers",
      "model error of $0.036$ against an oracle ceiling of $0.033$" in tex)
check("the paper no longer says 'within 10% of an oracle ceiling'",
      "within 10\\% of an oracle ceiling" not in tex
      and "within 10% of an oracle ceiling" not in tex)

# ---------- the editorial layer agrees ----------
print("\n=== the editorial layer ===")
for rel, needle in [("00_OVERVIEW.md", "25 of 26"),
                    ("sections/04_v10_v16_safety_line.md", "25 of 26"),
                    ("sections/06_limitations_and_honesty.md", "25 of 26"),
                    ("REPRODUCE.md", "25 of 26"),
                    ("ERRATA.md", "Erratum 10"),
                    ("ERRATA.md", "Erratum 11")]:
    check(f"{rel} carries {needle!r}", needle in read(os.path.join(PKG, rel)))
ann = read(os.path.join(PKG, "ANNOUNCEMENT.md"))
check("the announcement carries the corrected v15 numbers",
      "model error of 0.036 against an oracle ceiling of" in ann)
check("the announcement does not carry 'within 10%'",
      "within 10% of an oracle ceiling" not in ann)

# ---------- the compiled PDF agrees (read the PDF, not the source) ----------
print("\n=== the compiled PDF ===")
txt = subprocess.run(["pdftotext", "-layout",
                      os.path.join(PKG, "paper", "emca_preprint.pdf"), "-"],
                     capture_output=True, text=True, check=True).stdout
flatz = " ".join(txt.split())
check("the PDF states 25 of 26 headline verdicts",
      "25 of 26 headline verdicts" in flatz)
check("the PDF does not state 26 of 27 as a claim",
      "26 of 27 headline verdicts" not in flatz and "26 of 27 replicated" not in flatz)
check("the PDF carries the count correction",
      "On the count itself" in flatz and "counts its own meta-row" in flatz)
check("the PDF states the v15 claim with the report's numbers",
      "model error of 0.036 against an oracle ceiling of 0.033" in flatz)
check("the PDF does not state 'within 10% of an oracle ceiling'",
      "within 10% of an oracle ceiling" not in flatz)

# ---------- the frozen record is untouched ----------
print("\n=== the frozen record ===")
TREE = os.path.dirname(PKG)
for rel in ["reports/RESULTS_N40_REPLICATION.md", "reports/RESULTS_V15.md",
            "reports/RESULTS_SCOPE_V16.md"]:
    p = os.path.join(PKG, rel)
    q = os.path.join(TREE, "research", os.path.basename(rel))
    if os.path.exists(q):
        check(f"{rel} is byte-identical to the frozen tree",
              read(p) == read(q))

print(f"\n{checks - len(fails)}/{checks} checks passed")
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL GREEN — the turn-160 corrections are verified independently of the tools "
      "that made them")
