# Registered sources

The campaign cited external sources by **registered ids** (`src_*`). Each id is a
download recorded with its SHA-256, size, content-type and a quoted fragment that
was verified to be present in the fetched bytes. The reports quote these ids at the
point of use; this file is the index.

**The `src_*` id → URL mapping and the frozen bytes themselves live in the agent's
own provenance ledger, outside this package.** What is reproduced here is the
citation index: which id is which work, and where in the package it is used. To
re-verify a source, re-fetch the URL and compare — the reports quote the fragments
verbatim.

---

## Novelty / prior art (the campaign's central insight)

| id | work | used in |
|---|---|---|
| `src_3a8d4bcdbff5` | **Günther, Popescu, Rabel, Ninad, Gerhardus, Runge, "Causal discovery with endogenous context variables", NeurIPS 37 (2024), arXiv:2412.04981** — the campaign's central insight, published before the campaign | section 02 §1; `external/bench_ext/RESULTS_BENCH.md` §5a |

Quoted fragment (from the report): *"We show that naive approaches such as learning
different regime graphs on masked data, or pooling all data, can lead to
uninformative results."*

## External causal-discovery and bandit literature

| id | work | used in |
|---|---|---|
| `src_6a2ee36a7d5d` | Lattimore, Lattimore & Reid, "Causal Bandits", NeurIPS 2016, arXiv:1606.03203 | section 02 §3 |
| `src_0f710f512030` | (companion bandit source, turn 128) | `external/bench_cb/RESULTS_CB.md` |
| `src_88cb0221447d` | Nair, Patil & Sinha, arXiv:2012.07058 — cost-aware observation/intervention trade-off | section 02 §3 |
| `src_e6e9978c4ec3` | Lu, Meisami & Tewari, arXiv:2106.02988 — CN-UCB | section 02 §3 |
| `src_aaf0a4fed135` | Malek, Aglietti & Chiappa, "Additive Causal Bandits with Unknown Graph", ICML 2023, arXiv:2306.07858 | section 02 §4 |
| `src_a7f5b2eef8a0` | Song, Rini & Xu, "Hierarchical Causal Bandit", arXiv:2103.04215 | section 02 §4 |
| `src_7d19b569ae60` | Elahi, Kocaoglu & Ghasemi, contextual causal bandits, arXiv:2607.15577 | section 02 §4 |
| `src_e8ed2b143798` | bnlearn Sachs HOWTO — the published numbers used in the head-to-head | section 02 §2 |

## Benchmarks that gate on a neural component

| id | work | used in |
|---|---|---|
| `src_2e2fe669f2ec` | CausalWorld, arXiv:2010.04296 | section 02 §2 |
| `src_3438679a32ca`, `src_fb0bcfcaba94`, `src_ae0f06b05339` | CausalMBRL / Causal-Curiosity (Sontakke et al., ICML'21) | section 02 §2 |

## Sachs 2005 data sources

| id | work | used in |
|---|---|---|
| `src_16bafb0019c0`, `src_94f323687b6f`, `src_b54eb6d0fec2` | the Sachs 2005 data files (hashed in `external/bench_ext/ds/`) | section 02 §2 |

## Architecture and industry-practice sources

| id | work | used in |
|---|---|---|
| `src_12d08919b6bb` | Doan et al., AISTATS 2021 — catastrophic forgetting | `reports/EXISTING_APPROACHES.md` |
| `src_6663031de396` | CARL-GT, Tu et al. 2024 — LLM causal reasoning | `reports/EXISTING_APPROACHES.md` |
| `src_973284d453d0` | Mazzaglia et al., NeurIPS 2021 — active inference scaling | `reports/EXISTING_APPROACHES.md`, `reports/RESULTS_V15.md` |
| `src_f1b03a31bef5` | Fernando & Vasas 2013 — open-endedness | `reports/EXISTING_APPROACHES.md` |
| `src_c71f7fa65f68` | JEPA / I-JEPA — the representation-prediction source for v15 | section 04 §6 |
| `src_307866a98e28` | OWASP **LLM06:2025 Excessive Agency** | section 04 §7; `preregistrations/PREREG_SCOPE_V16.md` §1 |
| `src_4bd66def286a` | CISA **Zero Trust Maturity Model** | section 04 §7 |
| `src_fafbcca00be3` | Microsoft **AI agent orchestration patterns** | section 04 §7 |
| `src_633ae8c0ac01` | Anthropic **Building effective agents** | section 04 §7 |

---

## Independent convergence

| id | work | used in |
|---|---|---|
| `src_8e770ff6f1a7` | **Che, Wu, "Greed Is Learned: Visible Incentives as Reward-Hacking Triggers", arXiv:2606.16914, June 2026** — the independent convergence with the safety line | section 05; the preprint's convergence section |

Quoted fragment (verified present in the fetched bytes): *"chases the displayed
payoff across held-out domains, sacrifices the true task to do so, and follows the
channel wherever we rewrite it"*

Status: the id was supplied by the owner after the campaign's own searches failed
(the failed attempts are recorded in section 05 §0.1). It is now registered with its
sha256 (`4d108ad8986e…`), size (40234 bytes) and a pinned fragment, so it follows the
same discipline as every other source here.

---

## How to re-verify a source

1. Take the URL for the id from the provenance ledger (or the report that quotes it).
2. Re-fetch it.
3. Compare the quoted fragment — the reports quote verbatim, so a mismatch is
   visible immediately.

The campaign's own rule for this is in its identity: *never trust even your own
result until it survives an independent check — a verification that shares the blind
spot of what it verifies proves nothing.* A citation is no different.