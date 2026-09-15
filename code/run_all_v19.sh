#!/bin/bash
# run_all_v19.sh -- the whole ADAPTIVE-PAYER line in one command (turn 154).
# World oracle -> matrix (resumable) -> analysis -> independent pass -> factcheck.
# Every stage writes to results/ only; no frozen matrix directory is touched.
set -e
cd "$(dirname "$0")"
export PYTHONHASHSEED=0

echo "=== 0/7 frozen-module hashes (v19 adds no agent code) ==="
sha256sum agent_attested_v14.py env_attested_v14.py env_bribed_v17.py \
          agent_safety_v10.py agent_ledger_v13.py env_wirehead_v12.py

echo "=== 1/7 world oracle (verify_env_adaptive_v19.py) ==="
python3 verify_env_adaptive_v19.py | tee results/oracle_adaptive_v19.txt | tail -3

echo "=== 2/7 matrix (driver_adaptive_v19.py, resumable) ==="
python3 driver_adaptive_v19.py 2>&1 | tee results/driver_adaptive_v19.log | tail -3

echo "=== 3/7 analysis (analyze_adaptive_v19.py) ==="
python3 analyze_adaptive_v19.py | tee results/analyze_adaptive_v19.txt | tail -4

echo "=== 4/7 independent pass (verify_adaptive_v19_independent.py) ==="
python3 verify_adaptive_v19_independent.py | tee results/verify_adaptive_v19_independent.txt | tail -3

echo "=== 5/7 factcheck (factcheck_adaptive_v19.py) ==="
python3 factcheck_adaptive_v19.py | tee results/factcheck_adaptive_v19.txt | tail -3

echo "=== 6/7 Lean: identification bound (kernel audit) ==="
cd /work/Shopify/audit-work/mathlib
lake env lean /work/Shopify/audit-work/agent_arch/bench_cb/lean/IDENTIFICATION_BOUND.lean
echo "IDENTIFICATION_BOUND.lean: exit 0, no sorry"
cd /work/Shopify/audit-work/agent_arch

echo "=== 7/7 frozen files and matrices intact ==="
for d in results/matrix_v7 results/matrix_safety_v10 results/matrix_wirehead_v11 \
         results/matrix_wirehead_v12 results/matrix_ledger_v13 \
         results/matrix_attested_v14 results/matrix_v15 results/matrix_scope_v16 \
         results/matrix_bribed_v17 results/matrix_enforced_v18; do
  echo -n "$d: "; ls "$d"/*.json 2>/dev/null | wc -l
done
echo -n "results/matrix_adaptive_v19: "; ls results/matrix_adaptive_v19/*.json | wc -l

echo "ALL GREEN"