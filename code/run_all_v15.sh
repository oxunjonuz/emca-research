#!/usr/bin/env bash
# run_all_v15.sh -- the whole v15 line in one command, ALL GREEN or fail.
set -u
cd "$(dirname "$0")"
export PYTHONHASHSEED=0
FAIL=0

echo "=== 1. world oracle ==="
python3 verify_env_v15.py | tee results/oracle_v15.txt || FAIL=1
grep -q "0 failures" results/oracle_v15.txt || FAIL=1

echo "=== 2. drive the matrix (210 cells) ==="
rm -rf results/matrix_v15
python3 driver_v15.py | tee results/driver_v15.log || FAIL=1
N=$(ls results/matrix_v15 | wc -l | tr -d ' ')
echo "cells: $N"
[ "$N" = "210" ] || FAIL=1

echo "=== 3. analyze ==="
python3 analyze_v15.py | tee results/analyze_v15.txt || FAIL=1

echo "=== 4. independent pass (fresh process, disk only) ==="
python3 verify_v15_independent.py | tee results/verify_v15_independent.txt || FAIL=1

echo "=== 5. determinism (two fresh processes) ==="
python3 - <<'EOF' > /tmp/v15_det1.txt
import json, hashlib
from run_life_v15 import run
r = run(3, "ig_ctx", steps=16000, decoy=True, model_seed=3)
print(hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest())
EOF
python3 - <<'EOF' > /tmp/v15_det2.txt
import json, hashlib
from run_life_v15 import run
r = run(3, "ig_ctx", steps=16000, decoy=True, model_seed=3)
print(hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest())
EOF
if diff -q /tmp/v15_det1.txt /tmp/v15_det2.txt >/dev/null; then
  echo "determinism: byte-identical ($(cat /tmp/v15_det1.txt | cut -c1-16))"
else
  echo "determinism: MISMATCH"; FAIL=1
fi

echo "=== 6. factcheck ==="
python3 factcheck_v15.py | tee results/factcheck_v15.txt || FAIL=1

if [ "$FAIL" = "0" ]; then
  echo "=== ALL GREEN ==="
else
  echo "=== RED ==="
fi
exit $FAIL