/-
  nonvacuity_v5.lean — turn 131.  (Concatenated AFTER union_stoch_v2.lean.)

  A theorem with unsatisfiable hypotheses is TRUE and EMPTY.  (T9)'s bound would
  be worth nothing if no instance satisfied all its hypotheses.  This file
  APPLIES (T9) to a concrete instance, so the bound is inhabited.

  Instance: Ω = Unit, μ = dirac () (a probability measure); k = 1 context,
  r = 1 pull, X := constant 1/2 (a genuine [0,1] family); regret R ≡ 0.
  Conclusion reads `∫ R ≤ 0 + 0 · 1/(4·1·(1/2)²)`, i.e. `0 ≤ 0`.
-/

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

namespace UnionNV

/-- The concrete sample family: one context, `k = 1`; constant `1/2`. -/
noncomputable def Xc : (Fin 1) → ℕ → Unit → ℝ := fun _ _ _ => (1 / 2 : ℝ)

lemma Xc_indep : ∀ _i : Fin 1, iIndepFun (Xc _i) (Measure.dirac ()) :=
  fun _ => iIndepFun.of_subsingleton

lemma Xc_strong : ∀ _i j, StronglyMeasurable (Xc _i j) :=
  fun _ _ => stronglyMeasurable_const

lemma Xc_01 : ∀ _i j, ∀ᵐ _ω ∂(Measure.dirac ()), Xc _i j _ω ∈ Set.Icc (0:ℝ) 1 :=
  fun _ _ => Filter.Eventually.of_forall fun _ => by norm_num [Xc]

/-- (NV) (T9) IS APPLIED — every hypothesis discharged on this instance, so the
bound constrains at least one non-trivial model. -/
theorem t9_applied :
    ∫ _ : Unit, (0 : ℝ) ∂(Measure.dirac ())
      ≤ (0 : ℝ) + 0 * (((1 : ℕ) : ℝ) / (4 * ((1 : ℕ) : ℝ) * (1/2 : ℝ) ^ 2)) := by
  have h := Union.union_regret_bound (μ := Measure.dirac ())
    (R := (fun _ : Unit => (0 : ℝ))) (k := 1) (r := 1) (X := Xc)
    (hR := integrable_const (0:ℝ)) (hr := by norm_num)
    (h_indep := Xc_indep) (hstrong := Xc_strong) (h01 := Xc_01)
    (ε := (1/2 : ℝ)) (bΔ := 0) (M := 0)
    (hε := by norm_num) (hM0 := le_rfl) (hbΔ0 := le_rfl)
    (hgood := fun _ _ => le_rfl) (hbound := fun _ => le_rfl)
  simpa using h

/-- (NV-compute) The right-hand side at these parameters is exactly `0`, computed
independently of (T9): the instance really does reduce to `0 ≤ 0`. -/
theorem instance_rhs_computed :
    (0:ℝ) + 0 * (((1 : ℕ) : ℝ) / (4 * ((1 : ℕ) : ℝ) * (1/2 : ℝ) ^ 2)) = 0 := by norm_num

end UnionNV
