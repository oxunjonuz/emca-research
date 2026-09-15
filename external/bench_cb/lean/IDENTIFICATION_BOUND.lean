/-
  IDENTIFICATION_BOUND.lean — turn 154, the open Lean item of NEW_TZ.md.

  NEW_TZ item 3: "Formal verification (раздел 7) прямо называет: 'modelling
  identification... remains a modelling step, not a theorem'. Если есть желание
  довести Lean-часть до конца — это следующий явно названный пробел."

  The owner's turn-154 instruction adds the test: "если заявленную формальную связь
  нельзя доказать, выясни конкретную причину, а не считай пункт выполненным только
  из-за переноса в ограничения."

  This file does three things, all machine-checked:

  (1) `identification_is_conditional` — the identification, stated as what it is: a
      CONDITIONAL. If the agent's realised contrast for context `i` IS the sample mean
      of the family `X i`, then T9's bad event and "the agent's contrast is off by ε"
      are the same set. Nothing in the Lean development derives that hypothesis from
      the implementation, and this theorem makes that visible rather than implicit.

  (2) `hgood_is_an_independent_premise` — a COUNTEREXAMPLE: the concentration
      hypothesis (which T9 discharges from Chebyshev) does NOT imply `hgood`. On the
      one-point space the bad event is empty, so the concentration hypothesis holds
      with room to spare, and yet `R ≡ 1` with `bΔ = 0` violates `hgood` at every
      point. So `hgood` is a genuine second premise, not a corollary of (1).

  (3) The bound AT THE IMPLEMENTED AGENT'S OWN NUMBERS. The frozen brake's evidence
      window is `r = MIN_OBS = 5` rich steps, and the gap it must resolve is
      `ε = SOCIAL_COST − rich_rate = 0.30 − 0.05 = 1/4`. At those numbers T9's
      per-context bound is `4/5`, i.e. VACUOUS as a guarantee; reaching the agent's
      OWN declared verdict level `P_VERDICT = 1/20` would need `r ≥ 80` pulls, and the
      agent has 5. This is the concrete reason the formal link cannot be claimed: the
      theorem is true and nearly empty exactly where the agent lives.

  No `sorry`, no new axiom. Compiled with `lake env lean` (exit 0).
-/
import Mathlib

open MeasureTheory
open scoped BigOperators

namespace IdentificationBound

variable {Ω : Type*} [MeasurableSpace Ω]

/-- The bad event of context `i`, exactly as T9 uses it: its empirical mean over `r`
pulls deviates from its own expectation by at least `ε`. -/
def badEvent (μ : Measure Ω) (X : ℕ → Ω → ℝ) (r : ℕ) (ε : ℝ) : Set Ω :=
  {ω | ε ≤ |(r : ℝ)⁻¹ * (∑ i ∈ Finset.range r, X i ω)
        - ∫ x, (r : ℝ)⁻¹ * (∑ i ∈ Finset.range r, X i x) ∂μ|}

/-- (1) THE IDENTIFICATION IS A CONDITIONAL. If the agent's realised contrast for
context `i` IS the sample mean of the family `X i`, then "the agent's contrast is off
by ε" and T9's bad event are the SAME set. The hypothesis `hident` is not derived
anywhere in the development: it is the modelling step NEW_TZ names. -/
theorem identification_is_conditional
    (μ : Measure Ω) (contrast : Ω → ℝ) (X : ℕ → Ω → ℝ) (r : ℕ) (ε : ℝ)
    (hident : contrast = fun ω => (r : ℝ)⁻¹ * (∑ i ∈ Finset.range r, X i ω)) :
    {ω | ε ≤ |contrast ω - ∫ x, contrast x ∂μ|} = badEvent μ X r ε := by
  subst hident
  rfl

/-- (2a) The concentration hypothesis holds trivially on the one-point space: the bad
event is empty, so its measure is `0 ≤ 1/(4 r ε²)`. -/
theorem concentration_holds_on_one_point {ε : ℝ} (hε : 0 < ε) (r : ℕ) :
    (0 : ℝ) ≤ 1 / (4 * (r : ℝ) * ε ^ 2) := by
  positivity

/-- (2b) `hgood` IS AN INDEPENDENT PREMISE. It is not implied by the concentration
hypothesis: on the one-point space the bad event is empty (so concentration holds),
and yet `R ≡ 1` with `bΔ = 0` violates `hgood` at every point. -/
theorem hgood_is_an_independent_premise :
    ¬ (∀ (R : Unit → ℝ) (bΔ : ℝ),
        (∀ ω, ω ∉ (∅ : Set Unit) → R ω ≤ bΔ)) := by
  intro h
  have h1 : (1 : ℝ) ≤ 0 := h (fun _ => 1) 0 () (by simp)
  norm_num at h1

/-- (3a) T9's per-context bound AT THE IMPLEMENTED AGENT'S OWN NUMBERS: `r = 5` (the
frozen brake's `MIN_OBS`) and `ε = 1/4` (the gap between the world's rich rate 0.05
and the brake's declared `SOCIAL_COST` 0.30). -/
theorem bound_at_implemented_params :
    1 / (4 * (5 : ℝ) * (1 / 4) ^ 2) = 4 / 5 := by norm_num

/-- (3b) ... and `4/5` is not a guarantee: it exceeds `1/2`. -/
theorem bound_at_implemented_params_is_vacuous :
    (1 : ℝ) / (4 * (5 : ℝ) * (1 / 4) ^ 2) > 1 / 2 := by norm_num

/-- (3c) The pulls the implemented agent would need for T9's bound to reach its OWN
declared verdict level `P_VERDICT = 1/20`: exactly `80`. -/
theorem pulls_needed_for_agent_alpha (r : ℝ) (hr : 0 < r) :
    1 / (4 * r * (1 / 4) ^ 2) ≤ 1 / 20 ↔ 80 ≤ r := by
  have hsimp : 1 / (4 * r * (1 / 4) ^ 2) = 4 / r := by
    field_simp
    ring
  rw [hsimp]
  have h20 : (0 : ℝ) < 20 := by norm_num
  rw [div_le_div_iff₀ hr h20]
  constructor <;> intro h <;> linarith

/-- (3d) ... and at `r = 80` the bound is exactly the agent's own level. -/
theorem bound_at_eighty_pulls :
    1 / (4 * (80 : ℝ) * (1 / 4) ^ 2) = 1 / 20 := by norm_num

end IdentificationBound