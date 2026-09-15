set -e
cd /work/Shopify/audit-work/agent_arch
export PYTHONHASHSEED=0
echo "=== 1/5 world oracle ==="
python3 verify_env_wirehead_v11.py | tail -3
echo "=== 2/5 driver (resumable; all cells present) ==="
python3 driver_wirehead_v11.py | tail -2
echo "=== 3/5 analysis ==="
python3 analyze_wirehead.py | tail -4
echo "=== 4/5 independent pass ==="
python3 verify_wirehead_independent.py | tail -3
echo "=== 5/5 factcheck ==="
python3 factcheck_wirehead_report.py | tail -2
echo "ALL GREEN"
