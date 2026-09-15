set -e
cd /work/Shopify/audit-work/agent_arch
export PYTHONHASHSEED=0
echo "=== 1/6 world oracle ==="
python3 verify_env_wirehead_v12.py | tail -2
echo "=== 2/6 driver (resumable; all cells present) ==="
python3 driver_wirehead_v12.py | tail -1
echo "=== 3/6 analysis ==="
python3 analyze_wirehead_v12.py | tail -2
echo "=== 4/6 crossing diagnostic ==="
python3 diag_v12_crossing.py | tail -1
echo "=== 5/6 independent pass ==="
python3 verify_wirehead_v12_independent.py | tail -2
echo "=== 6/6 factcheck ==="
python3 factcheck_v12_report.py | tail -2
echo "ALL GREEN"
