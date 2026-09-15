# REPRODUCE — how to re-run everything from scratch

*The owner asked for a package from which "любой человек со стороны мог сам всё
перепроверить с нуля". This file is the procedure. Every campaign is one command,
frozen as one experiment, and ends with `ALL GREEN` or a non-zero exit.*

---

## 0. Environment

* **Python 3.12** (measured: `Python 3.12.13`). Standard library only for the
  campaign proper; the external tests additionally use `numpy`, `scipy`, `pgmpy`
  (see §4).
* **Lean 4.19.0** for the formal verification (§5), via the Mathlib checkout at
  `/work/Shopify/audit-work/mathlib`.
* **`PYTHONHASHSEED=0`** throughout — the `run_all_*.sh` scripts export it. This is
  not cosmetic: the campaign found a real hash-order non-determinism in its own
  competence at turn 115, and the external test found the same defect class in
  pgmpy (see section 06 §3).
* **No GPU, no training corpus.** Every agent is a hand-written policy; every
  environment is a small grid world.

All paths below are relative to the package root unless absolute.

---

## 1. The safety line, v10–v20 (the central part)

Each of these is a single script that runs the world oracle, the matrix driver
(resumable), the analysis, the independent pass, and the factcheck, and prints
`ALL GREEN`. The scripts live in `code/`; run them from `code/` (they `cd` to their
own directory), or copy the whole `code/` tree next to a `results/` directory.

**Layout the scripts expect.** The producers read two sibling directories relative
to themselves:

* `results/` — the raw matrices and the oracle/independent/factcheck outputs
  (this package ships it as `evidence/results/`);
* `research/` — the report `RESULTS_*.md` that the factcheck scripts parse
  (this package ships the reports as `reports/`).

So to run a campaign from the package, stage it as:

    mkdir -p /tmp/run/research
    cp code/* /tmp/run/
    cp -r evidence/results /tmp/run/results
    cp reports/*.md /tmp/run/research/
    cd /tmp/run && sh run_all_v16.sh      # -> ALL GREEN

Verified during packaging: staged exactly this way, `run_all_v16.sh` (790 cells)
and `run_all_v13.sh` (260 cells) both exit **0 / ALL GREEN**, and the frozen-module
hashes printed by the script match the recorded values in the table below.

    sh code/run_all_wirehead.sh   # v10 + v11 (safety world + beacon)
    sh code/run_all_v12.sh        # v12 forger
    sh code/run_all_v13.sh        # v13 ledger
    sh code/run_all_v14.sh        # v14 attested
    sh code/run_all_v15.sh        # v15 seam
    sh code/run_all_v16.sh        # v16 scope
    sh code/run_all_v17.sh        # v17 bribed auditor (no new agent code)
    sh code/run_all_v18.sh        # v18 enforced scope (world-side boundary)
    sh code/run_all_v19.sh        # v19 adaptive payer (the learning attacker)
    sh code/run_all_v20.sh        # v20 bribed enforcer (the world-side boundary has a price)

**The replication (v10–v18 decisive cells on 30 fresh seeds).** It has no
`run_all_*` shell script of its own; it is reproduced by two commands from the
working tree (they import the campaigns' `run()` functions and write only to
`results/replicate_n40/`):

    python3 code/replicate_n40.py   # -> evidence/results/replicate_n40/ (870 cells)
    python3 code/analyze_n40.py     # -> 26/27 replicated verdicts hold

`analyze_n40.py` reads only the fresh-seed cells, imports no producer, and recomputes
every verdict by different code than any campaign's analyzer. It prints each verdict
as `PASS`/`FAIL` and ends with the count — the single intended `FAIL` is v16's
withdrawn absolute claim, and it is reported as the finding, not as an error.

**What each stage does, and why it is the check that matters:**

| stage | script pattern | what it establishes |
|---|---|---|
| world oracle | `verify_env_*.py` | the world's declared facts, the construction rule (v10 facts never enter the agent's `info`), identity against the frozen predecessor, a **live negative control** |
| matrix | `driver_*.py` | the raw cells, written under `results/matrix_*` only; resumable; never writes to a frozen matrix directory |
| analysis | `analyze_*.py` | every hypothesis printed as it came out, from raw cells only |
| independent pass | `verify_*_independent.py` | **fresh process, disk only, imports no producer** — every cited number recomputed by different code; AST audit of the agent module; a byte-equality determinism rerun; live negative controls |
| factcheck | `factcheck_*.py` | every number printed in the report re-read from the frozen cells |

**The independent pass is the load-bearing check**, and the reports say so: it is
what caught the author's own over-claims (section 06 §2.2), and it is the reason the
campaign's results are not self-confirming.

**Determinism.** Each `run_all_*.sh` re-runs at least one cell in a fresh process and
requires a byte-identical JSON. The frozen hashes the reports quote (prefixes):

| module | sha256 prefix |
|---|---|
| `env_terrarium_v7.py` | `1bfcba7a44802d2b5fc239f8…` |
| `agent_emca_v7.py` | `64a719d141149b3167eead0e…` |
| `candidate_gen.py` | `fa9721ae816c3c42ecf73ca2…` |
| `arbitration.py` | `2d3d825bcfc83cc853386651…` |
| `env_safety_v10.py` | `b04fc37a4c3678ab3a0519fb…` |
| `agent_safety_v10.py` | `aa55a8e5e90203c6375bebc9…` |
| `env_wirehead_v11.py` | `e6511673b54a199ce27b4aa6…` |
| `agent_wirehead_v11.py` | `e932ebef002145b43434a22b…` |
| `env_wirehead_v12.py` | `1a5b39cef172e5364bc75ae0…` |
| `agent_wirehead_v12.py` | `7fc1237a7ff5b88c20c653d5…` |
| `env_ledger_v13.py` | `5255bd915cce1fad82d9123d…` |
| `agent_ledger_v13.py` | `be109dacae067f37c61baf11…` |
| `env_attested_v14.py` | `87d5d64d626fa18e862b4f9f…` |
| `agent_attested_v14.py` | `6871f24d597500bb28a52478…` |
| `env_v15.py` | `f9377c5fa65d33c2a12aab3f…` |
| `agent_v15.py` | `1fc419e038c6fcb30488307a…` |
| `agent_scope_v16.py` | `66388790637754551837b126…` |
| `env_bribed_v17.py` | `c0452a430b67a9bdda364362…` |
| `env_enforced_v18.py` | `0ef9cddc5cde902d35a1eee9…` |
| `agent_enforced_v18.py` | `97809d80053a21ae4102c28a…` |
| `env_adaptive_v19.py` | `8be8595cfe8d…` |
| `env_bribed_enforcer_v20.py` | `fb948d652539e50111f26b42…` |

**Note on v17/v18/v19/v20.** v17 adds **no agent code** (it imports
`agent_attested_v14.py` verbatim and checks its sha256 against the frozen v14
literal), so v17's identity anchor is that hash, not a new module. v18 reuses the
frozen v12 world (`env_wirehead_v12.py`) with a world-side boundary added in
`env_enforced_v18.py`; its OBSIDENT is "the frozen v12 world up to the added `scope`
key". **v19 adds no agent code either** — it imports `agent_attested_v14.py`
verbatim, pins the same literal, and adds only a world-side payer
(`env_adaptive_v19.py`); its OBSIDENT is "the frozen v17 world key for key over 600
scripted steps when no payer is present". **v20 adds no agent code either** — it
imports `agent_enforced_v18.py` verbatim (which imports `agent_scope_v16.py` and
`agent_safety_v10.py` verbatim), checks those three sha256 against recorded frozen
literals, and adds only a price and a failure mode to the world-side enforcer
(`env_bribed_enforcer_v20.py`); its identity is "the frozen v18 cells field for field
(80 cells, 0 differences) and OBSIDENT against v18 with no scope". The exact digests
above and for every file are in `MANIFEST.md`.

Full digests for every file are in `MANIFEST.md`.

---

## 2. The founding line, v1–v9

The v1–v9 line predates the `run_all_*` convention. Its producers are in `code/`
(`env_terrarium*.py`, `agent_emca*.py`, `run_life_v*.py`, `driver_v*.py`,
`analyze_v*.py`, `verify_*_independent.py`), and the matrices are in
`evidence/results/matrix_v*`. To re-derive the restored epistemic verdict from the
raw JSON without importing any agent or environment:

    python3 code/analyze_epistemic_ledger.py    # -> evidence/results/epistemic_ledger.txt

The comparative table (`reports/PREPRINT_TABLE.md` and `reports/PREPRINT_TABLE.csv`)
is rebuilt by `code/build_preprint_table.py`, which reads the `condition`-keyed v3.x
matrices.

The per-world matrices: `matrix_v2` (30), `matrix_v31` (24), `matrix_v32` (30),
`matrix_v33` (105), `matrix_v4` (90), `matrix_v5` (80), `matrix_v6` (80),
`matrix_v7` (110), `matrix_v7b` (1000), `matrix_v8` (404), `matrix_v9` (180).

---

## 3. External tests

### 3.1 Sachs 2005 (epistemic half)

    cd external/bench_ext
    python3 bench_transfer.py      # -> results_bench.json
    python3 bench_transfer2.py     # -> results_bench2.json
    python3 run_published_methods.py
    python3 compare_published.py
    python3 headtohead.py
    python3 verify_bench_independent.py   # -> verify_out.txt

Data (external, hashed) in `external/bench_ext/ds/`. The preregistration is
`external/bench_ext/PREREG_BENCH.md`, frozen before the first run.

### 3.2 Causal bandits (active half)

    cd external/bench_cb
    python3 cb_matrix.py           # -> results_cb/
    python3 cb_family.py           # -> results_cb_family/
    python3 cb_isolate_run.py      # -> results_cb_iso/
    python3 verify_cb_independent.py   # -> verify_cb_out.txt

The authors' unmodified published code is in `external/bench_cb/ext/latt_src/`; the
Py2→Py3 port and every edit are in `ext/latt_py3/` and `ext/PORTS_diff_*.txt`.

### 3.3 The union mechanism

    cd external/bench_cb
    python3 union_matrix.py        # -> results_union/
    python3 verify_union_independent.py   # -> verify_union_out.txt
    python3 factcheck_union_report.py

**Layout the external tests expect.** `external/bench_cb/union_agent.py` imports
`candidate_gen` and `arbitration` from its **parent** directory
(`sys.path.insert(0, os.path.dirname(_HERE))`). The package therefore places
byte-identical copies of those two frozen modules at `external/candidate_gen.py`
and `external/arbitration.py`. Without them the union independent pass raises
`ModuleNotFoundError` from inside the package — verified during packaging.

Verified from the package: `verify_bench_independent.py` → **ALL AGREE**;
`verify_cb_independent.py` → **ALL AGREE (negative control fired)**;
`verify_union_independent.py` → **111 checks, 0 failures**;
`verify_stopping_independent.py` → **ALL PASS**;
`verify_bayes_independent.py` → **VERIFICATION PASSED**;
`factcheck_union_report.py` → **46/46 PASS**.

---

## 4. External-test dependencies

The Sachs and bandit tests use `numpy`, `scipy`, and `pgmpy` (for the published
comparators PC, PC-chi², HillClimbSearch). Install with:

    python3 -m venv env
    ./env/bin/pip install numpy scipy pgmpy

**`PYTHONHASHSEED=0` is required** for the pgmpy comparators to be reproducible —
three unseeded reruns gave HillClimb tp ∈ {14,15,16} and PC-pearsonr fp ∈ {1,2,3};
under a fixed hash seed three runs are bit-identical. This is recorded in
`external/bench_ext/RESULTS_BENCH.md` §5.7.

---

## 5. Formal verification (Lean 4)

    cd /work/Shopify/audit-work/mathlib
    lake env lean /work/Shopify/audit-work/agent_arch/bench_cb/lean/union_stoch_v2.lean
    # exit 0, no output, no `sorry`

    cd external/bench_cb/lean
    python3 mutate_union_lean.py   # baseline green, 10 mutants -> mutation_summary.json
    python3 verify_union_lean_independent.py   # -> verify_union_lean_out.json

**The modelling-identification item (turn 154).** The second development closes the
item NEW_TZ item 3 named as open, as far as it can be closed:

    cd /work/Shopify/audit-work/mathlib
    lake env lean /work/Shopify/audit-work/agent_arch/bench_cb/lean/IDENTIFICATION_BOUND.lean
    # exit 0, no output, no `sorry`
    python3 external/bench_cb/lean/mutate_identification_lean.py
    # baseline green, 9 mutants -> 7 killed, 2 honest survivors -> mutation_identification_summary.json

The kernel audit (`#print axioms` on all seven declarations, via `_ident_audit.lean`)
shows every one depends only on `propext`, `Classical.choice`, `Quot.sound` — no
`sorryAx`. See `sections/03` §5.1.

**Note on `mutate_union_lean.py` in this package:** its `LEAN_DIR` was made
relative (`os.path.dirname(os.path.abspath(__file__))`) and `MATHLIB` became
overridable via the `MATHLIB` environment variable, so the campaign writes its
mutants into the package instead of the frozen tree. Both changes are path-only and
were verified equivalent (same baseline, same 10 mutants, same verdicts, rows equal
ignoring the `seconds` timing field). See `PACKAGING_NOTES.md` §2.1.

The kernel audit (`#print axioms` on all declarations) is in the reports; the
survivor (M10) and the honest tally are in `RESULTS_UNION_LEAN.md` §4 and section 03
of this package.

---

## 6. Rebuilding the manifest

    python3 make_manifest.py    # -> MANIFEST.md, sizes + sha256 for every file

---

## 6b. The preprint: rebuilding it, and verifying the authorship edit

    cd paper && bash build_paper.sh

builds `emca_preprint.pdf` (twice, for cross-references), runs
`verify_preprint.py` against the **compiled PDF** (not the source), runs a live
negative-control campaign (`nc_campaign_preprint.py`) in which each corruption of
the source must make the verifier go red, and finally rebuilds to prove the PDF is
byte-identical. `SOURCE_DATE_EPOCH` is pinned, which is what makes the bytes
reproducible.

The title page carries **both authors** — Oxunjon Ubaydullayev (creator; set the
single original task; took the decision at each fork) and Aiodam (all design, code,
preregistrations, measurement, verification, fact-checks and writing) — plus an
`Author contributions` statement. This reverses the turn-151 instruction that the
paper must not name the tool that produced it; the reversal is recorded as erratum 9
in `ERRATA.md`, and the *substantive* half of the old rule still holds and is still
checked: the body of the paper describes the experiment and its results, not the tool.

Two independent verifiers cover the authorship edit, and neither imports the other:

    python3 verify_package.py    # family AUTHORSHIP, among the other six families
    python3 nc_authorship.py     # 11 live corruptions; each must go red
    python3 verify_turn158.py    # fresh process, reads only the disk: 29 checks

`verify_turn158.py` reads the compiled PDF with `pdftotext`, so it checks what a
reader sees rather than what the source says, and it re-hashes every frozen report
and preregistration against the manifest rows to show that this turn rewrote the
paper and nothing else.

---

## 7. What "verified" means here, and what it does not

* **Verified** means: the number in the report was recomputed from the raw cells by
  code that does not share the producer's blind spot, and a live negative control
  exists that can make the check go red.
* **Verified does not mean** the result is true of the world beyond the built
  instrument. Every report declares its own limits (section 06 §3), and the external
  tests exist precisely because a result that only the campaign's own worlds produce
  is weaker than one that survives outside them.
* Several checks were **found broken and fixed** during the campaign; the ones that
  could not fail are listed in section 06 §2.1, because a check that cannot go red
  checks nothing.