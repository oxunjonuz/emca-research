#!/usr/bin/env python3
"""mutate_identification_lean.py -- the premise campaign for IDENTIFICATION_BOUND.lean
(turn 154).

One deliberate fault at a time in a COPY of the file; `lake env lean` must go RED for
each. A mutant that still compiles is a SURVIVOR and is reported as one -- not as a
kill. The original file is never touched.

The mutations target the three claims the file makes:
  M1  `identification_is_conditional`'s conclusion set equality -> the empty set
      (the identification made trivially true: a real weakening of the claim)
  M2  `hgood_is_an_independent_premise`'s negation dropped (the counterexample made
      into a positive statement -- should NOT compile as stated)
  M3  `bound_at_implemented_params`'s constant 4/5 -> 1/5 (the vacuity claim's number)
  M4  `pulls_needed_for_agent_alpha`'s 80 -> 8 (the pulls claim's number)
  M5  `bound_at_implemented_params_is_vacuous`'s `> 1/2` -> `> 1/4` (a looser claim)
  M6  `concentration_holds_on_one_point`'s `0` -> `1` (a false statement)
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MATHLIB = "/work/Shopify/audit-work/mathlib"
SRC = os.path.join(HERE, "IDENTIFICATION_BOUND.lean")
WORK = os.path.join(HERE, "_mut_ident.lean")

MUTANTS = [
    ("M1_identification_to_empty",
     "  subst hident\n  rfl",
     "  subst hident\n  ext ω\n  simp [badEvent]"),
    ("M2_hgood_negation_dropped",
     "theorem hgood_is_an_independent_premise :\n    ¬ (∀ (R : Unit → ℝ) (bΔ : ℝ),\n        (∀ ω, ω ∉ (∅ : Set Unit) → R ω ≤ bΔ)) := by\n  intro h\n  have h1 : (1 : ℝ) ≤ 0 := h (fun _ => 1) 0 () (by simp)\n  norm_num at h1",
     "theorem hgood_is_an_independent_premise :\n    (∀ (R : Unit → ℝ) (bΔ : ℝ),\n        (∀ ω, ω ∉ (∅ : Set Unit) → R ω ≤ bΔ)) := by\n  intro R bΔ ω hω\n  simp at hω"),
    ("M3_bound_constant",
     "    1 / (4 * (5 : ℝ) * (1 / 4) ^ 2) = 4 / 5 := by norm_num",
     "    1 / (4 * (5 : ℝ) * (1 / 4) ^ 2) = 1 / 5 := by norm_num"),
    ("M4_pulls_constant",
     "    1 / (4 * r * (1 / 4) ^ 2) ≤ 1 / 20 ↔ 80 ≤ r := by",
     "    1 / (4 * r * (1 / 4) ^ 2) ≤ 1 / 20 ↔ 8 ≤ r := by"),
    ("M5_vacuity_threshold",
     "    (1 : ℝ) / (4 * (5 : ℝ) * (1 / 4) ^ 2) > 1 / 2 := by norm_num",
     "    (1 : ℝ) / (4 * (5 : ℝ) * (1 / 4) ^ 2) > 1 / 4 := by norm_num"),
    ("M6_concentration_false",
     "    (0 : ℝ) ≤ 1 / (4 * (r : ℝ) * ε ^ 2) := by\n  positivity",
     "    (1 : ℝ) ≤ 1 / (4 * (r : ℝ) * ε ^ 2) := by\n  positivity"),
    # ---- added after the first run: statement-level mutants that are genuinely
    # FALSE, so a survivor here would be a real hole rather than a loosening
    ("M7_identification_conclusion_false",
     "    {ω | ε ≤ |contrast ω - ∫ x, contrast x ∂μ|} = badEvent μ X r ε := by",
     "    {ω | ε ≤ |contrast ω - ∫ x, contrast x ∂μ|} = (∅ : Set Ω) := by"),
    ("M8_eighty_pulls_false",
     "    1 / (4 * (80 : ℝ) * (1 / 4) ^ 2) = 1 / 20 := by norm_num",
     "    1 / (4 * (80 : ℝ) * (1 / 4) ^ 2) = 1 / 19 := by norm_num"),
    ("M9_vacuity_false",
     "    (1 : ℝ) / (4 * (5 : ℝ) * (1 / 4) ^ 2) > 1 / 2 := by norm_num",
     "    (1 : ℝ) / (4 * (5 : ℝ) * (1 / 4) ^ 2) > 4 / 5 := by norm_num"),
]


def compile_file(path):
    r = subprocess.run(["lake", "env", "lean", path], cwd=MATHLIB,
                       capture_output=True, text=True, timeout=1800)
    return r.returncode, (r.stdout + r.stderr)


def main():
    src = open(SRC).read()
    rc, out = compile_file(SRC)
    print("BASELINE: exit %d (must be 0)" % rc)
    if rc != 0:
        print(out[:2000])
        return 2

    results = []
    for name, old, new in MUTANTS:
        if old not in src:
            results.append({"mutant": name, "status": "PATTERN_NOT_FOUND"})
            print("%-32s PATTERN NOT FOUND" % name)
            continue
        mut = src.replace(old, new, 1)
        with open(WORK, "w") as f:
            f.write(mut)
        rc, out = compile_file(WORK)
        status = "KILLED" if rc != 0 else "SURVIVOR"
        first = ""
        for line in out.splitlines():
            if "error" in line:
                first = line.strip()[:150]
                break
        results.append({"mutant": name, "status": status, "rc": rc,
                        "first_error": first})
        print("%-32s %-9s rc=%d  %s" % (name, status, rc, first))

    if os.path.exists(WORK):
        os.remove(WORK)
    killed = sum(1 for r in results if r["status"] == "KILLED")
    surv = [r["mutant"] for r in results if r["status"] == "SURVIVOR"]
    summary = {"baseline_rc": 0, "mutants": len(results), "killed": killed,
               "survivors": surv, "results": results}
    with open(os.path.join(HERE, "mutation_identification_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("\nMUTATION CAMPAIGN: %d/%d killed; survivors: %s"
          % (killed, len(results), surv if surv else "none"))
    return 0 if killed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())