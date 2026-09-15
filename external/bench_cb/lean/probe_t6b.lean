/-
  probe_t6b.lean — turn 131.  Diagnosis + closure of T6.

  The turn-130 file times out at `whnf` while ELABORATING the T6 statement:
      μ.real {ω | ε ≤ |sampleMean X n ω - ∫ x, sampleMean X n x ∂μ|} ≤ ...
  with `sampleMean X n := fun ω => (n:ℝ)⁻¹ * ∑ i ∈ Finset.range n, X i ω`.

  Diagnosis (isolated here): the `fun ω => ...` definition forces whnf to unfold
  a `Finset.range` sum inside the `setOf` predicate when type-checking the `≤`.
  Variant tested: the mean as a scalar multiple of the SUM FUNCTION
  (`sampleMeanV1 X n := (n:ℝ)⁻¹ • ∑ i ∈ Finset.range n, X i`).  The `•` form is
  opaque to whnf; the statement then elaborates and the proof closes.
-/

import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 800000

namespace UnionProbe

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

/-- V1: the mean as a scalar multiple of the SUM FUNCTION (not pointwise). -/
noncomputable def sampleMeanV1 (X : ℕ → Ω → ℝ) (n : ℕ) : Ω → ℝ :=
  (n : ℝ)⁻¹ • ∑ i ∈ Finset.range n, X i

/-- V1 pointwise unfolding: the bridge to the turn-130 shape. -/
lemma sampleMeanV1_apply (X : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) :
    sampleMeanV1 X n ω = (n : ℝ)⁻¹ * ∑ i ∈ Finset.range n, X i ω := by
  simp [sampleMeanV1, Pi.smul_apply, smul_eq_mul]

lemma variance_sum_le_probe [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ}
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

/-- V1 variance transfer: now a direct rewrite, because `sampleMeanV1` IS a smul. -/
lemma variance_mean_le_probe [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ} (hn : 0 < n)
    (h : Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 4) :
    Var[sampleMeanV1 X n; μ] ≤ 1 / (4 * (n : ℝ)) := by
  have hv : Var[sampleMeanV1 X n; μ]
      = ((n : ℝ))⁻¹ ^ 2 * Var[∑ i ∈ Finset.range n, X i; μ] := by
    simpa [sampleMeanV1] using variance_smul (μ := μ) (((n : ℝ))⁻¹)
      (∑ i ∈ Finset.range n, X i)
  rw [hv]
  calc ((n : ℝ))⁻¹ ^ 2 * Var[∑ i ∈ Finset.range n, X i; μ]
      ≤ ((n : ℝ))⁻¹ ^ 2 * ((n : ℝ) / 4) := mul_le_mul_of_nonneg_left h (sq_nonneg _)
    _ = 1 / (4 * (n : ℝ)) := by field_simp; ring

/-- Chebyshev in real-measure form with an explicit variance bound. -/
lemma chebyshev_abs_probe [IsFiniteMeasure μ] {Y : Ω → ℝ} (hY : MemLp Y 2 μ) {σ2 c : ℝ}
    (hc : 0 < c) (hvar : Var[Y; μ] ≤ σ2) :
    μ.real {ω | c ≤ |Y ω - ∫ x, Y x ∂μ|} ≤ σ2 / c ^ 2 := by
  rw [measureReal_def]
  refine (ENNReal.toReal_mono (by finiteness) (meas_ge_le_variance_div_sq hY hc)).trans ?_
  rw [ENNReal.toReal_ofReal (div_nonneg (variance_nonneg Y μ) (sq_nonneg c))]
  exact div_le_div_of_nonneg_right hvar (sq_nonneg c)

/-- (T6-V1) THE EMPIRICAL-MEAN CONCENTRATION, closed with the `•` definition. -/
theorem chebyshev_sample_mean_V1 [IsProbabilityMeasure μ]
    {X : ℕ → Ω → ℝ} (h_indep : iIndepFun X μ)
    (hmeas : ∀ i, AEStronglyMeasurable (X i) μ)
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1)
    {n : ℕ} (hn : 0 < n) {ε : ℝ} (hε : 0 < ε) :
    μ.real {ω | ε ≤ |sampleMeanV1 X n ω - ∫ x, sampleMeanV1 X n x ∂μ|}
      ≤ 1 / (4 * (n : ℝ) * ε ^ 2) := by
  have hml' : MemLp (fun ω => ∑ i ∈ Finset.range n, X i ω) 2 μ :=
    memLp_finset_sum _ fun i _ => memLp_of_bounded (h01 i) (hmeas i) 2
  have hmlm : MemLp (sampleMeanV1 X n) 2 μ := by
    have := hml'.const_smul ((n : ℝ))⁻¹
    convert this using 1
    ext ω
    simp [sampleMeanV1, Pi.smul_apply, smul_eq_mul]
  have hvar : Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 4 :=
    variance_sum_le_probe h_indep hmeas h01
  have hvarMean : Var[sampleMeanV1 X n; μ] ≤ 1 / (4 * (n : ℝ)) :=
    variance_mean_le_probe hn hvar
  exact (chebyshev_abs_probe hmlm (σ2 := 1 / (4 * (n : ℝ))) (c := ε) hε hvarMean).trans
    (le_of_eq (by field_simp))

end UnionProbe