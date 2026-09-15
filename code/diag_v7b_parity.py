"""diag_v7b_parity.py -- WHY do probe verdicts occasionally fire on a
pair that carries no causal information?

The frozen rule's per-test false-positive rate at n=200/arm is 0.488%
(exact enumeration, PREREG_V7B H3), yet the held-out battery produced
2 events in 109 null tests (1.83%) and the frozen matrix produced 1
(seed 8). The scripted replica (same 5/5 alternation, no agent) produced
0/400 and 0/160.

Hypothesis under test: the world draws hum and glow from ONE random
stream; the agent's probe splits its steps into alternating blocks of 5.
If that alternation pins the target and control arms to DRAW POSITIONS of
fixed parity, then the two arms are not two iid Bernoulli samples: they
are two interleaved slices of one stream, and any fine structure in the
stream (or in the phase/draw-count bookkeeping) becomes an arm
difference. This is measurable and it is a HARNESS property, not a world
claim: nothing about hum/glow/actions is assumed.

Measurement, per seed, on the REAL agent:
  * wrap env.rng, so every random() call is counted;
  * at every step record the arm the probe scored (target/control/none),
    the phase, and the index (and parity) of the glow draw;
  * report the parity distribution by arm, and the glow rate by arm
    crossed with parity.
If parity is arm-determined and the rate depends on parity, the FP is an
interleaving artifact. If parity is mixed within each arm, it is not.

Usage: python3 diag_v7b_parity.py <seed> [steps] [truth]
"""
import json
import sys
from collections import defaultdict

from env_terrarium_v7 import TerrariumV7, pick_edge_action
import run_life_v7 as R


class CountingRNG:
    """Proxy over the world RNG: counts calls, records the last index."""

    def __init__(self, rng):
        self._rng = rng
        self.n = 0
        self.last_index = None

    def random(self):
        self.last_index = self.n
        v = self._rng.random()
        self.n += 1
        return v

    def __getattr__(self, k):
        return getattr(self._rng, k)


def probe(seed, steps=16000, truth=True):
    from agent_emca_v7 import AgentV7Full
    edge = pick_edge_action(seed)
    agent = AgentV7Full(seed)
    env = TerrariumV7(seed, truth=truth, decoy=True, rich="low",
                      edge_action=edge)
    crng = CountingRNG(env.rng)
    env.rng = crng
    recs = []
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        mark = getattr(agent, "_probe_mark", None)
        start_idx = crng.n
        if a not in o["afford"]:
            a = "wait" if "wait" in o["afford"] else o["afford"][0]
        o2, r, done, info = env.step(a)
        recs.append(dict(t=t, phase=o["phase"], arm=(mark[0] if mark else None),
                         act=(mark[1] if mark else None),
                         glow=bool(info.get("glow")), hum=bool(info.get("hum")),
                         draws=crng.n - start_idx,
                         glow_idx=(crng.n - 1 if info.get("glow") else None)))
        agent.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=True,
                              rich="low", edge_action=edge)
            env.rng = crng
    return recs, agent


def main():
    seed = int(sys.argv[1])
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 16000
    truth = (sys.argv[3] != "off") if len(sys.argv) > 3 else True
    recs, agent = probe(seed, steps, truth)
    scored = [r for r in recs if r["arm"] in ("target", "ctrl")
              and r["glow_idx"] is not None]
    print(f"=== seed {seed} truth={truth} steps={steps} ===")
    print(f"  scored steps that produced a glow draw: {len(scored)}")
    by = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in scored:
        by[r["arm"]][r["glow_idx"] % 2][0 if r["glow"] else 1] += 1
        by[r["arm"]][r["glow_idx"] % 2][0] += 0  # keep shape
    # recompute cleanly
    cnt = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # arm,par -> [glow, n]
    for r in scored:
        c = cnt[r["arm"]][r["glow_idx"] % 2]
        c[0] += 1 if r["glow"] else 0
        c[1] += 1
    print("  arm x draw-index parity -> glow rate:")
    for arm in ("target", "ctrl"):
        for par in (0, 1):
            g, n = cnt[arm][par]
            print(f"    {arm:6s} parity {par}: {g}/{n} = "
                  f"{(g/n if n else 0):.3f}")
    print("  arm totals:")
    for arm in ("target", "ctrl"):
        g = sum(cnt[arm][p][0] for p in (0, 1))
        n = sum(cnt[arm][p][1] for p in (0, 1))
        print(f"    {arm:6s}: {g}/{n} = {(g/n if n else 0):.4f}")
    # is parity arm-determined?
    print("  parity share within each arm (a constant-parity arm would be "
          "0.00/1.00):")
    for arm in ("target", "ctrl"):
        n_tot = sum(cnt[arm][p][1] for p in (0, 1))
        for par in (0, 1):
            print(f"    {arm:6s} parity {par}: "
                  f"{100*cnt[arm][par][1]/n_tot if n_tot else 0:.1f}%")
    print("  verdicts on disk for this run:")
    for k, v in sorted(agent.verdicts.items()):
        print(f"    {k[0]}->{k[1]}: {v['verdict']} p={v['p']} rr={v['rr']} "
              f"{v['target_yes']}/{v['target_no']} vs "
              f"{v['ctrl_yes']}/{v['ctrl_no']}")


if __name__ == "__main__":
    main()
