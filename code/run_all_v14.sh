#!/bin/bash
# run_all_v14.sh -- the whole v14 "ATTESTED" line in one command (turn 145).
# World oracle -> matrix (resumable) -> analysis -> independent pass -> factcheck.
# Every stage writes to results/ only; no frozen matrix directory is touched.
set -e
cd "$(dirname "$0")"
export PYTHONHASHSEED=0

echo "=== 1/6 world oracle (verify_env_attested_v14.py) ==="
python3 verify_env_attested_v14.py | tee results/oracle_attested_v14.txt | tail -3

echo "=== 2/6 matrix (driver_attested_v14.py, resumable) ==="
python3 driver_attested_v14.py 2>&1 | tee results/driver_attested_v14.log | tail -3

echo "=== 3/6 analysis (analyze_attested_v14.py) ==="
python3 analyze_attested_v14.py | tee results/analyze_attested_v14.txt | tail -14

echo "=== 4/6 independent pass (verify_attested_v14_independent.py) ==="
python3 verify_attested_v14_independent.py | tee results/verify_attested_v14_independent.txt | tail -3

echo "=== 5/6 factcheck (factcheck_attested_v14.py) ==="
python3 factcheck_attested_v14.py | tee results/factcheck_attested_v14.txt | tail -3

echo "=== 6/6 frozen files and matrices intact ==="
sha256sum env_terrarium_v7.py agent_emca_v7.py candidate_gen.py arbitration.py \
          env_safety_v10.py agent_safety_v10.py env_wirehead_v11.py \
          agent_wirehead_v11.py env_wirehead_v12.py agent_wirehead_v12.py \
          run_life_v12.py env_ledger_v13.py agent_ledger_v13.py run_life_v13.py \
  | tee results/frozen_hashes_v14.txt
for d in results/matrix_v7 results/matrix_ledger_v13 results/matrix_safety_v10; do
  echo -n "$d: "; ls "$d"/*.json 2>/dev/null | wc -l
done

echo "ALL GREEN"
