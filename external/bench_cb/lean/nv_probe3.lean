/-
  nv_probe.lean — turn 131.  Probe: can we INHABIT the hypotheses of (T9)?
-/

import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 800000

namespace NVProbe

/-- Independence of a constant family on a one-point space, via the subsingleton
index: the family has ONE member, which is always independent. -/
lemma indep_const : iIndepFun (ι := Fin 1) (fun _ : Fin 1 => fun _ : Unit => (1/2 : ℝ))
    (Measure.dirac ()) :=
  iIndepFun.of_subsingleton

/-- The [0,1] bound on the one-point space. -/
lemma bound_const : ∀ i : Fin 1, ∀ᵐ ω ∂(Measure.dirac ()),
    (fun _ : Unit => (1/2 : ℝ)) ω ∈ Set.Icc (0:ℝ) 1 :=
  fun _ => Filter.Eventually.of_forall fun _ => by norm_num

/-- Strong measurability of the constant family. -/
lemma strong_const : ∀ i : Fin 1, StronglyMeasurable (fun _ : Unit => (1/2 : ℝ)) :=
  fun _ => stronglyMeasurable_const

end NVProbe
