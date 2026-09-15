import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 800000

namespace Union

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

/-- Empirical mean of the first `n` samples; a definition keeps statement
elaboration cheap (an inline `∫` in a `setOf` blows the heartbeat budget). -/
noncomputable def sampleMean (X : ℕ → Ω → ℝ) (n : ℕ) : Ω → ℝ :=
  fun ω => (n : ℝ)⁻¹ * ∑ i ∈ Finset.range n, X i ω

/-- Chebyshev in real-measure form with an explicit variance bound. -/
lemma chebyshev_abs [IsFiniteMeasure μ] {Y : Ω → ℝ} (hY : MemLp Y 2 μ) {σ2 c : ℝ}
    (hc : 0 < c) (hvar : Var[Y; μ] ≤ σ2) :
    μ.real {ω | c ≤ |Y ω - ∫ x, Y x ∂μ|} ≤ σ2 / c ^ 2 := by
  rw [measureReal_def]
  refine (ENNReal.toReal_mono (by finiteness) (meas_ge_le_variance_div_sq hY hc)).trans ?_
  rw [ENNReal.toReal_ofReal (div_nonneg (variance_nonneg Y μ) (sq_nonneg c))]
  exact div_le_div_of_nonneg_right hvar (sq_nonneg c)

/-- Variance of a sum of independent `[0,1]` variables is at most `n/4`. -/
lemma variance_sum_le [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ}
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

/-- Variance of the empirical mean is the sum's variance divided by `n²`. -/
lemma variance_mean_le [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ} (hn : 0 < n)
    (h : Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 4) :
    Var[sampleMean X n; μ] ≤ 1 / (4 * (n : ℝ)) := by
  have hv : Var[sampleMean X n; μ]
      = ((n : ℝ))⁻¹ ^ 2 * Var[∑ i ∈ Finset.range n, X i; μ] := by
    have hsm := variance_smul (μ := μ) (((n : ℝ))⁻¹)
      (∑ i ∈ Finset.range n, X i)
    simpa [sampleMean, Pi.smul_apply, Finset.sum_apply] using hsm
  rw [hv]
  calc ((n : ℝ))⁻¹ ^ 2 * Var[∑ i ∈ Finset.range n, X i; μ]
      ≤ ((n : ℝ))⁻¹ ^ 2 * ((n : ℝ) / 4) := mul_le_mul_of_nonneg_left h (sq_nonneg _)
    _ = 1 / (4 * (n : ℝ)) := by field_simp; ring

/-- `MemLp` of the empirical mean. -/
lemma memLp_sampleMean [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ}
    (hmeas : ∀ i, AEStronglyMeasurable (X i) μ)
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1) :
    MemLp (sampleMean X n) 2 μ := by
  have hml : MemLp (fun ω => ∑ i ∈ Finset.range n, X i ω) 2 μ :=
    memLp_finset_sum _ fun i _ => memLp_of_bounded (h01 i) (hmeas i) 2
  simpa [sampleMean] using hml.const_mul ((n : ℝ))⁻¹

/-- Chebyshev applied to the empirical mean. -/
lemma mean_concentration [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ} {ε : ℝ}
    (hε : 0 < ε)
    (hmlm : MemLp (sampleMean X n) 2 μ)
    (hvarMean : Var[sampleMean X n; μ] ≤ 1 / (4 * (n : ℝ))) :
    μ.real {ω | ε ≤ |sampleMean X n ω - ∫ x, sampleMean X n x ∂μ|}
      ≤ 1 / (4 * (n : ℝ) * ε ^ 2) := by
  have hcheb := chebyshev_abs hmlm (σ2 := 1 / (4 * (n : ℝ))) (c := ε) hε hvarMean
  exact hcheb.trans (le_of_eq (by field_simp))

/-- (T6) THE EMPIRICAL-MEAN CONCENTRATION, fully closed. -/
theorem chebyshev_sample_mean [IsProbabilityMeasure μ]
    {X : ℕ → Ω → ℝ} (h_indep : iIndepFun X μ)
    (hmeas : ∀ i, AEStronglyMeasurable (X i) μ)
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1)
    {n : ℕ} (hn : 0 < n) {ε : ℝ} (hε : 0 < ε) :
    μ.real {ω | ε ≤ |sampleMean X n ω - ∫ x, sampleMean X n x ∂μ|}
      ≤ 1 / (4 * (n : ℝ) * ε ^ 2) :=
  mean_concentration (X := X) (n := n) (ε := ε) hε
    (memLp_sampleMean (X := X) (n := n) hmeas h01)
    (variance_mean_le (X := X) (n := n) hn (variance_sum_le (X := X) (n := n) h_indep hmeas h01))

end Union
