/-
  nonvacuity.lean — turn 131.  (Concatenated AFTER union_stoch_v2.lean.)

  A theorem with unsatisfiable hypotheses is TRUE and EMPTY.  (T9)'s conclusion
  would be worth nothing if no instance satisfied `h_indep`, `hstrong`, `h01`,
  `hgood`, `hbound` simultaneously.  This file APPLIES (T9) to a concrete
  instance, so the bound is inhabited, not vacuous.

  Instance: Ω = Unit with μ = dirac () (a probability measure), k = 1 context,
  r = 1 pull, X := constant 1/2 (a genuine [0,1] family), regret R ≡ 0.
  Then the conclusion reads `∫ R ≤ 0 + 0·k/(4rε²)`, i.e. `0 ≤ 0`.
-/

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

namespace UnionNV

/-- The concrete sample family: one context, one pull, constant `1/2`. -/
noncomputable def X0 : Fin 1 → ℕ → Unit → ℝ := fun _ _ _ => 1 / 2

/-- (NV1) Independence holds because `Fin 1` is a subsingleton. -/
lemma X0_indep : ∀ i : Fin 1, iIndepFun (X0 i) (Measure.dirac ()) :=
  fun _ => iIndepFun.of_subsingleton

/-- (NV2) Strong measurability of a constant family. -/
lemma X0_strong : ∀ i j, StronglyMeasurable (X0 i j) := fun _ _ => stronglyMeasurable_const

/-- (NV3) The `[0,1]` almost-everywhere bound. -/
lemma X0_01 : ∀ i j, ∀ᵐ ω ∂(Measure.dirac ()) , X0 i j ω ∈ Set.Icc (0:ℝ) 1 :=
  fun _ _ => Filter.Eventually.of_forall fun _ => by norm_num [X0]

/-- (NV4) THE INSTANCE IS INHABITED — and (T9) is APPLIED to it.  Every
hypothesis is discharged on this instance, so the bound is not vacuous. -/
theorem t9_applied :
    ∫ _ : Unit, (0 : ℝ) ∂(Measure.dirac ())
      ≤ (0 : ℝ) + 0 * (((1 : ℕ) : ℝ) / (4 * ((1 : ℕ) : ℝ) * (1/2 : ℝ) ^ 2)) := by
  have h := Union.union_regret_bound
    (μ := Measure.dirac ()) (R := fun _ : Unit => (0 : ℝ))
    (k := 1) (r := 1) (X := X0)
    integrable_const (fun _ => X0_indep _) X0_strong X0_01
    (ε := 1/2) (bΔ := 0) (M := 0)
    (by norm_num) le_rfl le_rfl
    (fun _ _ => le_rfl) (fun _ => le_rfl)
  simpa using h

/-- (NV5) The right-hand side at these parameters is exactly `0`: the applied
instance reduces to `0 ≤ 0`, computed independently of (T9). -/
theorem instance_rhs_computed :
    (0:ℝ) + 0 * (((1 : ℕ) : ℝ) / (4 * ((1 : ℕ) : ℝ) * (1/2 : ℝ) ^ 2)) = 0 := by norm_num

end UnionNV
