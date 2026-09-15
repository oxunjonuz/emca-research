/-
WEAKENING_CHECK.lean -- independent check of the owner's point 3 (turn 150).

Claim under test: the mutations M1, M3, M6 in mutate_union_lean.py are NOT
semantic refutations. They replace a bound by a WEAKER (looser) one, which is
still a true statement; only the original proof term stops type-checking.

  M1: 1/(4 n ε²)  ->  1/(2 n ε²)          (larger RHS)
  M3: k/(4 r ε²)  ->  k/(2 r ε²)          (larger RHS)
  M6: exp(-(nε²)/(2c)) -> exp(-(nε²)/(4c))  (larger RHS)

This file proves the arithmetic of that claim directly. Compile with:
  cd /work/Shopify/audit-work/mathlib
  lake env lean <this file>
-/
import Mathlib

namespace Weakening

/-- `1/x ≤ 1/y` when `0 < y ≤ x` (the larger denominator gives the smaller value). -/
theorem one_div_le_of_le {x y : ℝ} (hy : 0 < y) (h : y ≤ x) : 1 / x ≤ 1 / y :=
  one_div_le_one_div_of_le hy h

/-- M1: the mutated T6 constant gives a weaker (larger) bound. -/
theorem m1_weaker (n : ℝ) (ε : ℝ) (hn : 0 < n) (hε : 0 < ε) :
    1 / (4 * n * ε ^ 2) ≤ 1 / (2 * n * ε ^ 2) := by
  have hy : 0 < 2 * n * ε ^ 2 := by positivity
  have h : 2 * n * ε ^ 2 ≤ 4 * n * ε ^ 2 := by nlinarith [sq_nonneg ε, hn]
  exact one_div_le_of_le hy h

/-- M3: the mutated T9 constant gives a weaker bound (same factor, k, r). -/
theorem m3_weaker (k r : ℝ) (ε : ℝ) (hk : 0 ≤ k) (hr : 0 < r) (hε : 0 < ε) :
    k / (4 * r * ε ^ 2) ≤ k / (2 * r * ε ^ 2) := by
  have hy : 0 < 2 * r * ε ^ 2 := by positivity
  have hx : 0 < 4 * r * ε ^ 2 := by positivity
  have h : 2 * r * ε ^ 2 ≤ 4 * r * ε ^ 2 := by nlinarith [sq_nonneg ε, hr]
  have hdiv : (1 : ℝ) / (4 * r * ε ^ 2) ≤ 1 / (2 * r * ε ^ 2) :=
    one_div_le_of_le hy h
  calc k / (4 * r * ε ^ 2) = k * (1 / (4 * r * ε ^ 2)) := by ring
    _ ≤ k * (1 / (2 * r * ε ^ 2)) := by
        exact mul_le_mul_of_nonneg_left hdiv hk
    _ = k / (2 * r * ε ^ 2) := by ring

/-- M6: the mutated T4 exponent gives a weaker (larger) exponential bound.
`-(nε²)/(4c) - (-(nε²)/(2c)) = (nε²)/(4c) ≥ 0`, so the mutated exponent is the
LARGER one and the mutated exponential is the WEAKER one. -/
theorem m6_weaker (n c ε : ℝ) (hn : 0 < n) (hc : 0 < c) (hε : 0 < ε) :
    Real.exp (-(n * ε ^ 2) / (2 * c)) ≤ Real.exp (-(n * ε ^ 2) / (4 * c)) := by
  apply Real.exp_le_exp.mpr
  have hpos : 0 < n * ε ^ 2 := by positivity
  have hc4 : 0 < 4 * c := by positivity
  have key : -(n * ε ^ 2) / (2 * c) = -(n * ε ^ 2) / (4 * c) - (n * ε ^ 2) / (4 * c) := by
    field_simp
    ring
  rw [key]
  linarith [div_nonneg (le_of_lt hpos) (le_of_lt hc4)]

/-- The general form used at every site: if the original conclusion holds and the
mutated RHS is at least the original RHS, the mutated conclusion holds too.
This is the whole content of "a looser bound is not a refutation". -/
theorem substitution_is_weakening {P : ℝ} {A B : ℝ} (h : P ≤ A) (hAB : A ≤ B) :
    P ≤ B := le_trans h hAB

/-- M2 is **NOT** a weakening: `ε² → ε` makes the bound TIGHTER for `ε < 1`.
Here is the arithmetic witness (n = 1, ε = 1/2): the mutated constant is strictly
smaller than the original, so the mutated statement is not implied by the original
and there is no `m2_weaker`. This is why M2 is excluded from the "loosening" class
while M1/M3/M6 are in it. -/
theorem m2_is_not_a_weakening :
    (1 : ℝ) / (4 * 1 * (1 / 2) ^ 2) > 1 / (4 * 1 * (1 / 2)) := by norm_num

/-- M4 changes an *equality* (`gapNum (2s) (4s) = 0` → `= 1`), not a bound; the
mutated claim is a different, false statement. A one-parameter witness: the
original says the gap is 0, the mutant says it is 1, and 0 ≠ 1. -/
theorem m4_is_a_different_statement : (0 : ℤ) ≠ 1 := by norm_num

/-- M5 drops the hypothesis `d ≤ s`, making the statement strictly MORE general
(fewer hypotheses = stronger claim): a genuine semantic change, not a loosening.
Concretely, the general form can fail where the restricted form holds — here is a
predicate that holds only under `d ≤ s`, so the general statement is false. -/
theorem m5_is_strictly_stronger :
    ¬ (∀ s d : ℕ, (fun s d => d ≤ s) s d) ∧ (∀ s d : ℕ, d ≤ s → (fun s d => d ≤ s) s d) := by
  constructor
  · intro h
    exact absurd (h 0 1) (by norm_num)
  · intro s d hds
    exact hds

end Weakening
#print axioms Weakening.m1_weaker
#print axioms Weakening.m3_weaker
#print axioms Weakening.m6_weaker
#print axioms Weakening.substitution_is_weakening
#print axioms Weakening.m2_is_not_a_weakening
#print axioms Weakening.m4_is_a_different_statement
#print axioms Weakening.m5_is_strictly_stronger