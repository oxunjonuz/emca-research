/-
  probe_t9.lean — turn 131.  Probe for discharging `hp` in T8 (the glue).

  T8 (union_regret_bound) takes `hp : ∀ i, μ.real (B i) ≤ 1/(4 r ε²)` as a
  HYPOTHESIS.  To discharge it we must (a) build `B i` as the deviation event of
  an explicit per-context sample family and apply T6, and (b) keep the
  `MeasurableSet` requirement of T1 (needed for the Set.indicator split).

  This probe only establishes the two pieces (a) needs from the samples:
    P1  MemLp of the scalar-multiple mean (for Chebyshev's `hY`).
    P2  MeasurableSet of the deviation event, from STRONG measurability of the
        samples — the point where `AEStronglyMeasurable` alone would not do.
-/

import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 800000

namespace UnionProbe9

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

noncomputable def sMean (X : ℕ → Ω → ℝ) (n : ℕ) : Ω → ℝ :=
  (n : ℝ)⁻¹ • ∑ i ∈ Finset.range n, X i

/-- P2: the deviation event is measurable when the samples are. -/
lemma deviation_measurable {X : ℕ → Ω → ℝ} {n : ℕ} {ε : ℝ}
    (hstrong : ∀ i, StronglyMeasurable (X i)) :
    MeasurableSet {ω | ε ≤ |sMean X n ω - ∫ x, sMean X n x ∂μ|} := by
  have hsum : StronglyMeasurable (fun ω => ∑ i ∈ Finset.range n, X i ω) :=
    Finset.stronglyMeasurable_sum _ fun i _ => hstrong i
  have hsm : StronglyMeasurable (sMean X n) := by
    convert hsum.const_smul ((n : ℝ))⁻¹ using 1
    ext ω
    simp [sMean, Pi.smul_apply, smul_eq_mul]
  have hsub : Measurable (fun ω => sMean X n ω - ∫ x, sMean X n x ∂μ) :=
    (hsm.sub stronglyMeasurable_const).measurable
  exact measurableSet_le measurable_const hsub.abs

/-- P1: MemLp of the mean, from boundedness + strong measurability. -/
lemma sMean_memLp [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ}
    (hstrong : ∀ i, StronglyMeasurable (X i))
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1) :
    MemLp (sMean X n) 2 μ := by
  have hml' : MemLp (fun ω => ∑ i ∈ Finset.range n, X i ω) 2 μ :=
    memLp_finset_sum _ fun i _ =>
      memLp_of_bounded (h01 i) (hstrong i).aestronglyMeasurable 2
  have := hml'.const_smul ((n : ℝ))⁻¹
  convert this using 1
  ext ω
  simp [sMean, Pi.smul_apply, smul_eq_mul]

end UnionProbe9
