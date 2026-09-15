# PACKAGING_NOTES — what was changed for the package, and what was not

This file exists because the packaging turn touched two files. Everything else is a
verbatim copy. Nothing in this package changes a measurement, a threshold, a
preregistration or a result — but where a *path* had to change so the package runs
from its own folder, that is recorded here rather than left silent.

---

## 1. What is verbatim

* **Every report** in `reports/` is a byte-identical copy of the frozen file in the
  working tree (`research/*.md`, `bench_cb/*.md`, `bench_ext/*.md`).
* **Every preregistration** in `preregistrations/` is a byte-identical copy of
  `research/PREREG_*.md`.
* **Every producer** in `code/`, `external/bench_cb/`, `external/bench_ext/` is a
  byte-identical copy — with the two exceptions in §2.
* **Every raw matrix, oracle output, independent-pass output, factcheck output and
  diagnostic** in `evidence/results/` and `external/*/results*` is a byte-identical
  copy.
* **The Lean proofs** (`external/bench_cb/lean/union_stoch_v2.lean`,
  `UNION_BOUND.lean`) are byte-identical, and were verified to compile from the
  package (exit 0, no `sorry`).

Verified during packaging by comparing SHA-256 for the frozen campaign modules
(`candidate_gen.py fa9721ae…`, `arbitration.py 2d3d825b…`,
`env_terrarium_v7.py 1bfcba7a…`, `agent_emca_v7.py 64a719d1…`,
`agent_scope_v16.py 663887906377…`) against the package copies: **identical**.

---

## 2. The two files changed, and exactly why

Both changes are **path relocatability only** — they let the code run from inside
the package instead of hardcoding the original working tree. Neither changes any
computation.

### 2.1 `external/bench_cb/lean/mutate_union_lean.py`

| line | before (frozen tree) | after (package) |
|---|---|---|
| 26 | `LEAN_DIR = "/work/Shopify/audit-work/agent_arch/bench_cb/lean"` | `LEAN_DIR = os.path.dirname(os.path.abspath(__file__))` |
| 27 | `MATHLIB = "/work/Shopify/audit-work/mathlib"` | `MATHLIB = os.environ.get("MATHLIB", "/work/Shopify/audit-work/mathlib")` |

**Why:** with the hardcoded `LEAN_DIR`, running the script from inside the package
still wrote its mutants (`m_M*.lean`) and `mutation_summary.json` **into the frozen
working tree**. That is a write to a frozen artefact directory, and it was observed:
the run created ten `m_M*.lean` files and rewrote `mutation_summary.json` under
`bench_cb/lean/`. Making `LEAN_DIR` relative confines the campaign to its own folder.
`MATHLIB` is unchanged in behaviour (same default) and is now overridable by
environment, because the Mathlib checkout lives outside the package.

**Verified equivalent:** after the patch, the campaign re-run in the package produced
the **same** baseline exit code, the **same** 10 mutants, the **same** verdicts, and
rows that are **equal to the pre-patch run ignoring the `seconds` timing field** — and
it wrote **nothing** into the frozen tree (`find … -newermt` over the frozen `lean/`
directory returns 0 files).

### 2.2 Nothing else

No other file was edited. In particular: no report, no preregistration, no
environment, no agent, no driver, no matrix.

---

## 3. What the packaging turn ADDED (new files, no frozen file changed)

| file | what it is |
|---|---|
| `README.md`, `00_OVERVIEW.md` | navigation and the one-page summary |
| `sections/01…06_*.md` | the six publication documents |
| `REPRODUCE.md` | the re-run procedure for every campaign |
| `MANIFEST.md` | size + SHA-256 for every file in the package |
| `make_manifest.py` | the generator for `MANIFEST.md` |
| `verify_package.py` | the package's own checker (links, quoted numbers, matrix counts) with two live negative controls |
| `sources/README.md` | the `src_*` citation index |
| `external/candidate_gen.py`, `external/arbitration.py` | copies of the two frozen campaign modules the bench_cb external test imports from its parent directory — placed so the external test runs from the package |

The two copies in `external/` are byte-identical to the frozen originals (hashes in
§1); they were required because `external/bench_cb/union_agent.py` does
`sys.path.insert(0, os.path.dirname(_HERE))` and then `import candidate_gen`. Without
them the union independent pass raised `ModuleNotFoundError` from inside the package.

---

## 4. How the package was verified (independently)

1. **`verify_package.py`** — 0 failures across three checks: every referenced file
   resolves; every key number appears in a named source report; every quoted matrix
   cell count matches the matrix on disk. Two **negative controls** were run and both
   fired: a fabricated number (`99999.99`) and a broken link
   (`nonexistent_file_xyz.md`) were each caught.
2. **Full campaign re-run from the package** in a scratch directory
   (`code/` + `evidence/results/`→`results/` + `reports/*.md`→`research/`): all six
   campaigns — `run_all_wirehead.sh`, `run_all_v12.sh`, `run_all_v13.sh`,
   `run_all_v14.sh`, `run_all_v15.sh`, `run_all_v16.sh` — exited **0 / ALL GREEN**,
   and the frozen-module hashes printed by the scripts match the recorded values.
3. **External tests from the package**: `bench_transfer.py` →
   `verify_bench_independent.py` **ALL AGREE**; `verify_cb_independent.py`
   **ALL AGREE (negative control fired)**; `verify_union_independent.py`
   **111 checks, 0 failures**; `verify_stopping_independent.py` **ALL PASS**;
   `verify_bayes_independent.py` **VERIFICATION PASSED**; `factcheck_union_report.py`
   **46/46 PASS**.
4. **Lean from the package**: `union_stoch_v2.lean` compiled under
   `lake env lean` with **exit 0**; `mutate_union_lean.py` ran green baseline,
   10 mutants, `mutation_summary.json` written.
5. **Frozen tree untouched**: SHA-256 of the frozen campaign modules and Lean proofs
   re-checked after all runs; unchanged.

---

## 5. Known packaging limitations, stated

* The `src_*` source **bytes** live in the agent's provenance ledger outside the
  package; `sources/README.md` is a citation index, not the frozen downloads. URLs
  are in the reports that quote them.
* The factcheck scripts read the report they check from a sibling `research/`
  directory; `REPRODUCE.md` §1 gives the exact staging that satisfies this.
* `external/bench_ext/env/venv/` (a 498 MiB virtualenv) was **not** copied; install
  dependencies per `REPRODUCE.md` §4.
* `results/matrix_v15` is 287 MiB of deliberately verbose traces (one JSON per cell ×
  210 cells). It is included in full because the v15 result rests on the trace, but a
  reader on a tight disk can drop it and re-run `run_all_v15.sh` to regenerate it.

## 6. GitHub distribution copy (2026-09-15)

The GitHub distribution was prepared in a separate directory; the agent's working
publication package was not modified. Four macOS `.DS_Store` metadata files were
omitted. A `.gitignore` was added for macOS metadata and generated Python bytecode,
and `MANIFEST.md` was regenerated for the distributed files. All research source
files, reports, raw results, the PDF, and its LaTeX source were retained unchanged.
This distribution step does not constitute a new experimental or theorem check.

## 7. Corrected publication, version 2 (2026-09-15)

This update incorporates the author's turn-160 corrections, documented as errata
10 and 11: the replication headline is 25 of 26 verdicts, and the learning claim
now states the model error and oracle reference numerically. The corrected PDF,
editorial documents, announcement and verification scripts were copied from the
agent's publication package. Frozen research code, reports, preregistrations and
raw experimental results were not changed by this update.

In this distribution copy, the Russian announcement's remaining "within 10 %"
wording was also replaced with the same numerical values as the English version.
The original agent work folder was not edited. The distribution README includes
Zenodo version links, and MANIFEST.md was regenerated after packaging.
