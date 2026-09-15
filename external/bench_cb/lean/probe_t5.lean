import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 4000000

namespace Probe

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

/-- (T5-step) Variance of a sum of independent `[0,1]` variables is at most `n/4`. -/
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

/-- (T5) Chebyshev + Popoviciu for `[0,1]` independent samples: the empirical mean
deviates from its expectation by `ε` with probability at most `1/(4 n ε²)`.
Fully closed from Mathlib lemmas; no missing bridge is used. -/
theorem chebyshev_sample_mean [IsProbabilityMeasure μ]
    {X : ℕ → Ω → ℝ} (h_indep : iIndepFun X μ)
    (hmeas : ∀ i, AEStronglyMeasurable (X i) μ)
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1)
    {n : ℕ} (hn : 0 < n) {ε : ℝ} (hε : 0 < ε) :
    μ.real {ω | ε ≤ |(∑ i ∈ Finset.range n, X i ω
                        - ∫ x, (∑ i ∈ Finset.range n, X i x) ∂μ)| / n}
      ≤ 1 / (4 * (n : ℝ) * ε ^ 2) := by
  have hnR : (0 : ℝ) < (n : ℝ) := by exact_mod_cast hn
  have hml : MemLp (fun ω => ∑ i ∈ Finset.range n, X i ω) 2 μ :=
    memLp_finset_sum _ fun i _ => memLp_of_bounded (h01 i) (hmeas i) 2
  have hvar : Var[fun ω => ∑ i ∈ Finset.range n, X i ω; μ] ≤ (n : ℝ) / 4 :=
    variance_sum_le h_indep hmeas h01
  have hc : (0 : ℝ) < (n : ℝ) * ε := by positivity
  have hcheb := meas_ge_le_variance_div_sq hml hc
  have hset : {ω | ε ≤ |(∑ i ∈ Finset.range n, X i ω
                        - ∫ x, (∑ i ∈ Finset.range n, X i x) ∂μ)| / n}
      = {ω | (n : ℝ) * ε ≤ |(∑ i ∈ Finset.range n, X i ω
                        - ∫ x, (∑ i ∈ Finset.range n, X i x) ∂μ)|} := by
    ext ω
    simp only [Set.mem_setOf_eq]
    rw [le_div_iff₀ hnR]
    constructor <;> intro h <;> linarith
  rw [hset, measureReal_def]
  refine (ENNReal.toReal_mono (by finiteness) hcheb).trans ?_
  rw [ENNReal.toReal_ofReal (by positivity)]
  calc Var[fun ω => ∑ i ∈ Finset.range n, X i ω; μ] / ((n : ℝ) * ε) ^ 2
      ≤ ((n : ℝ) / 4) / ((n : ℝ) * ε) ^ 2 :=
        div_le_div_of_nonneg_right hvar (by positivity)
    _ = 1 / (4 * (n : ℝ) * ε ^ 2) := by
        field_simp
        ring

end Probe