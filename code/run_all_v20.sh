#!/bin/bash
# run_all_v20.sh -- the whole BRIBED-ENFORCER line in one command (turn 157).
# World oracle -> matrix (resumable) -> analysis -> independent pass -> factcheck
# -> replication on 30 fresh seeds -> replication analysis.
# Every stage writes to results/ only; no frozen matrix directory is touched.
set -e
cd "$(dirname "$0")"
export PYTHONHASHSEED=0

echo "=== 0/7 frozen-module hashes (v20 adds no agent code) ==="
sha256sum agent_safety_v10.py agent_scope_v16.py agent_enforced_v18.py \
          env_enforced_v18.py

echo "=== 1/7 world oracle (verify_env_bribed_enforcer_v20.py) ==="
python3 verify_env_bribed_enforcer_v20.py | tee results/oracle_bribed_enforcer_v20.txt | tail -3

echo "=== 2/7 matrix (driver_bribed_enforcer_v20.py, resumable) ==="
python3 driver_bribed_enforcer_v20.py 2>&1 | tee results/driver_bribed_enforcer_v20.log | tail -3

echo "=== 3/7 analysis (analyze_bribed_enforcer_v20.py) ==="
python3 analyze_bribed_enforcer_v20.py | tee results/analyze_bribed_enforcer_v20.txt | tail -6

echo "=== 4/7 independent pass (verify_bribed_enforcer_v20_independent.py) ==="
python3 verify_bribed_enforcer_v20_independent.py | tee results/verify_bribed_enforcer_v20_independent.txt | tail -3

echo "=== 5/7 factcheck (factcheck_bribed_enforcer_v20.py) ==="
python3 factcheck_bribed_enforcer_v20.py | tee results/factcheck_bribed_enforcer_v20.txt | tail -3

echo "=== 6/7 replication on 30 fresh seeds (driver_v20_replication.py) ==="
python3 driver_v20_replication.py 2>&1 | tee results/driver_v20_replication.log | tail -3
python3 analyze_v20_replication.py | tee results/analyze_v20_replication.txt | tail -8

echo "=== 7/7 frozen files and matrices intact ==="
for d in results/matrix_v7 results/matrix_safety_v10 results/matrix_wirehead_v11 \
         results/matrix_wirehead_v12 results/matrix_ledger_v13 \
         results/matrix_attested_v14 results/matrix_v15 results/matrix_scope_v16 \
         results/matrix_bribed_v17 results/matrix_enforced_v18 \
         results/matrix_adaptive_v19; do
  echo -n "$d: "; ls "$d"/*.json 2>/dev/null | wc -l
done
echo -n "results/matrix_bribed_enforcer_v20: "; ls results/matrix_bribed_enforcer_v20/*.json | wc -l
echo -n "results/matrix_v20_replication: "; ls results/matrix_v20_replication/*.json | wc -l

echo "ALL GREEN"