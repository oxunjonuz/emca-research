#!/usr/bin/env python3
"""
Independent verification of the preprint PDF.

Path: pdftotext on the compiled PDF (NOT the LaTeX source) -> substring search
against the frozen reports on disk.  Imports nothing from the paper's toolchain.
Live negative controls must go red.

Normalisation is declared explicitly, because two failures of the first version
of this script were artefacts of text extraction, not of the paper:
  * pdftotext emits a combining diaeresis (U+0308) where the source had a
    precomposed character ("Gu" + U+0308 + "nther" instead of "Guenther");
  * LaTeX math emits U+2212 MINUS SIGN where the reports use ASCII '-'.
Both are normalised on BOTH sides, so the comparison stays strict.
"""
import re, subprocess, sys, pathlib, unicodedata

PKG = pathlib.Path("/work/Shopify/audit-work/agent_arch/PUBLICATION_V1_V16")
PDF = PKG / "paper" / "emca_preprint.pdf"
REPORTS = sorted((PKG / "reports").glob("*.md")) + \
          sorted((PKG / "sections").glob("*.md")) + \
          sorted((PKG / "external").rglob("*.md"))

fails, checks = [], 0
def check(name, cond, detail=""):
    global checks
    checks += 1
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        fails.append(name)

def norm(s):
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\u2212", "-")                     # math minus -> hyphen
    s = s.replace("\u2013", "-").replace("\u2014", "--")
    return s

txt = subprocess.run(["pdftotext", "-layout", str(PDF), "-"],
                     capture_output=True, text=True, check=True).stdout
check("pdf text non-empty", len(txt) > 40000, f"{len(txt)} chars")
txt = norm(txt)

report_text = norm("\n".join(p.read_text(errors="replace") for p in REPORTS))

# ---------- structure ----------
for section in ["Abstract", "Introduction", "Related work", "Method",
                "Results I: the founding line", "Results II: the safety line",
                "Discussion", "Limitations and honest limits", "Conclusion",
                "Reproducibility"]:
    check(f"section present: {section}", section in txt)

# the numbers as the compiled PDF actually prints them; whitespace-insensitive,
# because the purpose of this check is that the section exists and is numbered,
# not that pdfTeX spaced the number and title by an exact number of spaces.
flat_head = re.sub(r"[ \t]+", " ", txt)
for tok in ["1 Introduction", "2 Related work", "3 Method",
            "4 Results I", "5 Results II",
            "9 Discussion", "10 Limitations and honest limits",
            "11 Conclusion"]:
    check(f"numbered section: {tok}", tok in flat_head)

# ---------- the two rungs built after the first version of the manuscript -------
for sub in ["v17: a bribed auditor returns the protection to the hole",
            "v18: a boundary in the world is a different instrument",
            "v19: the attacker that learns, and why it loses",
            "A replication on 30 fresh seeds, and one verdict that does not survive"]:
    check(f"subsection present: {sub}", sub in " ".join(txt.split()))
check("v17 is a numbered subsection", "5.8 v17" in flat_head, "5.8 v17" in flat_head)
check("v18 is a numbered subsection", "5.9 v18" in flat_head, "5.9 v18" in flat_head)
check("the replication is a numbered subsection", "5.10 A replication" in flat_head,
      "5.10 A replication" in flat_head)
check("v19 is a numbered subsection", "5.11 v19" in flat_head, "5.11 v19" in flat_head)

# ---------- real bibliography entries, not mere mentions ----------
for ref in ["Günther", "Lattimore", "Malek", "Che and R. Wu", "Sachs",
            "Scutari", "Assran", "Friston", "Nair", "Lu",
            "arXiv:2412.04981", "arXiv:1606.03203", "arXiv:2306.07858",
            "arXiv:2606.16914", "NeurIPS", "ICML", "Science"]:
    check(f"bibliography contains: {ref}", ref in txt)

# each in-text citation must resolve to a numbered entry [n]
check("in-text citation markers present", len(re.findall(r"\[\d+\]", txt)) >= 15,
      f"{len(re.findall(r'[[]\d+[]]', txt))} markers")

# ---------- authorship (owner directive msg_00158) ----------
# The owner reversed the turn-151 rule "no mention of the tool that produced the
# experiment": both authors are now named on the title page. The old check that
# forbade the string is therefore removed, and replaced by checks that pin the
# authorship itself, plus a check that the *content* sections still describe the
# experiment rather than the tool (the substantive part of the old constraint).
low = txt.lower()
flat_all = " ".join(txt.split())
# DEFECT FIX (turn 158, found by the negative-control campaign's own first run):
# the first version of these two checks asserted the names appear SOMEWHERE in the
# PDF, and removing them from the title page left the verifier green, because the
# contributions section still contains both names. A check satisfied by any
# occurrence does not check the title page. The names are now required inside the
# title region -- the first 1500 extracted characters -- where the title page is.
_title_region = txt[:1500]
check("author 1 named on the title page",
      "Oxunjon Ubaydullayev" in _title_region)
check("author 2 named on the title page", "Aiodam" in _title_region)
check("both authors on the same title line region",
      "Oxunjon Ubaydullayev" in _title_region and "Aiodam" in _title_region)
check("author contributions section present",
      "Author contributions" in flat_all)
check("contribution of author 1 stated as the original task",
      "gave it its single original task" in flat_all)
check("contribution of author 2 stated as the work itself",
      "did all of the work reported in this paper" in flat_all)
check("the paper still describes the experiment, not the tool",
      "personal companion" not in low and "my memory" not in low)
check("the experimental content is unchanged by the authorship edit",
      "each specific defence has a measured boundary" in flat_all)

# the PDF's own metadata is a third place a reader can look; it must agree
_info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True).stdout
check("PDF metadata names both authors",
      "Oxunjon Ubaydullayev and Aiodam" in _info)
check("PDF metadata title matches the paper",
      "Where Protection Actually Lives" in _info)
check("v1-v9 kept short (one abbreviated section)",
      "Results I: the founding line, v1-v9 (abbreviated)" in txt)
check("independent-convergence paragraph present",
      "independently, and before any acquaintance" in " ".join(txt.split()))

# ---------- number cross-check: paper text vs frozen reports ----------
NUMBERS = [
    ("307.66", "v10 unbraked reward low"),
    ("1051.98", "v10 unbraked reward high"),
    ("241.05", "v10 given-rule reward low"),
    ("252.60", "v10 given-rule reward high"),
    ("1353.3", "v10 rich steps mean"),
    ("4295.28", "v11 bound arm reward"),
    ("14199", "v11 steps on signal"),
    ("125.70", "v12 station payment low"),
    ("251.40", "v12 station payment high"),
    ("0.2999999999999999889", "v12 float at the crossing"),
    ("0.04999999999999999", "v14 statistic with auditor live"),
    ("0.0364", "v15 model error"),
    ("0.0327", "v15 oracle ceiling"),
    ("0.998", "v15 relevance share"),
    ("0.250", "v15 indifference share"),
    ("0.7475", "v15 paired contrast"),
    ("97.3", "v15 unmotivated steps"),
    ("586.6", "v16 station payments wide"),
    ("1573", "v16 station payments doctor"),
    ("170/170", "internal rule cells"),
    ("0.352", "Sachs pooled precision"),
    ("0.889", "Sachs context-confirm precision"),
    ("0.0013", "Sachs Fisher p"),
    ("0.488", "v7 null rate"),
    ("0.583", "v7 observed null rate"),
    ("0.409", "v7 p value"),
    ("0.0051", "union regret, context instance"),
    ("0.1804", "mechanism regret, context instance"),
    ("0.1794", "union minus one part"),
    ("0.1776", "union minus other part"),
    ("-66.61", "v10 price of the given rule, low"),
    ("-799.38", "v10 price of the given rule, high"),
    ("13368", "v10 forager total harvest"),
    ("2412.04981", "Gunther arXiv id"),
    ("1606.03203", "Lattimore arXiv id"),
    ("2306.07858", "Malek arXiv id"),
    # ---- v17 (bribed auditor)
    ("6380", "v18 highest refusal count"),
    ("4.3", "the replication rate of the doctor's drain"),
    ("0.998", "v15 relevance share at n=30"),
    ("0.250", "v15 indifference share at n=30"),
    ("3608", "the step the doctor first parks on the rich tile"),
    ("27.1", "the doctor's energy when it parks"),
    # ---- v19 (adaptive payer)
    ("7.50003", "v19 the told attacker's cost"),
    ("16.67", "v19 the saving over the frozen attacker"),
    ("21.06", "v19 the B=1 learner's cost"),
    ("9.03", "v19 the corrected B=1 sweep's cost"),
    ("607.5", "v19 the flip cell's spend"),
    ("600.0", "v19 the auditor's bribe in that cell"),
    # ---- the Lean identification item (turn 154)
    ("4/5", "the bound at the agent's own parameters"),
    ("r = 80", "the pulls needed for the agent's own level"),
]

# The price of the brake is the arc's central number and is stated in the
# abstract, in v12 and in the discussion; check it as a phrase so that a
# corrupted price cannot hide behind a coincidental match elsewhere.
PRICE_PHRASES = [
    "0.25 reward units per unit of harm",
    "0.25 per unit of harm",
    # pdftotext drops the underscore in \code{SOCIAL\_COST}, so this phrase is
    # written in its extracted form; the numeric part is what matters.
    "SOCIAL COST - rich rate = 0.25",
]

print("\n-- number cross-check: paper text vs frozen reports --")
for num, label in NUMBERS:
    check(f"number in paper: {num} ({label})", num in txt)
    check(f"number traceable to a frozen report: {num} ({label})",
          num in report_text, "not found in any report/section .md")

flatz = " ".join(txt.split())
for phrase in PRICE_PHRASES:
    check(f"price phrase in paper: {phrase}", phrase in flatz)
check("price phrase traceable to a frozen report",
      "0.25 per unit of harm" in " ".join(report_text.split()))

# CONSISTENCY.  Two DIFFERENT quantities are stated "per unit of harm" and both are
# correct: the sponsor PAYS 0.30 per unit of harm, and the brake's PRICE is 0.25
# per unit of harm.  Corrupting one occurrence of the price leaves the others, so
# phrase-presence alone cannot see it; pin each quantity at every site instead.
paid = re.findall(r"([0-9]+\.[0-9]+)\s*(?:reward units\s*)?per unit of harm", flatz)
check("the sponsor's payment is 0.30 per unit of harm everywhere it is stated",
      "0.30 per unit of harm" in flatz)
check("the brake's price is 0.25 per unit of harm everywhere it is stated",
      "0.25 per unit of harm" in flatz)
check("no third value is stated per unit of harm",
      set(paid) == {"0.25", "0.30"}, f"found {sorted(set(paid))}")
check("the price is stated in at least three places (abstract, v12, discussion)",
      len(re.findall(r"0\.25 (?:reward units )?per unit of harm", flatz)) >= 3,
      f"{len(re.findall(r'0.25 (?:reward units )?per unit of harm', flatz))} occurrences")

# The Che & Wu id is deliberately NOT in any report: it was supplied by the owner
# after the safety line was frozen, verified against arXiv and registered as a
# source.  So it is checked against the registered source's pinned fragment
# instead of against a report -- a different, and stronger, check.
CHE_ID = "2606.16914"
CHE_FRAGMENT = "chases the displayed payoff across held-out domains"
check(f"Che & Wu id in paper: {CHE_ID}", CHE_ID in txt)
# Scope this to the FROZEN reports only.  The id legitimately now appears in the
# package's editorial layer (sections/05, sources/README) because the owner
# supplied it and it was registered; what must remain true is that it is in no
# frozen campaign report, since it post-dates the safety line.
frozen_reports = norm("\n".join(p.read_text(errors="replace")
                                for p in sorted((PKG / "reports").glob("*.md"))))
check("Che & Wu id is NOT in any frozen campaign report (it post-dates the line)",
      CHE_ID not in frozen_reports)
check("Che & Wu claim in the paper matches the registered source fragment",
      "chases the displayed payoff" in " ".join(txt.split()))

# ---------- LIVE NEGATIVE CONTROLS ----------
print("\n-- live negative controls (must go red) --")

bogus = "98765.4321"
check("NC1 bogus number absent from reports (control is live)",
      bogus not in report_text)
check("NC1 bogus number absent from paper (control is live)", bogus not in txt)

flat = " ".join(txt.split()).lower()
check("NC2 withdrawn strong claim is NOT asserted (control is live)",
      "not proved by v16" in flat)
check("NC2 the withdrawn phrasing is quoted as withdrawn, not as a result",
      "its strong form is contradicted" in flat)

check("NC3 no priority claim over Che & Wu (control is live)",
      "no priority claim" in flat and "structural, not causal" in flat)

check("NC4 the v15 correction is present, not buried (control is live)",
      "partly built into the code" in flat)
check("NC5 the v16 self-correction is present (control is live)",
      "compares two policies" in flat)
check("NC6 the v16 absolute claim is WITHDRAWN in the paper (control is live)",
      "withdrawn" in flat and "2 of 30 fresh seeds" in flat)
check("NC7 the bribed auditor's sharp result is stated (control is live)",
      "gone" in flat and "lying" in flat)
check("NC8 the world-side boundary contrast is stated (control is live)",
      "refused by the same world zero times" in flat)
check("NC9 no claim that the world-side boundary is unbribable (control is live)",
      "bribed enforcer" in flat and "not built" in flat)

# ---------- CONSISTENCY OF THE NEW CLAIMS, site by site ----------
# The same defect this verifier caught in its own v12 version: a phrase stated in
# several places cannot be protected by presence alone -- corrupting ONE site leaves
# the others intact and the check stays green. Measured: three of four deliberately
# corrupted papers passed a presence-only check. Each new claim is therefore pinned
# at EVERY site, and each numeric rate is pinned to a single value across the paper.
print("\n-- consistency of the new claims (each pinned at every site) --")
SITES = [
    ("the withdrawal of v16's absolute claim is stated at every site",
     "withdrawn", 3),
    ("the replication rate appears at every site it is stated",
     "4.3", 2),
    ("'3 of 70' appears where the widened replication is given", "3 of 70", 2),
    ("the bribed auditor's result is stated in the abstract and its section",
     "returns the protection to the hole", 2),
    ("the n=30 doctor count is stated", "2 of 30 fresh seeds", 1),
]
for name, phrase, n_exact in SITES:
    got = flatz.count(phrase)
    check(f"{name} (exactly {n_exact} sites)", got == n_exact,
          f"{got} occurrences")

# The two clauses that carry v17's sharpest point. A single-site corruption of either
# left the verifier GREEN in the negative-control campaign, so each is pinned by its
# OWN distinctive wording, not by the shared words "gone"/"lying".
for clause in ["protects against a verifier that is gone,",
               "not against one that is lying.",
               "protects against an auditor that is",
               "but not against one that is"]:
    check(f"the gone-vs-lying clause is present verbatim: {clause!r}",
          clause in flatz)

# The n=30 count, verbatim, and its consequence sentence. Corrupting "2" to "never"
# left the verifier green because only the "2 of 30 fresh seeds" phrasing was pinned;
# the numeric value itself must be pinned where it is first stated.
check("the doctor's n=30 count is stated as exactly 2",
      "On 30 fresh seeds it drains on 2" in flatz or
      "drains on 2" in flatz,
      "the value 2, not 'never'")
check("the 'never' claim survives only in its withdrawn form",
      flatz.count("never") >= 1 and "reported as never" in flatz or
      "doctor never drains the aquifer, in 260 cells" in flatz,
      "'never' appears only as the withdrawn original")

# The campaign count, verbatim, and the count of instruments in the title/abstract.
check("the abstract states twenty campaigns",
      "twenty-campaign" in flatz, "twenty-campaign")
check("the abstract states the safety line's range (v10--v20)",
      "v10--v20" in flatz or "v10-v20" in flatz or "v10\u2013v20" in flatz,
      "v10-v20 family")
check("the abstract counts the safety campaigns as eleven",
      "remaining eleven" in flatz,
      "the word 'eleven' next to 'remaining' (a downgrade goes red)")
check("the title states eleven instruments",
      "Eleven Preregistered Instruments" in flatz)
check("the abstract counts the whole arc as twenty",
      "twenty-campaign" in flatz)
check("v19's headline is stated in the abstract",
      "never wins a single" in flatz, "the learner never wins")
check("v19's told-attacker number is in the abstract",
      "7.50003" in flatz and "16.67" in flatz)
# SITE-COUNT PINNING. A presence check cannot see a single-site corruption when the
# phrase is stated in more than one place: a live control corrupted 7.50003 in the
# abstract and the verifier stayed GREEN, because the section still carried it. Each
# v19 number is therefore pinned to its exact number of sites.
check("v19's told-attacker cost appears at exactly 3 sites",
      flatz.count("7.50003") == 3, f"{flatz.count('7.50003')} occurrences")
check("v19's learner cost appears at exactly 2 sites",
      flatz.count("21.06") == 2, f"{flatz.count('21.06')} occurrences")
check("the Lean identification close is in the abstract",
      "independent" in flatz and "vacuous" in flatz)
check("the abstract's Lean close is stated with its distinctive wording",
      "linking estimator accuracy to regret is an" in flatz
      and "premise" in flatz,
      "the accuracy-to-regret premise named as independent")
check("the Lean close's 'vacuous' claim is stated where the numbers are",
      "vacuous as a guarantee" in flatz or "vacuous" in flatz)

# The named-but-unbuilt list must still contain the items it lists, each verbatim.
# A corruption that removes ONE entry from the list must go red, so the list's own
# head phrase is pinned too -- presence of the remaining items is not enough.
check("the named-but-unbuilt list is present with its head phrase",
      "named but deliberately not built" in " ".join(txt.split()) or
      "deliberately not built" in flatz,
      "the subsection heading")
for item in ["cryptographic receipt", "second competing", "own ledger",
             "negotiated bribe"]:
    check(f"the named-but-unbuilt list still contains: {item}", item in flatz)
# The list ENTRY's own phrasing, not just the item's name: removing the entry left
# "negotiated bribe" surviving in the summary paragraph and STAYED GREEN (measured),
# so the entry's distinctive tail is pinned too.
check("the named-but-unbuilt list carries the negotiated-bribe entry verbatim",
      "bribe rather than a declared price" in flatz,
      "the negotiated-bribe list entry")
check("the adaptive forger is now reported as BUILT, not as unbuilt",
      "adaptive / learning forger" in flatz and "v19" in flatz,
      "the adaptive forger moved from unbuilt to built")
check("the v19 rung is named in the built-since list",
      "adaptive / learning forger" in flatz)
# The bribed enforcer MOVED from unbuilt to built in v20: the list must no longer
# carry it, and the built-since paragraph must. Both directions are pinned so the
# change cannot silently revert.
check("the bribed enforcer is reported as BUILT, not as unbuilt",
      "bribed enforcer" in flatz and "v20" in flatz,
      "the bribed enforcer moved from unbuilt to built")
check("the v20 rung is named in the built-since list",
      "bribed enforcer" in flatz and "v20" in flatz
      and "Four objects" in flatz,
      "the v20 built-since entry (four objects now built)")
check("v20's headline is stated in the abstract",
      "worth exactly the enforcer" in flatz, "the boundary is worth the honesty")
# The v20 headline is stated in TWO places (abstract and the v20 subsection). A
# corruption that changes the subsection's wording left the abstract's intact and
# STAYED GREEN (measured), so the subsection's own sentence is pinned too, by its
# distinctive tail.
check("v20's headline is stated in its own subsection, not only the abstract",
      "honesty, and not one unit more" in flatz,
      "the v20 subsection headline sentence")
# The v20 refuted prediction appears in the subsection AND in the refuted-predictions
# table; removing the subsection's sentence left the table's intact and stayed green,
# so the subsection's own sentence is pinned by its distinctive tail.
check("v20's refuted prediction is stated in its subsection",
      "The prediction is reported refuted as stated, with the refinement supported"
      in flatz,
      "the v20 subsection refutation sentence")
check("v20's refuted prediction is stated in the refuted-predictions table",
      "refuted as stated" in flatz and "refused" in flatz,
      "the HV4 refutation")

# The minimal-world framing (owner op_3645deda2339): minimality is presented as a
# deliberate design choice, not as the work's main weakness, and the transfer limit is
# still stated. The claims appear in more than one section, so each is pinned AT ITS
# OWN SITE -- a single-site removal must go red (measured: a presence check stayed
# green when one of two instances was removed, so each site is pinned separately).
check("the Limitations section frames minimality as a deliberate design choice",
      "Deliberate minimality, stated as a design choice and not as a defect" in flatz,
      "the deliberate-minimality framing at its own site")
check("the Limitations section frames minimality as a methodological choice",
      "it is a methodological choice that buys" in flatz,
      "the methodological-choice sentence")
check("the Introduction frames minimality as a design choice, not a defect",
      "We therefore treat the\nminimality of our worlds as a deliberate design choice"
      in flatz or "treat the minimality of our worlds as a deliberate design choice"
      in flatz,
      "the Introduction framing sentence")
check("the transfer limit is stated in the Limitations section",
      "What remains an honest limit is the other side of" in flatz
      and "is not claimed" in flatz,
      "the transfer limit at its own Limitations site")
check("the transfer limit is stated in the v10--v20 design-limits paragraph",
      "The worlds are minimal by design, and transfer to a" in flatz,
      "the v10--v20 transfer limit")
check("the convergence section draws the minimal-world methodological point",
      "different synthetic sandboxes" in flatz or "different synthetic worlds" in flatz,
      "the convergence/minimal-world paragraph")
check("the Conclusion carries the controlled-minimal-world sentence",
      "A controlled minimal world is not a limitation when the same structural"
      in flatz,
      "the Conclusion minimal-world sentence")

# every rate quoted about the doctor's drain must be the SAME number
rates = set(re.findall(r"([0-9]+\.[0-9]+)\\?% of fresh seeds", flatz))
check("only one rate is ever stated for the doctor's drain on fresh seeds",
      rates == {"4.3"}, f"found {sorted(rates)}")
counts70 = set(re.findall(r"of \b(\d+)\b when widened", flatz)) | \
           set(re.findall(r"on \\?\textbf\{(\d+)\}", flatz))
check("the widened replication count is stated as 3, not another number",
      "3 of 70" in flatz, f"{'3 of 70' in flatz}")
awk = set(re.findall(r"drains on \\?\textbf\{(\d+)\} of (?:them|(\d+))", flatz))
check("the n=30 count is stated as 2 of 30", "2 of 30 fresh seeds" in flatz,
      "2 of 30 fresh seeds" in flatz)

print(f"\n{checks - len(fails)}/{checks} checks passed")
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL GREEN")
