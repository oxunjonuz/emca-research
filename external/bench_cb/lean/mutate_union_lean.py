#!/usr/bin/env python3
"""
mutate_union_lean.py — turn 131.

A Lean mutation campaign for bench_cb/lean/union_stoch_v2.lean.

For each mutant we record:
  - the mutation (what was changed, and why it should matter)
  - exit code
  - the FIRST error line, verbatim
  - a CLASSIFICATION of the red, decided by string inspection of that line:
        semantic_conclusion  — the statement itself is now false/different and the
                               proof cannot reach it (the constant/statement is
                               load-bearing)
        syntactic_reference  — the proof body mentions a name that no longer
                               exists; this reds a NAME, not a FACT, and is
                               recorded as WEAK evidence
        ill_typed            — the mutated header no longer type-checks as a
                               function; recorded, but not as logic

The honest summary is the count in each class, not "N/N mutants caught".
"""

import subprocess, json, os, re, time

LEAN_DIR = os.path.dirname(os.path.abspath(__file__))
MATHLIB = os.environ.get("MATHLIB", "/work/Shopify/audit-work/mathlib")
BASE = os.path.join(LEAN_DIR, "union_stoch_v2.lean")
TARGETS = "Union.union_regret_bound"

MUTANTS = [
    ("M1_t6_conclusion_tightened",
     "T6 conclusion 1/(4 n ε²) -> 1/(2 n ε²)",
     "the Chebyshev+Popoviciu constant in T6 is tight for the proof",
     lambda s: s.replace(
        "      ≤ 1 / (4 * (n : ℝ) * ε ^ 2) := by\n  have hmlm : MemLp (sMean X n) 2 μ := sMean_memLp hstrong h01",
        "      ≤ 1 / (2 * (n : ℝ) * ε ^ 2) := by\n  have hmlm : MemLp (sMean X n) 2 μ := sMean_memLp hstrong h01")),
    ("M2_t6_no_square",
     "T6 conclusion 1/(4 n ε²) -> 1/(4 n ε)",
     "the ε² (Chebyshev's quadratic penalty) is load-bearing",
     lambda s: s.replace(
        "    μ.real {ω | ε ≤ |sMean X n ω - ∫ x, sMean X n x ∂μ|}\n      ≤ 1 / (4 * (n : ℝ) * ε ^ 2) := by\n  have hmlm : MemLp (sMean X n) 2 μ := sMean_memLp hstrong h01",
        "    μ.real {ω | ε ≤ |sMean X n ω - ∫ x, sMean X n x ∂μ|}\n      ≤ 1 / (4 * (n : ℝ) * ε) := by\n  have hmlm : MemLp (sMean X n) 2 μ := sMean_memLp hstrong h01")),
    ("M3_t9_conclusion_tightened",
     "T9 conclusion k/(4 r ε²) -> k/(2 r ε²)",
     "T9's constant is not slack: the proof cannot be squeezed",
     lambda s: s.replace(
        "    ∫ ω, R ω ∂μ ≤ bΔ + M * ((k : ℝ) / (4 * (r : ℝ) * ε ^ 2)) := by",
        "    ∫ ω, R ω ∂μ ≤ bΔ + M * ((k : ℝ) / (2 * (r : ℝ) * ε ^ 2)) := by")),
    ("M4_t7_pooled_nonzero",
     "T7 pooled gap = 0 -> = 1",
     "the annihilation claim is a real equation, not a degeneracy",
     lambda s: s.replace(
        "    ∧ gapNum (2 * s) (4 * s) = 0 := by",
        "    ∧ gapNum (2 * s) (4 * s) = 1 := by")),
    ("M5_t7_drop_hds",
     "T7 drops the hypothesis d <= s",
     "the truncation hypothesis is needed (s - d is ℕ-subtraction)",
     lambda s: s.replace("theorem pooled_gap_zero (s d : Nat) (hds : d ≤ s) :",
                         "theorem pooled_gap_zero (s d : Nat) :")),
    ("M6_t4_exponent_halved",
     "T4 Hoeffding exponent /2 -> /4",
     "the sub-Gaussian exponent constant is load-bearing",
     lambda s: s.replace(
        "      ≤ Real.exp (-(n : ℝ) * ε ^ 2 / (2 * (c : ℝ))) := by\n  have hcR : (0 : ℝ) < (c : ℝ) := by exact_mod_cast hc",
        "      ≤ Real.exp (-((n : ℝ) * ε ^ 2) / (4 * (c : ℝ))) := by\n  have hcR : (0 : ℝ) < (c : ℝ) := by exact_mod_cast hc")),
    ("M7_t6_signature_no_indep",
     "T6 drops (h_indep : iIndepFun X μ) from the SIGNATURE",
     "independence is used by the proof, not merely named",
     lambda s: s.replace(
        """theorem chebyshev_sample_mean [IsProbabilityMeasure μ]
    {X : ℕ → Ω → ℝ} (h_indep : iIndepFun X μ)
    (hstrong : ∀ i, StronglyMeasurable (X i))""",
        """theorem chebyshev_sample_mean [IsProbabilityMeasure μ]
    {X : ℕ → Ω → ℝ}
    (hstrong : ∀ i, StronglyMeasurable (X i))""")),
    ("M8_t6_signature_no_bounded",
     "T6 drops (h01 : ∀ i, ∀ᵐ ω, X i ω ∈ Icc 0 1) from the SIGNATURE",
     "the [0,1] bound is used by the proof, not merely named",
     lambda s: s.replace(
        """    (hstrong : ∀ i, StronglyMeasurable (X i))
    (h01 : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) 1)
    {n : ℕ} (hn : 0 < n) {ε : ℝ} (hε : 0 < ε) :
    μ.real {ω | ε ≤ |sMean X n ω - ∫ x, sMean X n x ∂μ|}
      ≤ 1 / (4 * (n : ℝ) * ε ^ 2) := by""",
        """    (hstrong : ∀ i, StronglyMeasurable (X i))
    {n : ℕ} (hn : 0 < n) {ε : ℝ} (hε : 0 < ε) :
    μ.real {ω | ε ≤ |sMean X n ω - ∫ x, sMean X n x ∂μ|}
      ≤ 1 / (4 * (n : ℝ) * ε ^ 2) := by""")),
    ("M9_t9_hp_strictly_smaller",
     "T9's internal hp bound 1/(4 r ε²) -> 1/(8 r ε²)",
     "T9 consumes T6 at exactly the constant T6 supplies",
     lambda s: s.replace(
        "    (fun _ => 1 / (4 * (r : ℝ) * ε ^ 2)) hR",
        "    (fun _ => 1 / (8 * (r : ℝ) * ε ^ 2)) hR").replace(
        "    ∫ ω, R ω ∂μ ≤ bΔ + M * ((k : ℝ) / (4 * (r : ℝ) * ε ^ 2)) := by",
        "    ∫ ω, R ω ∂μ ≤ bΔ + M * ((k : ℝ) / (8 * (r : ℝ) * ε ^ 2)) := by")),
    ("M10_t5b_constant_loosened",
     "T5b variance bound n/4 -> n/2 (LOOSER)",
     "control: a weaker bound should still be provable, so this mutant "
     "SHOULD SURVIVE.  A survivor here is the honest finding that the suite "
     "does not pin the tight constant.",
     lambda s: s.replace(
        "    Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 4 := by\n  have hml' : ∀ i ∈ Finset.range n, MemLp (X i) 2 μ :=",
        "    Var[∑ i ∈ Finset.range n, X i; μ] ≤ (n : ℝ) / 2 := by\n  have hml' : ∀ i ∈ Finset.range n, MemLp (X i) 2 μ :=")),
]


def classify(first_err):
    if not first_err:
        return "SURVIVED"
    if "unknown identifier" in first_err or "unknown constant" in first_err:
        return "syntactic_reference"
    if "application type mismatch" in first_err and "expected to have type" in first_err:
        return "ill_typed"
    if "unsolved goals" in first_err or "omega could not prove" in first_err:
        return "semantic_conclusion"
    return "other"


def run(path):
    t0 = time.time()
    p = subprocess.run(["lake", "env", "lean", path], cwd=MATHLIB,
                       capture_output=True, text=True, timeout=3600)
    return p.returncode, p.stdout + p.stderr, time.time() - t0


def main():
    base_src = open(BASE).read()
    # baseline must be green first
    rc, out, secs = run(BASE)
    print(f"BASELINE exit={rc} ({secs:.1f}s)  errors={out.count('error:')}")
    if rc != 0:
        print("BASELINE NOT GREEN — refusing to score.")
        print(out[:3000]); return
    if "sorry" in out:
        print("BASELINE uses sorry — refusing to score."); return

    rows = []
    for name, desc, why, fn in MUTANTS:
        code = fn(base_src)
        if code == base_src:
            rows.append({"id": name, "mutation": desc, "why": why,
                         "applied": False, "exit": None, "verdict": "PATCH_NOT_APPLIED",
                         "first_error": None})
            print(f"{name}: PATCH NOT APPLIED"); continue
        p = os.path.join(LEAN_DIR, f"m_{name}.lean")
        open(p, "w").write(code)
        rc, out, secs = run(p)
        lines = [l for l in out.splitlines() if "error:" in l]
        first = lines[0] if lines else None
        verdict = classify(first)
        rows.append({"id": name, "mutation": desc, "why": why,
                     "applied": True, "exit": rc, "errors": len(lines),
                     "seconds": round(secs, 1),
                     "verdict": verdict, "first_error": first})
        print(f"{name}: exit={rc} errors={len(lines)} verdict={verdict}")
        if first: print(f"    {first[:150]}")

    live = [r for r in rows if r["applied"]]
    killed = [r for r in live if r["exit"] != 0]
    survived = [r for r in live if r["exit"] == 0]
    print(f"\napplied={len(live)} killed={len(killed)} survived={len(survived)}")
    print("survivors (honest findings):")
    for r in survived:
        print(f"  {r['id']}: {r['mutation']}")
    sem = [r for r in killed if r["verdict"] == "semantic_conclusion"]
    print(f"semantic (load-bearing, not name-based) kills: {len(sem)}")
    for r in sem:
        print(f"  {r['id']}")

    json.dump({"baseline": {"exit": rc, "seconds": round(secs, 1)},
               "target": TARGETS, "rows": rows,
               "applied": len(live), "killed": len(killed),
               "survived": len(survived),
               "semantic_kills": [r["id"] for r in sem]},
              open(os.path.join(LEAN_DIR, "mutation_summary.json"), "w"), indent=1)
    print("\nwrote mutation_summary.json")


if __name__ == "__main__":
    main()
