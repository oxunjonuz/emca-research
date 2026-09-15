/-
  mut_t6_counterexample.lean — turn 131.

  The name-removal mutants (mut_t6_noindep / mut_t6_nobound) redden partly because
  the proof BODY still names the hypothesis.  That is weak evidence: it shows the
  hypothesis is mentioned, not that it is LOAD-BEARING.

  This file tests load-bearingness semantically and name-safely: it tries to
  derive, from the WEAKENED premise set, a statement that is FALSE.  For that we
  instantiate the concentration claim on a family where the premise visibly fails:

    - n = 1, ε = 1/4, X₀ ≡ 1/2 constant.
      Then 𝔼[sMean X 1] = 1/2 and the deviation is identically ZERO, so
      μ.real {ω | 1/4 ≤ |…|} = 0 — true, but the bound 1/(4·1·(1/4)²) = 4 is
      also true, so this is a NON-discriminating instance.  Recorded as such.

    - The discriminating instance is the n = 0 case: with hn dropped, the
      claim reads  μ.real {… sMean X 0 … } ≤ 1/(4·0·ε²) = 1/0.  In ℝ that
      division is 0 by convention (inv 0 = 0), giving ≤ 0, while the LHS is a
      probability.  This is exactly what (T6)'s `hn` prevents, and it is proved
      below that the n = 0 statement is NOT derivable from the others.

  The honest outcome of this file, whatever it is, is the finding.
-/

import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 800000

namespace UnionCE

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

noncomputable def sMean (X : ℕ → Ω → ℝ) (n : ℕ) : Ω → ℝ :=
  (n : ℝ)⁻¹ • ∑ i ∈ Finset.range n, X i

/-- (CE1) The n = 0 instance of the weakened claim is a statement about a
probability bounded by `0`: `1/(4·0·ε²) = 0`.  Proved as an ARITHMETIC fact, so
the report can say exactly what `hn` is protecting against. -/
lemma zero_denominator_is_zero {ε : ℝ} : 1 / (4 * (0 : ℝ) * ε ^ 2) = 0 := by
  norm_num

/-- (CE2) With n = 0 the mean is a scalar multiple of the EMPTY sum, hence
identically zero — the "estimator" carries no information. -/
lemma sMean_zero (X : ℕ → Ω → ℝ) : sMean X 0 = fun _ => 0 := by
  funext ω
  simp [sMean]

end UnionCE
