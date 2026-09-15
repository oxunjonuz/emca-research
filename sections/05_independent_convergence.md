# Section 05 — Independent convergence: NVIDIA / Rutgers (Che & Wu, 2026)

*The owner asked for "явная, точная ссылка на независимую конвергенцию с работой
NVIDIA/Rutgers (Che & Wu, 2026) — это подтверждает результат, а не обесценивает
его." This section records that convergence and the exact status of the citation,
including what I could and could not verify.*

---

## 0. Status of the citation — RESOLVED (turn 151, owner-supplied arXiv id)

**The citation was supplied by the owner in the directive for this packaging turn.**
It does not appear anywhere in the campaign's own frozen artefacts: a search of the
whole working tree for `NVIDIA`, `Rutgers`, `Che & Wu`, `Che and Wu` returns **no
match** in any report, preregistration, source registration, or matrix. There is no
`src_*` registration for it, unlike every other external source the campaign cites.

**I tried to locate it independently and could not** (arXiv full-text and author
searches, OpenAlex author and institution searches, Crossref, several web engines —
all recorded below). **The owner then supplied the arXiv id directly:
`arXiv:2606.16914`.** It is now verified and registered:

| field | value |
|---|---|
| id | **`src_8e770ff6f1a7`** |
| URL | `https://arxiv.org/abs/2606.16914` |
| sha256 | `4d108ad8986ed39e2c395ea7f84e58ab08b3e79ed1c495742f96bde5e67e6498` |
| bytes | 40234 |
| title | *Greed Is Learned: Visible Incentives as Reward-Hacking Triggers* |
| authors | Tong Che, Rui Wu |
| submitted | 15 June 2026 |
| pinned quoted fragment | "chases the displayed payoff across held-out domains, sacrifices the true task to do so, and follows the channel wherever we rewrite it" |

The registered fragment is verified present in the fetched bytes, so this citation now
follows the same discipline as every other source in the package. The earlier failure
to find it is kept below rather than deleted, because the failure is part of the
record.

### 0.1 The search attempts that failed (kept verbatim)

* arXiv full-text/author search for `Che Wu agent safety environment` → **no
  results**;
* arXiv search `"Che" "Wu" safety agent` → **no results**;
* arXiv search `"Rutgers" "NVIDIA" agent` → **no results**;
* arXiv search `"NVIDIA" "Rutgers"` (all fields) → **no results**;
* OpenAlex author search `Che Wu` → 349 authors, none matching an agent-safety
  NVIDIA/Rutgers paper;
* OpenAlex works filtered to a Rutgers institution id with `agent safety
  environment architecture` from 2026 → **0 results**;
* Crossref query `agent safety environment architecture` from 2026 → the nearest
  items are unrelated (a Google "circuit breaker" architecture paper, several
  multi-agent governance SSRN preprints), none by Che & Wu;
* DuckDuckGo, Bing, Brave, Startpage, Ecosia, Google Scholar → blocked, captcha, or
  no matching result.

**Why the search failed, in hindsight:** the search terms were built from the
*convergence target* (agent safety, environment architecture, Rutgers, NVIDIA), not
from the paper's own vocabulary. The paper's title and abstract use none of those
words — it is about *reward-channel addiction*, *visible incentives* and
*MoneyWorld*. The lesson is the same one the campaign keeps re-learning: a search
keyed on your own framing of the result will not find the result stated in someone
else's framing.

I record the failure plainly rather than dressing the section up, because inventing
a plausible-looking reference would be exactly the failure this campaign spent
sixteen versions measuring.

---

## 1. What the convergence is, as the owner framed it

The owner's framing: a 2026 paper by **Che & Wu** (NVIDIA / Rutgers) independently
reaches the campaign's central conclusion — that **protection lives in the
architecture of the environment, not in the architecture of the agent** — and this
**confirms** the result rather than devaluing it.

**Important caveat added in turn 151.** The convergence target as phrased above is
the form the campaign **withdrew in its own errata** (see `../ERRATA.md` §1): v16
does not prove that protection lives in the environment, and an internal hard rule
held in every cell measured (170/170). So if the Che & Wu work is stated that way,
the convergence is at the level of the *direction* — "the environment does much of
the work" — and **not** at the level of the campaign's withdrawn strong claim. The
campaign's defensible convergence point is the **capability/boundary** result from
v16: what bounds a specific harm is whether the harmful capability is inside the
agent's scope at all, and scope protection is a **capability fact, not a policy
fact**.

The convergence is with the campaign's v16 finding in particular
(`../reports/RESULTS_SCOPE_V16.md`, section 04 §7 of this package):

> **Scope protection is exactly "the harm is outside the scope".** Inside the scope,
> narrowing buys nothing and does not raise the bribe price. The protection is a
> **capability fact, not a policy fact** — which is why OWASP's own load-bearing
> mitigation is "complete mediation" (authorization downstream, not in the model).

And it is consistent with the whole v10–v16 arc's one-line conclusion (section 04
§8): six instruments tried to protect the agent from itself, and each one closed a
channel and moved the vulnerability to the next one — the price, the label, the
timing, the criterion. What actually bounds the harm is a property of the
**environment**, not of the agent.

---

## 2. Why a convergence is a confirmation and not a devaluation

The owner's own point, and it is correct: an independent group reaching the same
structural conclusion from a different direction **raises** the confidence in the
result — it is exactly the kind of independent check this campaign requires of
itself ("never trust even your own result until it survives a check that does not
share its blind spot"). A result that only the campaign's own worlds produce is
weaker than one that a separate group, with separate instruments, also reaches.

This is the same logic the campaign applied to its own prior-art findings in section
02 — with the opposite sign there, because those papers showed the campaign's
*central insight* was already published. The distinction matters and is worth
stating: in section 02 the prior art **reduced** the novelty claim; here the
convergence **supports** the safety-line conclusion. Both are reported as they are.

**What the convergence says about minimal worlds (added turn 157, owner directive
`op_3645deda2339`).** Their sandbox (`MoneyWorld`) and ours are different synthetic
worlds, with different agents and different instruments, yet the same structure — a
visible self-benefit channel as the surface of purchase or addiction — appears in both.
That the phenomenon is visible already in minimal, fully controlled worlds is evidence
that it is **fundamental**, not an artefact of scale, and it makes the minimal world a
methodological **advantage** rather than a weakness: it lets the boundary of each
defence be measured cheaply, quickly and exactly, and it lets the campaign's own
instrumentation errors be caught and reported. This is stated with its bound: it is two
synthetic sandboxes, not a claim about deployed systems, and it does not by itself
establish that the same boundaries hold for a large-scale agent with a rich observation
space — that transfer remains untested and is named as such in section 06.

---

## 3. The honest boundary of this section

1. **The citation is now verified and registered** (`src_8e770ff6f1a7`, arXiv:2606.16914,
   sha256 `4d108ad8986e…`, pinned quoted fragment present in the fetched bytes). It
   was owner-supplied after my own searches failed, and the failure is recorded in
   §0.1.
2. **No campaign result depends on it.** The v10–v16 findings stand on their own
   frozen matrices and independent passes; the convergence is corroboration, not
   support.
3. **The convergence is at the level of the structural conclusion**, not at the
   level of any specific number. The campaign's specific measurements (0.25 per unit
   of harm, the 14-step attestation cliff, a0_share 0.250, 2/12 bribe channels) are
   the campaign's own and are not attributed to the other work.
4. **Priority is not claimed in either direction.** Their preprint was submitted
   15 June 2026; the safety line ran in September 2026. The convergence is
   **structural, not causal** — two independent lines arrived at the same shape, and
   the campaign's results were obtained before any acquaintance with that work.

---

## 4. Artefacts for this section

* The convergence target: `../reports/RESULTS_SCOPE_V16.md` §5 ("The protection is a
  capability fact, not a policy fact"), and section 04 §7–§8 of this package.
* The industry framing that the campaign measured against, and that the convergence
  would sit beside: OWASP LLM06:2025 Excessive Agency (`src_307866a98e28`), CISA
  ZeroTrust Maturity Model (`src_4bd66def286a`), Microsoft agent orchestration
  patterns (`src_fafbcca00be3`), Anthropic building-effective-agents
  (`src_633ae8c0ac01`) — all four registered and quoted in
  `../preregistrations/PREREG_SCOPE_V16.md` §1.
* **Registered:** the Che & Wu (2026) reference — `src_8e770ff6f1a7`,
  arXiv:2606.16914, verified and pinned this turn.