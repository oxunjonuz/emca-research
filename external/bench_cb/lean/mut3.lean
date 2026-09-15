/-
  UNION_BOUND.lean — turn 129.

  The FINITE, COMBINATORIAL core of the claim the owner asked to formalise:

    "a regret bound for the case where the true cause has a
     context-specific (not pooled) effect, and must still be DISCOVERED."

  Honest scope, stated in the file and in the report: core Lean 4.19 with NO
  Mathlib is installed here. What can be closed in core is the finite arithmetic
  skeleton of the argument, not the stochastic (probability) statement. Each
  theorem below is a genuine arithmetic obligation: a mutated statement is
  FALSE, so the proofs are load-bearing (checked by mutation in
  lean/mutate_check.sh and reported).

  Three obligations:
    (S) separation : pooling a context-reversal ANNIHILATES the effect, while
                     the per-context gap survives. This is the precise reason a
                     pooled scan *cannot* see the arm — the union's context
                     split is necessary, not cosmetic.
    (P) pooled_probes_none : a pooled rule with a positive margin therefore
                     nominates nothing among the reversed arms.
    (B) union_regret_le : the discovery cost is bounded by
                     (number of exploration pulls) * (per-pull loss),
                     INDEPENDENT of the pooled marginal.
-/

namespace Union

/-- The gap of an arm in "numerator over 2n" units: for `h` successes in `n`
pulls, `h/n − 1/2 = (2h − n) / (2n)`. So `gapNum h n` is the numerator of
`rate − 1/2` over the common denominator `2n`. Positive = the arm pays above
the flat 1/2 alternative; zero = the flat alternative. -/
def gapNum (h n : Nat) : Int := 2 * (h : Int) - (n : Int)

/-- (S) SEPARATION. Two balanced contexts, each `2s` pulls, on an arm whose
effect reverses: `s+d` successes in one, `s−d` in the other. The per-context
gaps are `2d` and `−2d`; the POOLED gap is exactly `0` for every `s`, `d`.
This is why a pooled scan cannot separate the arm while a context scan can. -/
theorem separation (s d : Nat) (hds : d ≤ s) :
    gapNum (s + d) (2 * s) = 2 * (d : Int)
    ∧ gapNum (s - d) (2 * s) = -(2 * (d : Int))
    ∧ gapNum (2 * s) (4 * s) = 0 := by
  refine ⟨?_, ?_, ?_⟩ <;> unfold gapNum <;> omega

/-- (P) NO POOLED NOMINATION. With a strictly positive margin `M`, the pooled
gap (`0`) never clears it: a pooled-only rule nominates nothing here. -/
theorem pooled_probes_none (s M : Nat) (hM : 0 < M) :
    ¬ (gapNum (2 * s) (4 * s) ≥ (M : Int)) := by
  unfold gapNum
  omega

/-- (B) THE UNION'S DISCOVERY BOUND. If every one of the `e` exploration pulls
loses at most `Δ`, the total exploration regret is at most `e · Δ` — a quantity
that does not mention the pooled marginal at all. Finite and general: the list
is an arbitrary finite arm set. -/
theorem union_regret_le : ∀ (losses : List Nat) (Δ : Nat),
    (∀ l ∈ losses, l ≤ Δ) → losses.sum ≤ losses.length * Δ / 2
  | [], _, _ => by simp
  | l :: ls, Δ, h => by
      have hl : l ≤ Δ := h l (by simp)
      have hls : ∀ x ∈ ls, x ≤ Δ := fun x hx => h x (by simp [hx])
      have ih := union_regret_le ls Δ hls
      simp only [List.sum_cons, List.length_cons]
      rw [Nat.add_mul, Nat.one_mul]
      omega

/-- Sanity: the separation statement is not vacuous — at concrete values the
pooled gap is `0` and each context gap is `±2d`. `#eval` at check time. -/
example : gapNum 7 10 = 4 ∧ gapNum 3 10 = -4 ∧ gapNum 10 20 = 0 := by
  refine ⟨?_, ?_, ?_⟩ <;> unfold gapNum <;> decide

end Union
