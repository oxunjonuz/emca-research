/-
  nv_probe5.lean — turn 131.  Non-vacuity, the direct way.

  Try: with μ = dirac () on Unit and an arbitrary ℕ-indexed [0,1] family, prove
  iIndepFun from the iIndepFun_iff characterisation.  Each preimage is ∅ or univ,
  so the intersection is ∅ or univ and the product is a product of 0/1 numbers.
-/

import Mathlib.Probability.Independence.Basic
import Mathlib.MeasureTheory.Measure.Dirac

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

namespace NV5

lemma unit_set_eq (s : Set Unit) : s = Set.univ ∨ s = ∅ := by
  by_cases h : () ∈ s
  · left; ext x; simp [Subsingleton.elim x ()]; exact h
  · right; ext x; simp [Subsingleton.elim x ()]; exact h

/-- On `Unit`, every family is independent. -/
lemma iIndepFun_unit {ι : Type*} {β : ι → Type*} [∀ i, MeasurableSpace (β i)]
    (f : ∀ i, Unit → β i) (μ : Measure Unit) : iIndepFun f μ := by
  rw [iIndepFun_iff_measure_inter_preimage_eq_mul]
  intro S sets hmeas
  have key : ∀ i ∈ S, f i ⁻¹' sets i = Set.univ ∨ f i ⁻¹' sets i = ∅ :=
    fun i _ => unit_set_eq _
  by_cases hall : ∀ i ∈ S, f i ⁻¹' sets i = Set.univ
  · have hInt : (⋂ i ∈ S, f i ⁻¹' sets i) = Set.univ := by
      ext x; simp [Finset.mem_univ, hall]
    have hprod : (∏ i ∈ S, μ (f i ⁻¹' sets i)) = 1 := by
      apply Finset.prod_eq_one
      intro i hi; rw [hall i hi, measure_univ]
    rw [hInt, hprod]; simp
  · push_neg at hall
    obtain ⟨i0, hi0, hi0ne⟩ := hall
    have hempty : f i0 ⁻¹' sets i0 = ∅ := by
      rcases key i0 hi0 with h | h
      · exact absurd h hi0ne
      · exact h
    have hInt : (⋂ i ∈ S, f i ⁻¹' sets i) = ∅ := by
      ext x
      simp only [Set.mem_iInter, Set.mem_empty_iff_false, iff_false, not_forall]
      exact ⟨i0, hi0, by simp [hempty]⟩
    have hprod : (∏ i ∈ S, μ (f i ⁻¹' sets i)) = 0 := by
      apply Finset.prod_eq_zero hi0
      rw [hempty, measure_empty]
    rw [hInt, hprod]; simp

end NV5
