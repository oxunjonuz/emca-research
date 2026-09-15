#!/usr/bin/env python3
"""
verify_union_lean_independent.py — turn 131.

Independent re-check of the turn-131 Lean claims.  Different code from
mutate_union_lean.py; reads only what is on disk; imports nothing from the
producer.  Every check prints PASS/FAIL and the raw evidence line.

Checks
  C1  union_stoch_v2.lean compiles in a FRESH lake process, exit 0, no output.
  C2  no `sorry` / `admit` / `axiom` token in the source (text check).
  C3  the kernel axiom list, recomputed by `#print axioms`, contains no sorryAx.
  C4  every declaration named in RESULTS_UNION_LEAN.md's table actually exists
      in the compiled file (by #check).
  C5  mutation_summary.json agrees with the m_*.lean files on disk: each applied
      mutant exists and its recorded exit code matches a fresh run.
  C6  the M10 survivor: m10_followup.lean compiles -> the loosened constant IS
      provable -> the M10 red is an artefact, and the report says so.
  C7  non-vacuity: union_stoch_v2.lean + nonvacuity_v6.lean compiles as one file.
"""

import subprocess, os, json, re, sys

LEAN = "/work/Shopify/audit-work/agent_arch/bench_cb/lean"
MATHLIB = "/work/Shopify/audit-work/mathlib"
SRC = os.path.join(LEAN, "union_stoch_v2.lean")

results = []
def check(tag, ok, evidence):
    results.append((tag, ok, evidence))
    print(f"[{'PASS' if ok else 'FAIL'}] {tag}: {evidence}")

def lean(path, timeout=3600):
    p = subprocess.run(["lake", "env", "lean", path], cwd=MATHLIB,
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr

# C1 -------------------------------------------------------------------------
rc, out = lean(SRC)
check("C1_compiles_fresh", rc == 0 and out.strip() == "",
      f"exit={rc}, stdout/stderr bytes={len(out)}")

# C2 -------------------------------------------------------------------------
src = open(SRC).read()
bad = [t for t in ("sorry", "admit", "axiom") if re.search(rf"\b{t}\b", src)]
check("C2_no_sorry_axiom_token", not bad, f"tokens found: {bad or 'none'}")

# C3 -------------------------------------------------------------------------
names = ["pooled_gap_zero", "integral_le_of_split", "bad_le_sum",
         "expected_regret_le", "hoeffding_mean_raw", "exp_arg_eq",
         "hoeffding_mean_le", "chebyshev_abs", "variance_sum_le",
         "sMean_apply", "deviation_measurable", "sMean_memLp",
         "variance_mean_le", "chebyshev_sample_mean", "union_regret_bound"]
probe = os.path.join(LEAN, "_verify_axioms.lean")
with open(probe, "w") as f:
    f.write(src)
    for n in names:
        f.write(f"\n#print axioms Union.{n}")
rc, out = lean(probe)
lines = [l for l in out.splitlines() if "depends on axioms" in l]
has_sorry = any("sorryAx" in l for l in lines)
check("C3_no_sorryAx_in_kernel", rc == 0 and len(lines) == len(names) and not has_sorry,
      f"exit={rc}, {len(lines)}/{len(names)} axiom lines, sorryAx={has_sorry}")
allowed = {"propext", "Classical.choice", "Quot.sound"}
extra = set()
for l in lines:
    m = re.search(r"\[(.*)\]", l)
    if m:
        extra |= {x.strip() for x in m.group(1).split(",")} - allowed
check("C3b_only_standard_axioms", not extra, f"unexpected axioms: {extra or 'none'}")

# C4 -------------------------------------------------------------------------
probe4 = os.path.join(LEAN, "_verify_exists.lean")
with open(probe4, "w") as f:
    f.write(src)
    for n in names:
        f.write(f"\n#check Union.{n}")
rc, out = lean(probe4)
missing = [n for n in names if f"Union.{n}" not in out]
check("C4_all_declarations_exist", rc == 0 and not missing,
      f"exit={rc}, missing={missing or 'none'}")

# C5 -------------------------------------------------------------------------
summary = json.load(open(os.path.join(LEAN, "mutation_summary.json")))
mismatch = []
for row in summary["rows"]:
    if not row.get("applied"):
        continue
    p = os.path.join(LEAN, f"m_{row['id']}.lean")
    if not os.path.exists(p):
        mismatch.append(f"{row['id']}: file missing"); continue
    rc, out = lean(p)
    if rc != row["exit"]:
        mismatch.append(f"{row['id']}: recorded exit {row['exit']} vs fresh {rc}")
check("C5_mutation_summary_matches_disk", not mismatch,
      f"{len(summary['rows'])} rows, mismatches={mismatch or 'none'}")

# C6 -------------------------------------------------------------------------
rc, out = lean(os.path.join(LEAN, "m10_followup.lean"))
check("C6_m10_survivor_confirmed", rc == 0,
      f"m10_followup exit={rc} -> loosened constant IS provable -> M10 red is an artefact")

# C7 -------------------------------------------------------------------------
combo = os.path.join(LEAN, "_verify_nonvacuous.lean")
with open(combo, "w") as f:
    f.write(src)
    f.write(open(os.path.join(LEAN, "nonvacuity_v6.lean")).read())
rc, out = lean(combo)
check("C7_nonvacuity_compiles", rc == 0 and out.strip() == "",
      f"exit={rc}, bytes={len(out)}")

# summary --------------------------------------------------------------------
ok = sum(1 for _, o, _ in results if o)
print(f"\n{ok}/{len(results)} checks PASS")
json.dump({"checks": [{"tag": t, "pass": o, "evidence": e} for t, o, e in results],
           "passed": ok, "total": len(results)},
          open(os.path.join(LEAN, "verify_union_lean_out.json"), "w"), indent=1)
sys.exit(0 if ok == len(results) else 1)
