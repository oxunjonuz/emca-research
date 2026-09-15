/-
  m10_followup.lean — turn 131.  Why did the "loosened constant" mutant redden?

  The mutation changed T5b's conclusion from `≤ n/4` to `≤ n/2`, which is a
  WEAKER statement and should be provable.  It reddened.  Two possible reasons:

    (a) `n/2` is genuinely not derivable (my prediction was wrong about the math)
    (b) the calc block is pinned to `n/4` as its last step, so the goal `n/2` no
        longer matches the calc — an ARTEFACT of how the mutant was written, not
        a mathematical failure.

  This file decides between (a) and (b): it proves the n/2 statement by
  transitivity from the n/4 result.  If it compiles, the red was (b) — the
  mutant's calc pinning, not the logic.  Reporting it as "caught" would then be
  overclaiming.
-/

import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 800000

namespace M10Followup

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

lemma variance_sum_le_q [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ}
    (h_indep : iIndepFun X μ)
    (hmeas : ∀ i, AEStronglyMeasurable (X i) μ)
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1) :
    Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 4 := by
  have hml' : ∀ i ∈ Finset.range n, MemLp (X i) 2 μ :=
    fun i _ => memLp_of_bounded (h01 i) (hmeas i) 2
  rw [IndepFun.variance_sum hml' (fun i _ j _ hij => h_indep.indepFun hij)]
  calc ∑ i ∈ Finset.range n, Var[X i; μ]
      ≤ ∑ i ∈ Finset.range n, ((1 - 0) / 2) ^ 2 :=
        Finset.sum_le_sum fun i _ =>
          variance_le_sq_of_bounded (h01 i) (hmeas i).aemeasurable
    _ = (n : ℝ) / 4 := by
        simp only [Finset.sum_const, Finset.card_range, nsmul_eq_mul]
        ring

/-- The LOOSENED constant, proved by transitivity — no calc pinning.  If this
compiles, the M10 red was an artefact of the mutant's `calc`, not the logic. -/
lemma variance_sum_le_half [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ}
    (h_indep : iIndepFun X μ)
    (hmeas : ∀ i, AEStronglyMeasurable (X i) μ)
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1) :
    Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 2 :=
  (variance_sum_le_q h_indep hmeas h01).trans (by
    have : (0:ℝ) ≤ (n:ℝ) := by positivity
    linarith)

end M10Followup
