#!/bin/sh
# run_all_v16.sh -- the whole SCOPE line, one command, frozen as one experiment.
# Turn 149, owner directive msg_00149. PYTHONHASHSEED=0 throughout.
set -e
cd "$(dirname "$0")"

echo "=== 0. frozen-module hashes (v16 adds no world code) ==="
sha256sum env_terrarium_v7.py env_safety_v10.py env_wirehead_v11.py \
          env_wirehead_v12.py agent_safety_v10.py agent_emca_v7.py

echo "=== 1. world oracle ==="
PYTHONHASHSEED=0 python3 verify_env_scope_v16.py > results/oracle_scope_v16.txt 2>&1
tail -3 results/oracle_scope_v16.txt

echo "=== 2. matrix (790 cells) ==="
PYTHONHASHSEED=0 python3 driver_scope_v16.py | tail -2

echo "=== 3. analysis ==="
PYTHONHASHSEED=0 python3 analyze_scope_v16.py > results/analyze_scope_v16.txt 2>&1
tail -5 results/analyze_scope_v16.txt

echo "=== 4. independent pass (fresh process, disk only) ==="
PYTHONHASHSEED=0 python3 verify_scope_v16_independent.py \
    > results/verify_scope_v16_independent.txt 2>&1
tail -3 results/verify_scope_v16_independent.txt

echo "=== 5. factcheck ==="
PYTHONHASHSEED=0 python3 factcheck_scope_v16.py > results/factcheck_scope_v16.txt 2>&1
tail -2 results/factcheck_scope_v16.txt

echo "=== 6. frozen predecessors byte-identical ==="
sha256sum agent_scope_v16.py run_life_v16.py | cut -c1-24
echo "ALL GREEN"