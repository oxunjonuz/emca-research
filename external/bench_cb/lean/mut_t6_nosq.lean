/-
  union_stoch.lean — turn 130, COMPLETED turn 131.

  THE STOCHASTIC PART of the union's regret bound, which turn 129 could not close
  (Mathlib was not available then). The claim to be formalised, in the owner's
  words:

    "the transition from  this probe loses at most Δ  to  the expected regret is
     bounded through the exploration budget and Δ  — that needs a concentration
     argument (Hoeffding/Azuma)".

  Contents:

    (T7) pooled_gap_zero       — the deterministic half (pooling annihilates the
                                 context-specific effect).
    (T1) integral_le_of_split  — expectation split at a measurable bad event.
    (T2) bad_le_sum            — finite union bound in real-measure form.
    (T3) expected_regret_le    — 𝔼[R] ≤ bΔ + M · Σ pᵢ  (concentration in).
    (T4) hoeffding_mean_le     — Mathlib's sub-Gaussian Hoeffding for a sample mean.
    (T5) chebyshev_abs         — Chebyshev with an explicit variance bound.
    (T5b) variance_sum_le      — variance of n independent [0,1] pulls ≤ n/4.
    (T6) chebyshev_sample_mean — Popoviciu + Chebyshev for [0,1] samples, CLOSED.
    (T9) union_regret_bound    — THE FULL BOUND, with `hp` DISCHARGED: the
                                 per-context bad-event probability is no longer an
                                 assumption but is PROVED from (T6) for an explicit
                                 family of `r` independent [0,1] pulls per context.

  Turn-131 note on (T6).  In turn 130 (T6) was stated for
      sampleMean X n := fun ω => (n:ℝ)⁻¹ * ∑ i ∈ Finset.range n, X i ω
  and elaboration of the STATEMENT timed out at `whnf` (8M heartbeats): the
  *pointwise* body forces the elaborator to unfold a `Finset.range` sum inside the
  `setOf` predicate.  Reformulating the mean as a scalar multiple of the SUM
  FUNCTION,
      sMean X n := (n:ℝ)⁻¹ • ∑ i ∈ Finset.range n, X i
  makes the term opaque to whnf; the statement elaborates and the proof closes.
  Both forms are connected pointwise by `sMean_apply`, so the reformulation is
  cosmetic — it changes what the elaborator must unfold, not what is proved.

  HONEST LIMIT, named rather than hidden: Mathlib has Hoeffding's INEQUALITY for
  sub-Gaussian variables but NOT Hoeffding's LEMMA (bounded ⇒ sub-Gaussian).  So
  (T4) is stated for variables that provably carry `HasSubgaussianMGF`; the
  UNCONDITIONAL closing route is Chebyshev + Popoviciu (T5/T5b/T6), and that is
  the route (T9) actually uses.  Both routes are in the file; neither assumes the
  missing bridge.
-/

import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.Variance
import Mathlib.MeasureTheory.Function.LpSeminorm.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real

open MeasureTheory ProbabilityTheory
open scoped ENNReal BigOperators

set_option maxHeartbeats 4000000

namespace Union

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}

/-! ### (T7) The deterministic half, restated. -/

/-- Gap of an arm in "numerator over 2n" units: `h/n − 1/2 = (2h − n)/(2n)`. -/
def gapNum (h n : Nat) : Int := 2 * (h : Int) - (n : Int)

/-- (T7) SEPARATION: pooling a context-reversal ANNIHILATES the effect. -/
theorem pooled_gap_zero (s d : Nat) (hds : d ≤ s) :
    gapNum (s + d) (2 * s) = 2 * (d : Int)
    ∧ gapNum (s - d) (2 * s) = -(2 * (d : Int))
    ∧ gapNum (2 * s) (4 * s) = 0 := by
  refine ⟨?_, ?_, ?_⟩ <;> unfold gapNum <;> omega

/-! ### (T1)–(T3) The concentration-to-regret composition. -/

/-- (T1) CONCENTRATION-TO-REGRET GLUE.

Turn-131 note: `0 ≤ bΔ` and `0 ≤ M` were hypotheses here in turn 130 but are NOT
used by the proof (the pointwise split and the const-integral computation need no
sign).  They are dropped rather than kept as decoration: a dead hypothesis is a
premise a mutation campaign would report as a false survivor.  Nonnegativity is
used one level up, in (T3). -/
lemma integral_le_of_split [IsFiniteMeasure μ] {R : Ω → ℝ} {B : Set Ω}
    (hB : MeasurableSet B) (hR : Integrable R μ)
    {bΔ M : ℝ}
    (hgood : ∀ ω, ω ∉ B → R ω ≤ bΔ)
    (hbound : ∀ ω, R ω ≤ M) :
    ∫ ω, R ω ∂μ ≤ bΔ * μ.real Bᶜ + M * μ.real B := by
  have hpoint : ∀ ω, R ω ≤ (Bᶜ.indicator (fun _ : Ω => bΔ)) ω
      + (B.indicator (fun _ : Ω => M)) ω := by
    intro ω
    by_cases hω : ω ∈ B
    · have h1 : (B.indicator (fun _ : Ω => M)) ω = M := Set.indicator_of_mem hω _
      have h2 : (Bᶜ.indicator (fun _ : Ω => bΔ)) ω = 0 :=
        Set.indicator_of_not_mem (by simpa using hω) _
      simpa [h1, h2] using hbound ω
    · have h1 : (B.indicator (fun _ : Ω => M)) ω = 0 := Set.indicator_of_not_mem hω _
      have h2 : (Bᶜ.indicator (fun _ : Ω => bΔ)) ω = bΔ := Set.indicator_of_mem (by simpa using hω) _
      simpa [h1, h2] using hgood ω hω
  have hf : Integrable (Bᶜ.indicator (fun _ : Ω => bΔ)) μ :=
    (integrable_const bΔ).indicator hB.compl
  have hg : Integrable (B.indicator (fun _ : Ω => M)) μ :=
    (integrable_const M).indicator hB
  calc ∫ ω, R ω ∂μ
      ≤ ∫ ω, ((Bᶜ.indicator (fun _ : Ω => bΔ)) ω
                + (B.indicator (fun _ : Ω => M)) ω) ∂μ :=
        integral_mono hR (hf.add hg) hpoint
    _ = (∫ ω, (Bᶜ.indicator (fun _ : Ω => bΔ)) ω ∂μ)
          + ∫ ω, (B.indicator (fun _ : Ω => M)) ω ∂μ := integral_add hf hg
    _ = bΔ * μ.real Bᶜ + M * μ.real B := by
        rw [integral_indicator hB.compl, integral_indicator hB,
            setIntegral_const, setIntegral_const, smul_eq_mul, smul_eq_mul]
        ring

/-- (T2) FINITE UNION BOUND for the bad event, in real-measure form. -/
lemma bad_le_sum {ι : Type*} (s : Finset ι) (B : ι → Set Ω) (p : ι → ℝ)
    (hp : ∀ i ∈ s, μ.real (B i) ≤ p i) :
    μ.real (⋃ i ∈ s, B i) ≤ ∑ i ∈ s, p i :=
  (measureReal_biUnion_finset_le s B).trans (Finset.sum_le_sum hp)

/-- (T3) THE STOCHASTIC REGRET BOUND, abstract concentration form. -/
theorem expected_regret_le {ι : Type*} [IsProbabilityMeasure μ] {R : Ω → ℝ}
    (s : Finset ι) (B : ι → Set Ω) (p : ι → ℝ)
    (hR : Integrable R μ) (hBm : ∀ i ∈ s, MeasurableSet (B i))
    (hp : ∀ i ∈ s, μ.real (B i) ≤ p i)
    {bΔ M : ℝ} (hbΔ0 : 0 ≤ bΔ) (hM0 : 0 ≤ M)
    (hgood : ∀ ω, ω ∉ (⋃ i ∈ s, B i) → R ω ≤ bΔ)
    (hbound : ∀ ω, R ω ≤ M) :
    ∫ ω, R ω ∂μ ≤ bΔ + M * ∑ i ∈ s, p i := by
  have hunion : μ.real (⋃ i ∈ s, B i) ≤ ∑ i ∈ s, p i := bad_le_sum s B p hp
  have hsplit := integral_le_of_split (B := ⋃ i ∈ s, B i)
    (Finset.measurableSet_biUnion s hBm) hR hgood hbound
  have hcompl : μ.real ((⋃ i ∈ s, B i))ᶜ ≤ 1 :=
    (measureReal_mono (Set.subset_univ _)).trans_eq measureReal_univ_eq_one
  have h1 : bΔ * μ.real ((⋃ i ∈ s, B i))ᶜ ≤ bΔ * 1 :=
    mul_le_mul_of_nonneg_left hcompl hbΔ0
  have h2 : M * μ.real (⋃ i ∈ s, B i) ≤ M * ∑ i ∈ s, p i :=
    mul_le_mul_of_nonneg_left hunion hM0
  calc ∫ ω, R ω ∂μ
      ≤ bΔ * μ.real ((⋃ i ∈ s, B i))ᶜ + M * μ.real (⋃ i ∈ s, B i) := hsplit
    _ ≤ bΔ * 1 + M * ∑ i ∈ s, p i := add_le_add h1 h2
    _ = bΔ + M * ∑ i ∈ s, p i := by ring

/-! ### (T4) Hoeffding for a sample mean, from Mathlib's sub-Gaussian inequality. -/

/-- (T4a) Raw form: the deviation event rewritten as a condition on the sum. -/
lemma hoeffding_mean_raw {X : ℕ → Ω → ℝ} (h_indep : iIndepFun X μ)
    {c : NNReal} {n : ℕ} (hn : 0 < n) (h_subG : ∀ i < n, HasSubgaussianMGF (X i) c μ)
    {ε : ℝ} (hε : 0 ≤ ε) :
    μ.real {ω | ε ≤ (∑ i ∈ Finset.range n, X i ω) / n}
      ≤ Real.exp (-((n : ℝ) * ε) ^ 2 / (2 * ↑n * ↑c)) := by
  have h := HasSubgaussianMGF.measure_sum_range_ge_le_of_iIndepFun h_indep h_subG
    (ε := (n : ℝ) * ε) (by positivity)
  have hset : {ω | ε ≤ (∑ i ∈ Finset.range n, X i ω) / n}
      = {ω | (n : ℝ) * ε ≤ ∑ i ∈ Finset.range n, X i ω} := by
    ext ω
    simp only [Set.mem_setOf_eq]
    rw [le_div_iff₀ (by exact_mod_cast hn : (0:ℝ) < (n:ℝ))]
    constructor <;> intro h' <;> linarith
  rw [hset]
  exact h

/-- (T4b) Exponent identity: `-(nε)²/(2nc) = -nε²/(2c)` for `n > 0`, `c > 0`. -/
lemma exp_arg_eq {n : ℕ} {c : ℝ} (hn : 0 < n) (hc : 0 < c) (ε : ℝ) :
    -((n : ℝ) * ε) ^ 2 / (2 * (n : ℝ) * c) = -(n : ℝ) * ε ^ 2 / (2 * c) := by
  have hn' : (n : ℝ) ≠ 0 := by positivity
  have hc' : c ≠ 0 := ne_of_gt hc
  field_simp
  ring

/-- (T4) HOEFFDING FOR A SAMPLE MEAN: conditional on `HasSubgaussianMGF`, because
Mathlib does not contain Hoeffding's lemma (bounded ⇒ sub-Gaussian). -/
lemma hoeffding_mean_le {X : ℕ → Ω → ℝ} (h_indep : iIndepFun X μ)
    {c : NNReal} (hc : 0 < c) {n : ℕ} (hn : 0 < n)
    (h_subG : ∀ i < n, HasSubgaussianMGF (X i) c μ) {ε : ℝ} (hε : 0 ≤ ε) :
    μ.real {ω | ε ≤ (∑ i ∈ Finset.range n, X i ω) / n}
      ≤ Real.exp (-(n : ℝ) * ε ^ 2 / (2 * (c : ℝ))) := by
  have hcR : (0 : ℝ) < (c : ℝ) := by exact_mod_cast hc
  refine (hoeffding_mean_raw h_indep hn h_subG hε).trans (le_of_eq ?_)
  congr 1
  rw [exp_arg_eq hn hcR ε]

/-! ### (T5)–(T6) Chebyshev + Popoviciu: the unconditional closing route. -/

/-- (T5) Chebyshev in real-measure form with an explicit variance bound. -/
lemma chebyshev_abs [IsFiniteMeasure μ] {Y : Ω → ℝ} (hY : MemLp Y 2 μ) {σ2 c : ℝ}
    (hc : 0 < c) (hvar : Var[Y; μ] ≤ σ2) :
    μ.real {ω | c ≤ |Y ω - ∫ x, Y x ∂μ|} ≤ σ2 / c ^ 2 := by
  rw [measureReal_def]
  refine (ENNReal.toReal_mono (by finiteness) (meas_ge_le_variance_div_sq hY hc)).trans ?_
  rw [ENNReal.toReal_ofReal (div_nonneg (variance_nonneg Y μ) (sq_nonneg c))]
  exact div_le_div_of_nonneg_right hvar (sq_nonneg c)

/-- (T5b) Variance of a sum of independent `[0,1]` variables is at most `n/4`. -/
lemma variance_sum_le [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ}
    (h_indep : iIndepFun X μ)
    (hmeas : ∀ i, AEStronglyMeasurable (X i) μ)
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1) :
    Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 4 := by
  have hml' : ∀ i ∈ Finset.range n, MemLp (X i) 2 μ :=
    fun i _ => memLp_of_bounded (h01 i) (hmeas i) 2
  rw [IndepFun.variance_sum hml' (fun i _ j _ hij => h_indep.indepFun hij)]
  calc ∑ i ∈ Finset.range n, Var[X i; μ]
      ≤ ∑ i ∈ Finset.range n, ((1 - 0) / 2) ^ 2 :=
        Finset.sum_le_sum fun i _ =>
          variance_le_sq_of_bounded (h01 i) (hmeas i).aemeasurable
    _ = (n : ℝ) / 4 := by
        simp only [Finset.sum_const, Finset.card_range, nsmul_eq_mul]
        ring

/-- The empirical mean of the first `n` samples, as a scalar multiple of the SUM
FUNCTION.  The `•` form (rather than a pointwise `fun ω => …`) is what lets the
statement of (T6) elaborate: whnf does not unfold through it. -/
noncomputable def sMean (X : ℕ → Ω → ℝ) (n : ℕ) : Ω → ℝ :=
  (n : ℝ)⁻¹ • ∑ i ∈ Finset.range n, X i

/-- The two forms of the mean agree pointwise, so the reformulation above is
cosmetic: it changes what the elaborator unfolds, not what is proved. -/
lemma sMean_apply (X : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) :
    sMean X n ω = (n : ℝ)⁻¹ * ∑ i ∈ Finset.range n, X i ω := by
  simp [sMean, Pi.smul_apply, smul_eq_mul]

/-- The deviation event of the mean is Borel-measurable when the samples are
strongly measurable — needed by (T1)'s indicator split. -/
lemma deviation_measurable {X : ℕ → Ω → ℝ} {n : ℕ} {ε : ℝ}
    (hstrong : ∀ i, StronglyMeasurable (X i)) :
    MeasurableSet {ω | ε ≤ |sMean X n ω - ∫ x, sMean X n x ∂μ|} := by
  have hsum : StronglyMeasurable (fun ω => ∑ i ∈ Finset.range n, X i ω) :=
    Finset.stronglyMeasurable_sum _ fun i _ => hstrong i
  have hsm : StronglyMeasurable (sMean X n) := by
    convert hsum.const_smul ((n : ℝ))⁻¹ using 1
    ext ω
    simp [sMean, Pi.smul_apply, smul_eq_mul]
  have hsub : Measurable (fun ω => sMean X n ω - ∫ x, sMean X n x ∂μ) :=
    (hsm.sub stronglyMeasurable_const).measurable
  exact measurableSet_le measurable_const hsub.abs

/-- `MemLp` of the mean, from strong measurability + boundedness. -/
lemma sMean_memLp [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ}
    (hstrong : ∀ i, StronglyMeasurable (X i))
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1) :
    MemLp (sMean X n) 2 μ := by
  have hml' : MemLp (fun ω => ∑ i ∈ Finset.range n, X i ω) 2 μ :=
    memLp_finset_sum _ fun i _ =>
      memLp_of_bounded (h01 i) (hstrong i).aestronglyMeasurable 2
  have := hml'.const_smul ((n : ℝ))⁻¹
  convert this using 1
  ext ω
  simp [sMean, Pi.smul_apply, smul_eq_mul]

/-- Variance transfer: the mean's variance is the sum's, divided by `n²`.  With
the `•` definition this is a direct consequence of `variance_smul` — the
accounting step that turn 130 could not close for the pointwise definition. -/
lemma variance_mean_le [IsProbabilityMeasure μ] {X : ℕ → Ω → ℝ} {n : ℕ} (hn : 0 < n)
    (h : Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 4) :
    Var[sMean X n; μ] ≤ 1 / (4 * (n : ℝ)) := by
  have hv : Var[sMean X n; μ]
      = ((n : ℝ))⁻¹ ^ 2 * Var[∑ i ∈ Finset.range n, X i; μ] := by
    simpa [sMean] using variance_smul (μ := μ) (((n : ℝ))⁻¹)
      (∑ i ∈ Finset.range n, X i)
  rw [hv]
  calc ((n : ℝ))⁻¹ ^ 2 * Var[∑ i ∈ Finset.range n, X i; μ]
      ≤ ((n : ℝ))⁻¹ ^ 2 * ((n : ℝ) / 4) := mul_le_mul_of_nonneg_left h (sq_nonneg _)
    _ = 1 / (4 * (n : ℝ)) := by field_simp; ring

/-- (T6) THE EMPIRICAL-MEAN CONCENTRATION, fully closed:
for `[0,1]` independent samples, `μ.real {ε ≤ |mean − 𝔼 mean|} ≤ 1/(4 n ε²)`. -/
theorem chebyshev_sample_mean [IsProbabilityMeasure μ]
    {X : ℕ → Ω → ℝ} (h_indep : iIndepFun X μ)
    (hstrong : ∀ i, StronglyMeasurable (X i))
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1)
    {n : ℕ} (hn : 0 < n) {ε : ℝ} (hε : 0 < ε) :
    μ.real {ω | ε ≤ |sMean X n ω - ∫ x, sMean X n x ∂μ|}
      ≤ 1 / (4 * (n : ℝ) * ε) := by
  have hmlm : MemLp (sMean X n) 2 μ := sMean_memLp hstrong h01
  have hvarMean : Var[sMean X n; μ] ≤ 1 / (4 * (n : ℝ)) :=
    variance_mean_le hn (variance_sum_le h_indep (fun i => (hstrong i).aestronglyMeasurable) h01)
  exact (chebyshev_abs hmlm (σ2 := 1 / (4 * (n : ℝ))) (c := ε) hε hvarMean).trans
    (le_of_eq (by field_simp))

/-! ### (T9) The full stochastic regret bound, `hp` DISCHARGED. -/

/-- (T9) THE FULL STOCHASTIC REGRET BOUND, with the concentration PROVED rather
than assumed.

Setting: `k` contexts, each probed with `r` independent `[0,1]` pulls
(`X i : ℕ → Ω → ℝ`, the first `r` of which are used for context `i`).  Context
`i`'s bad event is the event that its empirical mean deviates from its own
expectation by at least `ε`; then

    𝔼[R] ≤ bΔ + M · k / (4 r ε²).

The per-context probability `1/(4 r ε²)` is **not** a hypothesis here: it is
discharged from (T6), one application per context.  The bound mentions the
exploration budget `bΔ`, the number of pulls `r` and the per-probe loss scale
`M` — and NO pooled marginal: this is the stochastic counterpart of (T7).

Honest note.  The identification of "context `i`'s bad event" with the event that
`i`'s own contrast estimate is off by `ε` is a MODELLING step, made explicit in
the statement (the `B` family is defined from `X`); what (T9) proves is that once
that identification is made, the regret bound follows with no further
probability assumption. -/
theorem union_regret_bound [IsProbabilityMeasure μ] {R : Ω → ℝ}
    (hR : Integrable R μ) {k r : ℕ} (hr : 0 < r)
    {X : Fin k → ℕ → Ω → ℝ}
    (h_indep : ∀ i, iIndepFun (X i) μ)
    (hstrong : ∀ i j, StronglyMeasurable (X i j))
    (h01 : ∀ i j, ∀ᵐ ω ∂μ, X i j ω ∈ Set.Icc (0:ℝ) 1)
    {ε bΔ M : ℝ} (hε : 0 < ε) (hM0 : 0 ≤ M) (hbΔ0 : 0 ≤ bΔ)
    (hgood : ∀ ω, ω ∉ (⋃ i, {ω | ε ≤ |sMean (X i) r ω
        - ∫ x, sMean (X i) r x ∂μ|}) → R ω ≤ bΔ)
    (hbound : ∀ ω, R ω ≤ M) :
    ∫ ω, R ω ∂μ ≤ bΔ + M * ((k : ℝ) / (4 * (r : ℝ) * ε ^ 2)) := by
  have hp : ∀ i : Fin k, μ.real {ω | ε ≤ |sMean (X i) r ω
      - ∫ x, sMean (X i) r x ∂μ|} ≤ 1 / (4 * (r : ℝ) * ε ^ 2) :=
    fun i => chebyshev_sample_mean (h_indep i) (fun j => hstrong i j) (fun j => h01 i j) hr hε
  have hmain := expected_regret_le (μ := μ) (Finset.univ : Finset (Fin k))
    (fun i => {ω | ε ≤ |sMean (X i) r ω - ∫ x, sMean (X i) r x ∂μ|})
    (fun _ => 1 / (4 * (r : ℝ) * ε ^ 2)) hR
    (fun i _ => deviation_measurable (fun j => hstrong i j)) (fun i _ => hp i)
    hbΔ0 hM0 (fun ω hω => hgood ω (by simpa using hω)) hbound
  refine hmain.trans (le_of_eq ?_)
  rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
  ring

end Union
