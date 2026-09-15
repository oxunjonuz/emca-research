import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

namespace Probe

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

/-- Chebyshev in real-measure form with an explicit variance bound. -/
lemma chebyshev_abs [IsFiniteMeasure μ] {Y : Ω → ℝ} (hY : MemLp Y 2 μ) {σ2 c : ℝ}
    (hc : 0 < c) (hvar : Var[Y; μ] ≤ σ2) :
    μ.real {ω | c ≤ |Y ω - ∫ x, Y x ∂μ|} ≤ σ2 / c ^ 2 := by
  rw [measureReal_def]
  refine (ENNReal.toReal_mono (by finiteness) (meas_ge_le_variance_div_sq hY hc)).trans ?_
  rw [ENNReal.toReal_ofReal (div_nonneg (variance_nonneg Y μ) (sq_nonneg c))]
  exact div_le_div_of_nonneg_right hvar (sq_nonneg c)

end Probe