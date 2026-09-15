# EMCA / agent_arch — publication package, campaigns v1–v20

**Corrected preprint and reproducibility archive — publication version 2:**
[Zenodo — DOI: 10.5281/zenodo.22772224](https://doi.org/10.5281/zenodo.22772224).
This version incorporates errata 10 and 11, updates the PDF and checking scripts,
and corrects both language versions of the announcement. Frozen experimental
code, reports, preregistrations and raw results are unchanged. The Zenodo record
links to the exact Git commit contained in its ZIP archive.

The original publication remains available at
[DOI: 10.5281/zenodo.22762848](https://doi.org/10.5281/zenodo.22762848), with the
original archive at commit
[`678dee6`](https://github.com/oxunjonuz/emca-research/tree/678dee668bad6c4a237234ad818f1f5d3eb2896b).
[The all-versions DOI](https://doi.org/10.5281/zenodo.22762847) resolves to the latest
published version.

This folder is a **packaging** of work already done and already frozen. It adds no
new measurement, moves no threshold, and softens no result. Every number in the
section documents is quoted from a report that is itself in `reports/`, and every
report is backed by raw cells in `evidence/`, a preregistration in
`preregistrations/`, and a verification log in `evidence/results/`.

**The preprint itself is `paper/emca_preprint.pdf`** (29 pages, LaTeX source
`paper/emca_preprint.tex`, build + independent verification `paper/build_paper.sh`).
It is the publication form of this package: abstract, introduction, related work,
method, results (v1--v9 abbreviated as foundation, v10--v20 as the main body),
external tests, formal verification, independent convergence, discussion,
limitations, references. The title page carries the two authors
(Oxunjon Ubaydullayev, Aiodam) and an author-contributions statement — see
erratum 9 in `ERRATA.md`, which reverses the earlier "no mention of the tooling"
instruction; the body of the paper still describes the experiment and its
results, not the tool.

If you are reading this for the first time, read in this order:

1. **`00_OVERVIEW.md`** — what the whole thing is, in one page, with the honest
   headline of each campaign.
2. **`sections/`** — six sections, each self-contained:
   * `01_v1_v9_causality_vs_economics.md` — the founding line, kept short (it is
     the ground everything else grew on).
   * `02_external_tests.md` — the honest re-assessment of scientific novelty
     against published literature (Sachs 2005, causal bandits, the union
     mechanism), with exact citations.
   * `03_formal_verification.md` — the Lean 4 proofs: what is proved, what
     remains a conjecture, and the honest boundary — including the turn-154 close
     of the modelling-identification item (§5.1: the identification is a
     *conditional*, `hgood` is an *independent premise*, and at the agent's own
     parameters the bound is vacuous).
   * `04_v10_v16_safety_line.md` — the central, strongest part: wayfinding-shaped
     harm, the purchasability of built-in values, the ledger and its hole, the
     truth-does-not-select-action collapse, the blast-radius boundary, the bought
     auditor (v17), the world-side boundary (v18), the 30-seed replication, the
     learning attacker (v19), and the bought enforcer (v20).
   * `05_independent_convergence.md` — the NVIDIA/Rutgers (Che & Wu, 2026)
     convergence, with the exact status of that citation.
   * `06_limitations_and_honesty.md` — every declared limit, every refuted
     prediction, every defect found in the author's own work.
3. **`REPRODUCE.md`** — how to re-run everything from scratch, one command per
   campaign, with the exact environment and the layout the scripts expect.
4. **`MANIFEST.md`** — the file inventory with sizes and SHA-256 for the frozen
   artefacts.
5. **`PACKAGING_NOTES.md`** — what was copied verbatim, and the two path-only edits
   made so the package runs from its own folder.
6. **`ERRATA.md`** — **read this before quoting anything.** Ten over-statements in
   this package's own section documents: four found by the owner's re-reading in turn
   151 and corrected here, two found in turn 152 — v16's withdrawn absolute
   headline (caught by the author's own fresh-seed replication) and the author's own
   preprint verifier reporting a catch it did not make — one in turn 154: a
   preregistered prediction (v19's HQ4d) refuted by the author's own code defect, with
   eight further defects of the checking layer recorded alongside it, and one in turn
   157: v20's preregistered invisibility claim (HV4's "`refused` is False in both")
   refuted by the author's own measurement — the flag does change; the invisibility is
   a property of the agent not reading `o["scope"]`; and two in turn 160, both found by
   recounting from the raw data rather than reading it: the replication count "26 of 27"
   was inflated by an analyzer line counting its own meta-row as a verdict — recounted
   from the raw cells, the honest count is **25 of 26** — and the abstract's "learns its
   world to within 10 % of an oracle ceiling" was **11.3 % above** the ceiling, not
   within 10 % (0.0364 against 0.0327). The frozen reports themselves are unchanged.

## Directory map

| folder | what is in it |
|---|---|
| `paper/` | **the preprint** — `emca_preprint.pdf`, its LaTeX source, the build script and the independent verifier |
| `sections/` | the six section documents the preprint was written from |
| `reports/` | every results/report document, verbatim, as frozen (`RESULTS_*.md`, `CAMPAIGN_RESULT.md`, `EPISTEMIC_VERDICT.md`, `TURN*_STATUS.md`, …) |
| `preregistrations/` | every `PREREG_*.md`, written **before** the first cell of its campaign |
| `code/` | every producer: environments, agents, runners, drivers, analyzers, oracles, independent verifiers, factchecks, `run_all_*.sh` |
| `evidence/results/` | the raw matrices (`matrix_*`), oracle outputs, independent-pass outputs, factcheck outputs, diagnostics |
| `external/bench_cb/` | the causal-bandit external test: ported published code (`ext/`), Lean proofs (`lean/`), matrices, verifiers |
| `external/bench_ext/` | the Sachs-2005 external test: data (`ds/`), measurement scripts, head-to-head against published methods |
| `sources/` | the registered external sources cited by the reports (see `sources/README.md`) |

Plus: `REPRODUCE.md` (how to re-run everything), `MANIFEST.md` (size + SHA-256 for
every file), `PACKAGING_NOTES.md` (what was copied verbatim and the two path-only
edits), `verify_package.py` (the package's own checker, with two live negative
controls), and `make_manifest.py`.

## What this package is NOT

* It is **not** a new result. Nothing here was measured for the first time in the
  packaging turn.
* It is **not** a claim about any frozen line it builds on: v10–v20 are verdicts on
  their own instruments, never on the frozen v1–v9 line, and the reports say so in
  their first paragraphs.
* It is **not** a novelty claim. Section 02 and section 05 exist precisely to put
  the published prior art next to the campaign's claims.
* It does **not** hide failures. Refuted predictions, checks that could not fail,
  a verifier that over-claimed, a first-pass matrix deleted rather than kept —
  all of these are in the reports and collected in section 06.
