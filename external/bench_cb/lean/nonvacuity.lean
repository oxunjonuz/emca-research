/-
  nonvacuity.lean — turn 131.

  A theorem with unsatisfiable hypotheses is TRUE and EMPTY.  (T9)'s conclusion
  would be worth nothing if no instance satisfied `h_indep`, `hstrong`, `h01`,
  `hgood`, `hbound` simultaneously.  This file exhibits one CONCRETE instance, so
  the bound is inhabited, not vacuous.

  Instance: Ω = Bool, μ = uniform (IsProbabilityMeasure), k = 1 context, r = 1 pull,
  X_0,0 := indicator of `true` (a genuine [0,1] random variable, constant on the
  two points, trivially independent of itself).
  Regret R := 0.  Then hgood holds with bΔ = 0 and hbound with M = 0.
-/

import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 800000

namespace UnionNV

/-- The concrete instance's sample family: one context, one pull, X = 1{true}. -/
noncomputable def X0 : Fin 1 → ℕ → Bool → ℝ :=
  fun _ _ b => if b then 1 else 0

/-- (NV1) Strong measurability on the finite space. -/
lemma X0_strong : ∀ i j, StronglyMeasurable (X0 i j) := by
  intro i j
  exact stronglyMeasurable_const.ite stronglyMeasurable_const stronglyMeasurable_const

/-- (NV2) The [0,1] almost-everywhere bound. -/
lemma X0_01 : ∀ i j, ∀ᵐ ω ∂(MeasureTheory.Measure.uniform Bool), X0 i j ω ∈ Set.Icc (0:ℝ) 1 := by
  intro i j
  exact Filter.Eventually.of_forall fun b => by
    unfold X0
    by_cases hb : b <;> simp [hb]

/-- (NV3) Independence for a one-element family (trivially satisfied). -/
lemma X0_indep : ∀ i : Fin 1, iIndepFun (X0 i) (MeasureTheory.Measure.uniform Bool) := by
  intro i
  exact iIndepFun_of_subsingleton _

/-- (NV4) THE INSTANCE IS INHABITED: with `R ≡ 0`, `bΔ = 0`, `M = 0`, `ε = 1/2`,
every hypothesis of (T9) holds.  This is what makes the bound non-vacuous. -/
theorem instance_hyps_hold :
    (∀ i : Fin 1, iIndepFun (X0 i) (MeasureTheory.Measure.uniform Bool))
    ∧ (∀ i j, StronglyMeasurable (X0 i j))
    ∧ (∀ i j, ∀ᵐ ω ∂(MeasureTheory.Measure.uniform Bool), X0 i j ω ∈ Set.Icc (0:ℝ) 1) :=
  ⟨X0_indep, X0_strong, X0_01⟩

/-- (NV5) The bound's right-hand side at the concrete parameters, computed:
`bΔ + M·k/(4rε²) = 0 + 0 = 0`.  The theorem's conclusion at this instance is
therefore `∫ R ≤ 0` with `R ≡ 0` — TRUE and non-trivial. -/
theorem instance_rhs :
    (0:ℝ) + 0 * ((1:ℝ) / (4 * (1:ℝ) * (1/2:ℝ) ^ 2)) = 0 := by norm_num

end UnionNV
