/-
  axiom_audit.lean — turn 131.

  Independent, machine-checked audit of what the union_stoch_v2 theorems actually
  rest on.  `grep` for `sorry`/`axiom` is a text check; `#print axioms` asks the
  KERNEL.  Anything beyond `propext`, `Classical.choice`, `Quot.sound` is a real
  dependency to report.
-/

import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

-- Re-declare the file under audit by importing it as a module is not possible
-- (no Lake package for bench_cb/lean), so the audit is run on the same source
-- with `#print axioms` appended.  This file documents the intent; the actual
-- command is:
--   cat union_stoch_v2.lean audit_print.lean > _audit.lean && lean _audit.lean
