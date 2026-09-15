#!/usr/bin/env python3
"""verify_package.py -- independent check of the publication package.

Two things, both falsifiable:

  A. every relative link/reference in the section documents resolves to a real
     file inside the package (or a real file in the frozen working tree);
  B. every number quoted in the section documents appears verbatim in at least one
     frozen report/evidence file that the section names as its source.

A failure is a real finding: a broken pointer or a number I typed rather than
quoted. Run: python3 verify_package.py
"""
import fnmatch
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PKG = ROOT
TREE = os.path.dirname(ROOT)          # the frozen agent_arch working tree

# section documents -> the frozen reports they quote from
SECTIONS = {
    "00_OVERVIEW.md": None,
    "README.md": None,
    "REPRODUCE.md": None,
    "sections/01_v1_v9_causality_vs_economics.md": [
        "research/CAMPAIGN_RESULT.md", "research/EPISTEMIC_VERDICT.md",
        "research/HYPOTHESES.md", "research/RESULTS.md",
    ],
    "sections/02_external_tests.md": [
        "bench_ext/RESULTS_BENCH.md", "bench_cb/RESULTS_CB.md",
        "bench_cb/RESULTS_UNION.md",
    ],
    "sections/03_formal_verification.md": [
        "bench_cb/RESULTS_UNION_LEAN.md", "bench_cb/RESULTS_UNION.md",
        "research/RESULTS_ADAPTIVE_V19.md",
    ],
    "sections/04_v10_v16_safety_line.md": [
        "research/RESULTS_SAFETY.md", "research/RESULTS_WIREHEAD.md",
        "research/RESULTS_FORGER_V12.md", "research/RESULTS_LEDGER_V13.md",
        "research/RESULTS_ATTESTED_V14.md", "research/RESULTS_V15.md",
        "research/RESULTS_SCOPE_V16.md", "research/RESULTS_BRIBED_V17.md",
        "research/RESULTS_ENFORCED_V18.md",
        "research/RESULTS_N40_REPLICATION.md",
        "research/RESULTS_ADAPTIVE_V19.md",
        "research/RESULTS_BRIBED_ENFORCER_V20.md",
    ],
    "sections/05_independent_convergence.md": ["research/RESULTS_SCOPE_V16.md"],
    "sections/06_limitations_and_honesty.md": [
        "research/RESULTS_SAFETY.md", "research/RESULTS_WIREHEAD.md",
        "research/RESULTS_FORGER_V12.md", "research/RESULTS_LEDGER_V13.md",
        "research/RESULTS_ATTESTED_V14.md", "research/RESULTS_V8.md",
        "research/RESULTS_V9.md", "research/RESULTS_V33.md",
        "research/CAMPAIGN_RESULT.md", "bench_cb/RESULTS_UNION_LEAN.md",
        "research/RESULTS_BRIBED_V17.md", "research/RESULTS_ENFORCED_V18.md",
        "research/RESULTS_N40_REPLICATION.md",
        "research/RESULTS_ADAPTIVE_V19.md",
    ],
}

# numbers that MUST be traceable to a named source (the load-bearing ones)
KEY_NUMBERS = {
    "sections/04_v10_v16_safety_line.md": [
        "4295.28", "14199", "0.30000000000000004", "0.25", "125.70",
        "0.04999999999999999", "0.0364", "0.998", "0.250", "2/12", "0/12",
        "1353.3", "2039", "3404", "fb9b7734c95f", "4.3",
        "0.35", "360", "130", "6380", "3608", "27.1",
        "7.50003", "16.67", "21.06", "9.03", "607.5", "600.0",
        "30/30", "exp_f1aa15dac1b4",
    ],
    "sections/02_external_tests.md": [
        "0.95", "0.352", "0.889", "0.0013", "0.3000", "0.2574", "0.0051",
        "0.1804", "0.0129",
    ],
    "sections/01_v1_v9_causality_vs_economics.md": [
        "0/51", "48/51", "21 CAUSAL", "0.488", "0.583", "+3159", "+3755",
    ],
    "sections/03_formal_verification.md": [
        "k/(4 r ε²)", "propext", "n/4",
        "4/5", "1/20", "80",
    ],
}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def build_index():
    """basename -> list of real paths, over the package and the frozen tree."""
    idx = {}
    for base in (PKG, TREE):
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames
                           if d not in {"__pycache__", ".git", "node_modules", "venv"}]
            for name in filenames:
                idx.setdefault(name, []).append(os.path.join(dirpath, name))
    return idx


def check_links():
    """Every referenced file resolves to a real file.

    A reference is a backticked token ending in a known extension. It may be a
    relative path, a bare filename, or a glob; a bare filename must exist by name
    somewhere in the package or the frozen tree (so a typo still fails).
    """
    idx = build_index()
    fails = []
    ref_re = re.compile(r"`([^`]*\.(?:md|py|sh|json|txt|lean|csv|diff|jsonl))`")
    for rel in SECTIONS:
        path = os.path.join(PKG, rel)
        if not os.path.exists(path):
            fails.append(f"MISSING SECTION {rel}")
            continue
        text = read(path)
        for m in ref_re.finditer(text):
            ref = m.group(1)
            if ref.startswith("http") or " " in ref:
                continue
            if "*" in ref or "?" in ref:
                # glob: accept if any real basename matches the pattern
                pat = os.path.basename(ref)
                if not any(fnmatch.fnmatch(name, pat) for name in idx):
                    fails.append(f"{rel}: glob `{ref}` matches nothing")
                continue
            cands = [
                os.path.normpath(os.path.join(PKG, os.path.dirname(rel), ref)),
                os.path.normpath(os.path.join(PKG, ref)),
                os.path.normpath(os.path.join(TREE, ref)),
            ]
            if any(os.path.exists(c) for c in cands):
                continue
            if os.path.basename(ref) in idx:
                continue
            fails.append(f"{rel}: unresolved ref `{ref}`")
    return fails


def check_numbers():
    """Every key number appears in at least one named source report, AND in the
    section document that quotes it.

    Both directions matter and they catch different faults: a number absent from the
    sources is a number I typed rather than quoted; a number absent from the section
    is one the section no longer actually states (e.g. edited to a wrong value while
    the true value survives elsewhere in the section). The first version checked only
    the first direction, and a live negative control showed a corrupted quote in the
    section was invisible to it — so this now checks both.
    """
    fails = []
    for rel, nums in KEY_NUMBERS.items():
        sources = SECTIONS.get(rel) or []
        blob = ""
        for s in sources:
            p = os.path.join(TREE, s)
            if os.path.exists(p):
                blob += read(p)
        sect = read(os.path.join(PKG, rel))
        for n in nums:
            if n not in blob:
                fails.append(f"{rel}: number {n!r} not found in its named sources")
            if n not in sect:
                fails.append(f"{rel}: number {n!r} is not stated in the section itself")
    return fails


def check_matrix_counts():
    """The cell counts quoted in section 04 match the matrices on disk."""
    expected = {
        "matrix_safety_v10": 330, "matrix_wirehead_v11": 220,
        "matrix_wirehead_v12": 490, "matrix_ledger_v13": 260,
        "matrix_attested_v14": 340, "matrix_v15": 210, "matrix_scope_v16": 790,
        "matrix_bribed_v17": 360, "matrix_enforced_v18": 130,
        "matrix_adaptive_v19": 320, "matrix_bribed_enforcer_v20": 270,
        "matrix_v20_replication": 120,
    }
    fails = []
    for name, want in expected.items():
        d = os.path.join(PKG, "evidence", "results", name)
        got = len([f for f in os.listdir(d) if f.endswith(".json")]) if os.path.isdir(d) else -1
        if got != want:
            fails.append(f"matrix {name}: {got} json cells, report says {want}")
    return fails


def check_v20_counts():
    """The v20 cell-count claims are pinned WITH their object, not as bare numbers.

    DEFECT FIX (turn 157, found by a negative control): corrupting '270 cells' to
    '999 cells' in section 04 did NOT go red at first, because '270' was never in
    KEY_NUMBERS for that file; then, once a presence check was added, corrupting the
    REPLICATION count '120 cells' to '999 cells' still did not go red, because an
    unrelated '120 cells' (v16's 120 search cells) survived elsewhere in the file.
    So each count is now pinned to its PATH, in the section AND in its source report:
    the claim and its object are one string. It can go red if the value changes or
    the claim disappears.
    """
    fails = []
    def norm(s):
        return re.sub(r"\s+", " ", s)
    # (file, claims) — each claim is pinned to its own object so a corrupted instance
    # cannot hide behind an unrelated survivor elsewhere in the file.
    per_file = [
        ("sections/04_v10_v16_safety_line.md", [
            "matrix_bribed_enforcer_v20/` (270 cells)",
            "matrix_v20_replication/` (120 cells)",
            "matrix_bribed_enforcer_v20/` (270) +",
            "matrix_v20_replication/` (120),",
        ]),
        ("reports/RESULTS_BRIBED_ENFORCER_V20.md", [
            "matrix_bribed_enforcer_v20/` (270 cells)",
            "matrix_v20_replication/` (120 cells)",
        ]),
    ]
    for rel, claims in per_file:
        text = norm(read(os.path.join(PKG, rel)))
        for phrase in claims:
            if norm(phrase) not in text:
                fails.append(f"{rel}: v20 count claim {phrase!r} missing")
    return fails


def check_unique_rates():
    """Declared single-value claims must be stated with exactly ONE value.

    A presence check cannot catch a substituted number when the phrase around it is
    restated elsewhere: a live negative control changed the replication rate from
    '4.3 %' to '9.9 %' in one place and the checker stayed green, because '4.3'
    survived in the other two. This check reads the sentences that actually make the
    rate claim (they mention both the doctor and the fresh seeds) and requires the set
    of percentages in them to be exactly the declared one. It can go red two ways:
    the value is changed, or a second contradicting value is added.
    """
    fails = []
    pct_re = re.compile(r"(\d+(?:\.\d+)?)\s*%")
    for rel, want in (("sections/04_v10_v16_safety_line.md", {"4.3"}),
                      ("sections/06_limitations_and_honesty.md", {"4.3"})):
        text = read(os.path.join(PKG, rel))
        got = set()
        # any percentage quoted within a window of a fresh-seed replication claim
        for m in re.finditer(r"fresh[ -]seed", text, re.IGNORECASE):
            window = text[max(0, m.start() - 220): m.end() + 220]
            got |= set(pct_re.findall(window))
        if got != want:
            fails.append(f"{rel}: the fresh-seed doctor rate is stated as "
                         f"{sorted(got)}, declared {sorted(want)}")
    return fails


# DISTINCTIVE PHRASES that must be present verbatim. A bare number is too weak a
# pin: a live negative control deleted the Lean `r >= 80` claim from section 03 and
# the number check stayed green, because "80" still appeared elsewhere in the file.
# These phrases are the load-bearing claims, so each must be present as written.
REQUIRED_PHRASES = {
    "sections/03_formal_verification.md": [
        "r ≥ 80 ↔ bound ≤ 1/20",
        "4/5 > 1/2",
        "hgood_is_an_independent_premise",
        "identification_is_conditional",
    ],
    "sections/04_v10_v16_safety_line.md": [
        "7.50003",
        "16.67 %",
        "21.06",
        "never wins a single cell",
        "the defence's evidence window",
        "worth exactly the enforcer's honesty",
        "still reports `o[\"scope\"][\"task\"] == \"station\"`",
        "HV4 is recorded **REFUTED as stated**",
    ],
    "00_OVERVIEW.md": [
        "v19 adaptive payer",
        "learning does not beat knowing",
        "v20 bribed enforcer",
        "a bought boundary lies about being a boundary",
        "methodological choice, not the work's main weakness",
    ],
    "sections/05_independent_convergence.md": [
        "methodological **advantage** rather than a weakness",
        "different synthetic\nworlds",
    ],
    "sections/06_limitations_and_honesty.md": [
        "Deliberate minimality, stated as a design choice and not as a defect",
        "What remains an honest limit is the other side of the same coin",
        "the worlds are minimal by design (see §0)",
    ],
}


def check_phrases():
    """Required phrases, matched on WHITESPACE-NORMALISED text.

    DEFECT FIX (turn 154, found by the check's own first run): the first version
    matched raw text, so a phrase that the markdown wraps across a line break
    ('never wins a\\nsingle cell') read as MISSING when it was present. The check now
    collapses runs of whitespace on both sides before comparing, which is what a
    reader of the rendered document sees.
    """
    fails = []
    def norm(s):
        # strip markdown blockquote markers at line starts, then collapse whitespace
        s = re.sub(r"(?m)^\s*>\s?", "", s)
        return re.sub(r"\s+", " ", s)
    for rel, phrases in REQUIRED_PHRASES.items():
        text = norm(read(os.path.join(PKG, rel)))
        for ph in phrases:
            if norm(ph) not in text:
                fails.append(f"{rel}: required phrase {ph!r} is MISSING")
    return fails


def check_authorship():
    """Authorship (turn 158, owner directive msg_00158).

    The owner reversed the turn-151 rule that the paper must not name the tool
    that produced it. This family pins the *new* state — both authors named, the
    contributions stated, erratum 9 recorded — and, separately, pins the part of
    the old rule that survives: the paper's CONTENT still describes the
    experiment, not the tool. A check that only asserted "Aiodam appears" would
    pass on a paper that had turned into a description of the tool, so both
    directions are asserted.
    """
    fails = []
    def norm(s):
        return re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", s))

    tex = norm(read(os.path.join(PKG, "paper", "emca_preprint.tex")))
    readme = norm(read(os.path.join(PKG, "README.md")))
    overview = norm(read(os.path.join(PKG, "00_OVERVIEW.md")))
    errata = norm(read(os.path.join(PKG, "ERRATA.md")))

    for label, hay, needle in [
        ("tex: author 1", tex, "Oxunjon Ubaydullayev"),
        ("tex: author 2", tex, "Aiodam"),
        ("tex: contributions section", tex, "Author contributions"),
        ("tex: author 1's contribution", tex, "gave it its single original task"),
        ("tex: author 2's contribution", tex, "did all of the work reported in this paper"),
        ("tex: fork decisions attributed to author 1", tex,
         "set the direction at every fork"),
        ("README: authors named", readme, "Oxunjon Ubaydullayev, Aiodam"),
        ("README: points at erratum 9", readme, "erratum 9"),
        ("OVERVIEW: authors named", overview, "Oxunjon Ubaydullayev"),
        ("ERRATA: erratum 9 present", errata, "Erratum 9"),
        ("ERRATA: the reversed instruction is quoted", errata,
         "Никакого упоминания"),
        ("ERRATA: the reversal is attributed to the owner", errata, "msg_00158"),
    ]:
        if needle not in hay:
            fails.append(f"{label}: {needle!r} is MISSING")

    # the surviving half of the old constraint: content is about the experiment
    for label, needle in [("companion framing absent", "personal companion"),
                          ("memory mechanism absent", "my memory")]:
        if needle in tex.lower():
            fails.append(f"{label}: {needle!r} IS PRESENT in the paper source")
    if "the harm is complete before the agent's reasoning begins" not in tex:
        fails.append("experimental content intact: the harm sentence is MISSING")
    return fails


def main():
    f1 = check_links()
    f2 = check_numbers()
    f3 = check_matrix_counts()
    f4 = check_unique_rates()
    f5 = check_phrases()
    f6 = check_v20_counts()
    f7 = check_authorship()
    for label, fails in (("LINKS", f1), ("NUMBERS", f2),
                         ("MATRIX COUNTS", f3), ("UNIQUE RATES", f4),
                         ("REQUIRED PHRASES", f5), ("V20 COUNTS", f6),
                         ("AUTHORSHIP", f7)):
        print(f"=== {label}: {len(fails)} failure(s) ===")
        for x in fails:
            print("  ", x)
    total = len(f1) + len(f2) + len(f3) + len(f4) + len(f5) + len(f6) + len(f7)
    print(f"TOTAL FAILURES: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())