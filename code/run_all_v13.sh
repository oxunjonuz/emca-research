#!/bin/bash
# run_all_v13.sh -- the whole v13 "LEDGER" line in one command (turn 143/144).
# World oracle -> matrix (resumable) -> analysis -> independent pass.
# Every stage writes to results/ only; no frozen matrix directory is touched.
set -e
cd "$(dirname "$0")"
export PYTHONHASHSEED=0

echo "=== 1/4 world oracle (verify_env_ledger_v13.py) ==="
python3 verify_env_ledger_v13.py | tee results/oracle_ledger_v13.txt | tail -3

echo "=== 2/4 matrix (driver_ledger_v13.py, resumable) ==="
python3 driver_ledger_v13.py 2>&1 | tee results/driver_ledger_v13.log | tail -3

echo "=== 3/4 analysis (analyze_ledger_v13.py) ==="
python3 analyze_ledger_v13.py | tee results/analyze_ledger_v13.txt | tail -20

echo "=== 4/4 independent pass (verify_ledger_v13_independent.py) ==="
python3 verify_ledger_v13_independent.py | tee results/verify_ledger_v13_independent.txt | tail -3

echo "=== drain-lag evidence re-measure (diag_ledger_lag_v13.py) ==="
python3 diag_ledger_lag_v13.py | tee results/diag_ledger_lag_v13.txt | tail -8

echo "=== factcheck (factcheck_ledger_v13.py) ==="
python3 factcheck_ledger_v13.py | tee results/factcheck_ledger_v13.txt | tail -5

echo "ALL GREEN"
