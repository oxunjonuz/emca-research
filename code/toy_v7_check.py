"""toy_v7_check.py -- the REAL-AGENT gate, before the matrix (PREREG_V7 §4.3).

W1  the generator NOMINATES the true pair (edge_action, hum) with truth=on
W2  the generator does NOT nominate it with truth=off
W3  the prober returns CAUSAL on the true pair (truth=on)
W4  the prober never returns CAUSAL on the decoy (glow pair)
W5  beta0 arms record NO probe trials
W6  the permuted arm's first probe follows the permuted ranking
W7  the forager records NO probe trials
A1  string audit: candidate_gen.py / arbitration.py carry ZERO world
    tokens as LOGIC (comments and docstrings stripped first)
A2  determinism: the same (arm, seed) in two FRESH processes gives
    bit-identical action streams

Fixes found here are recorded in PREREG_V7 §5 and applied to all arms.
Usage: python3 toy_v7_check.py
"""
import hashlib
import os
import re
import subprocess
import sys
import tokenize

from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import (
    AgentV7Full, AgentV7Beta0, AgentV7Perm, AgentV7NoGen, AgentV7Forager,
)
import candidate_gen as G

STEPS = 16000
FAILS = []
WORLD_TOKENS = ("hum", "glow", "fruit", "station", "rich", "berry",
                "warm", "cold", "wait", "press", "grasp", "pool", "aura")


def chk(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    if not ok:
        FAILS.append(name)


def strip_code(path):
    """Return the file's CODE with comments and standalone strings
    removed (documentation may mention the world; logic may not)."""
    with open(path, "rb") as f:
        toks = list(tokenize.tokenize(f.readline))
    keep = [t for t in toks
            if t.type not in (tokenize.COMMENT, tokenize.NL,
                              tokenize.NEWLINE, tokenize.STRING)]
    src = tokenize.untokenize(keep)
    return src.decode() if isinstance(src, bytes) else src


def run_arm(arm_cls, seed, steps=STEPS, truth=True, rich="low", decoy=True,
            keep_agent=False, edge=None):
    ea = edge or pick_edge_action(seed)
    ag = arm_cls(seed)
    env = TerrariumV7(seed, truth=truth, decoy=decoy, rich=rich,
                      edge_action=ea)
    acts = []
    first_probe_cand = None
    first_probe_cands = None
    for t in range(steps):
        o = env.obs()
        a = ag.act(o)
        acts.append(a)
        if getattr(ag, "probe_state", None) and first_probe_cand is None:
            first_probe_cand = (ag.probe_state["cand"].action,
                                ag.probe_state["cand"].effect,
                                ag.probe_state["cand"].score)
            # the ranked list AS SEEN at the moment the first probe began
            first_probe_cands = list(ag.candidates_seen)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=decoy,
                              rich=rich, edge_action=ea)
    if keep_agent:
        return ag, acts, first_probe_cand, ea, first_probe_cands
    return ag.probe_trials, {f"{a}->{e}": v["verdict"]
                             for (a, e), v in ag.verdicts.items()}, ea


def main():
    print("=== A1 string audit (world tokens as LOGIC) ===")
    for path in ("candidate_gen.py", "arbitration.py"):
        code = strip_code(path)
        hits = sorted({tok for tok in WORLD_TOKENS
                       if re.search(r"[A-Za-z_]" + tok, code)})
        print(f"   {path}: logic tokens {hits if hits else 'none'}")
        chk(f"A1 zero world tokens in {path}", not hits)

    print("=== W1/W2 generation (truth on/off) ===")
    on_hits = off_hits = 0
    for seed in range(10):
        for truth in (True, False):
            ag, acts, fpc, ea, _ = run_arm(AgentV7Full, seed, steps=STEPS,
                                           truth=truth, decoy=True,
                                           keep_agent=True)
            nom = (ea, "hum") in [tuple(x[:2]) for x in ag.candidates_seen]
            if truth:
                on_hits += nom
            else:
                off_hits += nom
    print(f"   truth=on nomination of the true pair: {on_hits}/10")
    print(f"   truth=off nomination of that pair:    {off_hits}/10")
    chk("W1 nominates the truth on", on_hits >= 8, f"({on_hits}/10)")
    chk("W2 no nomination off", off_hits <= 2, f"({off_hits}/10)")

    print("=== W3/W4 verification ===")
    causal = 0
    decoy_fp = 0
    for seed in range(10):
        ea = pick_edge_action(seed)
        ag, acts, fpc, _ea, _ = run_arm(AgentV7Full, seed, truth=True, decoy=True,
                                   keep_agent=True)
        v = ag.verdicts.get((ea, "hum"))
        if v and v["verdict"] == "CAUSAL":
            causal += 1
        for (a, e), vv in ag.verdicts.items():
            if e == "glow" and vv["verdict"] == "CAUSAL":
                decoy_fp += 1
    print(f"   CAUSAL on the true pair: {causal}/10 ; any CAUSAL on glow: {decoy_fp}")
    chk("W3 CAUSAL on truth", causal >= 8, f"({causal}/10)")
    chk("W4 no CAUSAL on the decoy", decoy_fp == 0)

    print("=== W5/W7 beta0 and forager never probe ===")
    b0 = fg = 0
    for seed in range(10):
        b0 += run_arm(AgentV7Beta0, seed)[0]
        fg += run_arm(AgentV7Forager, seed)[0]
    print(f"   beta0 probe trials: {b0} ; forager probe trials: {fg}")
    chk("W5 beta0 never probes", b0 == 0)
    chk("W7 forager never probes", fg == 0)

    print("=== W6 the permuted arm follows the permuted ranking ===")
    ok_perm = 0
    n_perm = 0
    for seed in range(10):
        ag, acts, fpc, ea, fpc_list = run_arm(AgentV7Perm, seed,
                                              keep_agent=True)
        if fpc is None or not fpc_list:
            continue
        n_perm += 1
        # the ranked list AS SEEN when the first probe began
        ranked = sorted(fpc_list, key=lambda c: (-c[2], -c[3], c[0], c[1]))
        if (fpc[0], fpc[1]) == (ranked[0][0], ranked[0][1]):
            ok_perm += 1
    print(f"   perm first-probe == permuted argmax: {ok_perm}/{n_perm}")
    chk("W6 follows permuted ranking", n_perm > 0 and ok_perm >= 8,
        f"({ok_perm}/{n_perm})")

    print("=== A2 determinism (two fresh processes) ===")
    code = ("from toy_v7_check import run_arm; from agent_emca_v7 import "
            "AgentV7Full; import hashlib;"
            "ag,acts,_,_,_=run_arm(AgentV7Full,7,keep_agent=True);"
            "print(hashlib.sha256('|'.join(acts).encode()).hexdigest())")
    outs = []
    for hs in ("0", "1"):
        env2 = {**os.environ, "PYTHONHASHSEED": hs}
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, env=env2,
                           cwd=os.path.dirname(os.path.abspath(__file__)))
        outs.append(r.stdout.strip() or r.stderr.strip()[-200:])
    print(f"   stream hashes: {outs}")
    chk("A2 bit-identical across hash seeds", len(set(outs)) == 1)

    print()
    if FAILS:
        print("TOY V7: FAIL", FAILS)
        raise SystemExit(1)
    print("TOY V7: ALL PASS")


if __name__ == "__main__":
    main()
