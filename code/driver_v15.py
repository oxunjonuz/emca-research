"""driver_v15.py -- the v15 matrix.

Arms x seeds x regimes, all through run_life_v15.run. No reward, no
energy, no death anywhere. Writes one JSON per cell under
results/matrix_v15/.
"""
import json
import os
import sys

from run_life_v15 import run

ARMS = [
    # name, mode, kwargs
    ("rand", "rand", {}),
    ("naive_info", "naive_info", {}),
    ("confirm", "confirm", {}),
    ("ig_pooled", "ig_pooled", {}),
    ("ig_ctx", "ig_ctx", {}),
    ("ig_relevant", "ig_relevant", {}),
    ("ig_ctx_oracle", "ig_ctx", {"oracle": True}),
]

REGIMES = {
    "base": {"decoy": False},
    "decoy": {"decoy": True},
    "tv": {"tv": True},
}

SEEDS = list(range(10))
STEPS = 16000


def main():
    outdir = os.path.join("results", "matrix_v15")
    os.makedirs(outdir, exist_ok=True)
    n = 0
    fails = 0
    for regime, rkw in REGIMES.items():
        for arm, mode, akw in ARMS:
            for seed in SEEDS:
                name = f"{arm}_{regime}_s{seed}.json"
                path = os.path.join(outdir, name)
                try:
                    res = run(seed, mode, steps=STEPS,
                              model_seed=seed, **rkw, **akw)
                except Exception as e:  # noqa
                    fails += 1
                    print(f"FAIL {name}: {type(e).__name__}: {e}")
                    continue
                with open(path, "w") as fh:
                    json.dump(res, fh, sort_keys=True)
                n += 1
    print(f"wrote {n} cells, {fails} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())