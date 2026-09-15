/-
  nv_probe4.lean — turn 131.  Can we get `iIndepFun` for an ℕ-indexed family on
  the one-point space?  If yes, the non-vacuity instance exists.

  Strategy: on `Unit` every preimage set is `∅` or `univ`; such a family of sets
  is always iIndepSets, and iIndepSets is what iIndepFun asks for.
-/

import Mathlib.Probability.Independence.Basic
import Mathlib.MeasureTheory.Measure.Dirac

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

namespace NV4

/-- Every subset of `Unit` is `∅` or `univ`. -/
lemma unit_set_eq (s : Set Unit) : s = Set.univ ∨ s = ∅ := by
  by_cases h : () ∈ s
  · left; ext x; simp [Subsingleton.elim x ()]; exact h
  · right; ext x; simp [Subsingleton.elim x ()]; exact h

/-- On `Unit`, every family is independent: the only events available are `∅` and
`univ`, and products of 0/1 indicators are automatically multiplicative. -/
lemma iIndepSets_unit {ι : Type*} (s : ι → Set Unit) (μ : Measure Unit) :
    iIndepSets s μ := by
  rw [iIndepSets_iff]
  intro S f' hmeas
  have hone : ∀ i, f' i = Set.univ ∨ f' i = ∅ := fun i => unit_set_eq (f' i)
  rcases (S.eq_empty_or_nonempty) with hS | hS
  · subst hS; simp
  · sorry

end NV4
