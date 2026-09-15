"""run_life_v7b.py -- HELD-OUT-SEED battery for V7B (PREREG_V7B.md H4).

IMPORTS run_life_v7.run (the frozen V7 life logic, byte-identical to the
one that produced results/matrix_v7/) and writes to a SEPARATE directory
results/matrix_v7b/. The frozen matrix is never touched.

Two batteries per seed, both v7_full:
  BA: truth=on,  rich=low, decoy=on   (the C2/C3 life)
  BB: truth=off, rich=low, decoy=on   (pure null: every glow CAUSAL is
                                       a false positive)

Seeds come from the caller (driver_v7b) and are HELD OUT: 10..29, never
used by the campaign (which ran 0..9).

Usage: python3 run_life_v7b.py <seed> [steps]
"""
import json
import os
import sys

from run_life_v7 import run as run_life
from env_terrarium_v7 import pick_edge_action

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "matrix_v7b")
STEPS = 16000


def one(arm, seed, truth, rich, decoy, steps):
    log = run_life(arm, seed, steps, truth, rich, decoy)
    log["battery"] = "BA" if truth else "BB"
    log["held_out"] = True
    tag = f"{arm}_{seed}_{'on' if truth else 'off'}_{rich}_{'on' if decoy else 'off'}"
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, tag + ".json")
    with open(path, "w") as f:
        f.write(json.dumps(log, indent=1))
    return path, log


def main():
    seed = int(sys.argv[1])
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else STEPS
    paths = []
    for truth in (True, False):
        p, log = one("v7_full", seed, truth, "low", True, steps)
        fp = sum(1 for k, v in log["verdicts"].items()
                 if k.endswith("->glow") and v["verdict"] == "CAUSAL")
        paths.append(p)
        print(f"seed {seed} truth={'on ' if truth else 'off'} "
              f"steps={log['steps']} verdicts={len(log['verdicts'])} "
              f"glowCAUSAL={fp} probes={log['probe_trials']}", flush=True)
    print("WROTE", *paths, flush=True)


if __name__ == "__main__":
    main()
