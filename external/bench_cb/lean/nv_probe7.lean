/-
  nv_probe7.lean — turn 131.  Non-vacuity of (T9), the direct way.
-/

import Mathlib.Probability.Independence.Basic
import Mathlib.MeasureTheory.Measure.Dirac
import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

namespace NV7

lemma unit_set_eq (s : Set Unit) : s = Set.univ ∨ s = ∅ := by
  by_cases h : () ∈ s
  · left; ext x; rw [Subsingleton.elim x ()]; exact ⟨fun _ => trivial, fun _ => h⟩
  · right; ext x; rw [Subsingleton.elim x ()]; exact ⟨fun hx => absurd hx h, fun hx => absurd hx (by simp)⟩

/-- On `Unit`, every family is independent. -/
lemma iIndepFun_unit {ι : Type*} {β : ι → Type*} [∀ i, MeasurableSpace (β i)]
    (μ : Measure Unit) [IsProbabilityMeasure μ] {f : ∀ i, Unit → β i} :
    iIndepFun f μ := by
  rw [iIndepFun_iff_measure_inter_preimage_eq_mul]
  intro S sets hmeas
  by_cases hall : ∀ i ∈ S, f i ⁻¹' sets i = Set.univ
  · have hInt : (⋂ i ∈ S, f i ⁻¹' sets i) = Set.univ := by
      ext x; simp only [Set.mem_iInter, Set.mem_univ, iff_true]
      intro i hi; rw [hall i hi]; exact trivial
    have hprod : (∏ i ∈ S, μ (f i ⁻¹' sets i)) = 1 :=
      Finset.prod_eq_one fun i hi => by rw [hall i hi, measure_univ]
    rw [hInt, hprod, measure_univ]
  · push_neg at hall
    obtain ⟨i0, hi0, hi0ne⟩ := hall
    have hempty : f i0 ⁻¹' sets i0 = ∅ := by
      rcases unit_set_eq (f i0 ⁻¹' sets i0) with h | h
      · exact absurd h hi0ne
      · exact h
    have hInt : (⋂ i ∈ S, f i ⁻¹' sets i) = ∅ := by
      ext x; simp only [Set.mem_iInter, Set.mem_empty_iff_false, iff_false, not_forall]
      exact ⟨i0, hi0, by rw [hempty]; exact not_false⟩
    have hprod : (∏ i ∈ S, μ (f i ⁻¹' sets i)) = 0 :=
      Finset.prod_eq_zero hi0 (by rw [hempty, measure_empty])
    rw [hInt, hprod, measure_empty]

end NV7