import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 1000000

namespace Probe

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

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

end Probe