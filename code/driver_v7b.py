"""driver_v7b.py -- HELD-OUT-SEED matrix for V7B (PREREG_V7B.md H4).

Seeds 10..29 (held out; the campaign used 0..9), v7_full, two batteries:
  BA: truth=on  rich=low decoy=on
  BB: truth=off rich=low decoy=on
40 runs, 16000 steps, PYTHONHASHSEED=0, sequential and resumable.
Writes only into results/matrix_v7b/ (the frozen results/matrix_v7/ is
never touched). Prints a per-run line and a final tally of glow-CAUSAL
events (the FP metric).
"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "matrix_v7b")
SEEDS = list(range(10, 510))    # AMENDMENT A1+A2 (PREREG_V7B §3b, §3c):
                               # 10..509, declared before the bulk ran
STEPS = 16000


def path_for(seed, truth):
    return os.path.join(OUT,
                        f"v7_full_{seed}_{'on' if truth else 'off'}_low_on.json")


def main():
    os.makedirs(OUT, exist_ok=True)
    tol = 0
    for seed in SEEDS:
        for truth in (True, False):
            p = path_for(seed, truth)
            if os.path.exists(p) and os.path.getsize(p) > 200:
                tol += 1
                print(f"skip seed {seed} truth={truth}", flush=True)
                continue
            r = subprocess.run([sys.executable, "run_life_v7b.py", str(seed),
                                str(STEPS)], cwd=HERE, capture_output=True,
                               text=True, timeout=1800,
                               env={**os.environ, "PYTHONHASHSEED": "0"})
            ok = os.path.exists(p) and os.path.getsize(p) > 200
            tol += 1
            print(f"[{tol}/40] seed {seed} truth={truth} "
                  f"{'OK' if ok else f'FAIL rc={r.returncode}'}",
                  flush=True)
            if not ok:
                print(r.stdout[-500:], r.stderr[-500:], flush=True)
    # tally
    n_null = 0
    events = []
    for p in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        d = json.load(open(p))
        for k, v in d["verdicts"].items():
            if k.endswith("->glow"):
                n_null += 1
                if v["verdict"] == "CAUSAL":
                    events.append((d["seed"], d["truth"], k, v["p"],
                                   v["rr"], v["target_yes"], v["target_no"],
                                   v["ctrl_yes"], v["ctrl_no"]))
    print(f"HELD-OUT NULL TESTS: {n_null}; "
          f"glow-CAUSAL events: {len(events)}", flush=True)
    for e in events:
        print("  FP:", e, flush=True)
    print("DONE", tol, "/40", flush=True)


if __name__ == "__main__":
    main()
