/-
  nv_probe.lean — turn 131.  Probe: can we even INHABIT the hypotheses of (T9)?

  If the hypotheses turn out unsatisfiable, (T9) is true and empty, and the honest
  thing is to say so.  Three pieces are needed on a concrete instance:
    A. iIndepFun for a constant family  (Ω = Unit, μ = dirac ())
    B. StronglyMeasurable for the same
    C. the [0,1] ae-bound
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

/-- A. Independence of a constant family on a one-point space, via the
`iIndepFun_iff` characterisation by the joint law. -/
lemma indep_const : iIndepFun (fun _ : Fin 1 => fun _ : Unit => (1/2 : ℝ))
    (Measure.dirac ()) := by
  rw [iIndepFun_iff]
  exact Subsingleton.elim _ _

/-- C. The [0,1] bound on the one-point space. -/
lemma bound_const : ∀ i : Fin 1, ∀ᵐ ω ∂(Measure.dirac ()),
    (fun _ : Unit => (1/2 : ℝ)) ω ∈ Set.Icc (0:ℝ) 1 :=
  fun _ => Filter.Eventually.of_forall fun _ => by norm_num

end NVProbe
