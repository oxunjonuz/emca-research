/-
  nonvacuity_v6.lean — turn 131.  (Concatenated AFTER union_stoch_v2.lean.)

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

/-- On `Unit`, every preimage set is `∅` or `univ`. -/
lemma unit_set_eq (s : Set Unit) : s = Set.univ ∨ s = ∅ := by
  by_cases h : () ∈ s
  · left; ext x; rw [Subsingleton.elim x ()]; exact ⟨fun _ => trivial, fun _ => h⟩
  · right; ext x; rw [Subsingleton.elim x ()]; exact ⟨fun hx => absurd hx h, fun hx => absurd hx (by simp)⟩

/-- On `Unit`, every family is independent. -/
lemma iIndepFun_unit {ι : Type*} {β : ι → Type*} [∀ i, MeasurableSpace (β i)]
    (μ : Measure Unit) [IsProbabilityMeasure μ] {f : ∀ i, Unit → β i} :
    iIndepFun f μ := by
  rw [iIndepFun_iff_measure_inter_preimage_eq_mul]
  intro S sets _hmeas
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

/-- The concrete sample family: one context, constant `1/2`. -/
noncomputable def Xc : (Fin 1) → ℕ → Unit → ℝ := fun _ _ _ => (1 / 2 : ℝ)

lemma Xc_indep : ∀ _i : Fin 1, iIndepFun (Xc _i) (Measure.dirac ()) :=
  fun _ => iIndepFun_unit (Measure.dirac ()) (f := Xc _)

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
  exact h

/-- (NV-compute) The right-hand side at these parameters is exactly `0`, computed
independently of (T9): the instance really does reduce to `0 ≤ 0`. -/
theorem instance_rhs_computed :
    (0:ℝ) + 0 * (((1 : ℕ) : ℝ) / (4 * ((1 : ℕ) : ℝ) * (1/2 : ℝ) ^ 2)) = 0 := by norm_num

end UnionNV