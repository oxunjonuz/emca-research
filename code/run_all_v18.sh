#!/bin/bash
# run_all_v18.sh -- the whole ENFORCED-SCOPE line in one command (turn 152).
# World oracle -> matrix (resumable) -> analysis -> independent pass -> factcheck.
# Every stage writes to results/ only; no frozen matrix directory is touched.
set -e
cd "$(dirname "$0")"
export PYTHONHASHSEED=0

echo "=== 0/6 frozen-module hashes (v18 reuses v16's arms and v12's world) ==="
sha256sum agent_scope_v16.py agent_safety_v10.py agent_emca_v7.py \
          env_wirehead_v12.py env_terrarium_v7.py

echo "=== 1/6 world oracle (verify_env_enforced_v18.py) ==="
python3 verify_env_enforced_v18.py | tee results/oracle_enforced_v18.txt | tail -3

echo "=== 2/6 matrix (driver_enforced_v18.py, resumable) ==="
python3 driver_enforced_v18.py 2>&1 | tee results/driver_enforced_v18.log | tail -3

echo "=== 3/6 analysis (analyze_enforced_v18.py) ==="
python3 analyze_enforced_v18.py | tee results/analyze_enforced_v18.txt | tail -22

echo "=== 4/6 independent pass (verify_enforced_v18_independent.py) ==="
python3 verify_enforced_v18_independent.py | tee results/verify_enforced_v18_independent.txt | tail -3

echo "=== 5/6 factcheck (factcheck_enforced_v18.py) ==="
python3 factcheck_enforced_v18.py | tee results/factcheck_enforced_v18.txt | tail -3

echo "=== 6/6 frozen files and matrices intact ==="
for d in results/matrix_v7 results/matrix_safety_v10 results/matrix_wirehead_v11 \
         results/matrix_wirehead_v12 results/matrix_ledger_v13 \
         results/matrix_attested_v14 results/matrix_v15 results/matrix_scope_v16 \
         results/matrix_bribed_v17; do
  echo -n "$d: "; ls "$d"/*.json 2>/dev/null | wc -l
done

echo "ALL GREEN"