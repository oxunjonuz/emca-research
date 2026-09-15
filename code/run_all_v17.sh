#!/bin/bash
# run_all_v17.sh -- the whole BRIBED-AUDITOR line in one command (turn 152).
# World oracle -> matrix (resumable) -> analysis -> independent pass -> factcheck.
# Every stage writes to results/ only; no frozen matrix directory is touched.
set -e
cd "$(dirname "$0")"
export PYTHONHASHSEED=0

echo "=== 0/6 frozen-module hashes (v17 adds no agent code) ==="
sha256sum agent_attested_v14.py env_attested_v14.py agent_safety_v10.py \
          agent_scope_v16.py env_wirehead_v12.py

echo "=== 1/6 world oracle (verify_env_bribed_v17.py) ==="
python3 verify_env_bribed_v17.py | tee results/oracle_bribed_v17.txt | tail -3

echo "=== 2/6 matrix (driver_bribed_v17.py, resumable) ==="
python3 driver_bribed_v17.py 2>&1 | tee results/driver_bribed_v17.log | tail -3

echo "=== 3/6 analysis (analyze_bribed_v17.py) ==="
python3 analyze_bribed_v17.py | tee results/analyze_bribed_v17.txt | tail -14

echo "=== 4/6 independent pass (verify_bribed_v17_independent.py) ==="
python3 verify_bribed_v17_independent.py | tee results/verify_bribed_v17_independent.txt | tail -3

echo "=== 5/6 factcheck (factcheck_bribed_v17.py) ==="
python3 factcheck_bribed_v17.py | tee results/factcheck_bribed_v17.txt | tail -3

echo "=== 6/6 frozen files and matrices intact ==="
for d in results/matrix_v7 results/matrix_safety_v10 results/matrix_wirehead_v11 \
         results/matrix_wirehead_v12 results/matrix_ledger_v13 \
         results/matrix_attested_v14 results/matrix_v15 results/matrix_scope_v16; do
  echo -n "$d: "; ls "$d"/*.json 2>/dev/null | wc -l
done

echo "ALL GREEN"