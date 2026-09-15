#!/usr/bin/env python3
"""Regression check for the S7 identifier fix (necessity/specificity):
does EMCA_SpecContrast keep the edges the ORIGINAL terrarium matrix (turn 93)
relied on -- press->lever (rare effect, E1) and eat->ate -- and does it drop
the vantage artifacts (up/left/right->door_gone)?

Real agent (act+observe), original Terrarium, 3 seeds x 6000 steps,
default EMCA vs EMCA_SpecContrast (spec_cap=0.10). No env changes.
Criteria fixed before the run:
  R1 press->lever present in spec edges in >=2/3 seeds
  R2 eat->ate present in spec edges in >=2/3 seeds
  R3 vantage edges (move->door_gone) ABSENT from spec edges in >=2/3 seeds
  (R3 is a prediction, not a requirement: vantage artifacts were known noise)
"""
from env_terrarium import run_episode
from agent_emca import EMCA
from sanity_v2_confounder import EMCA_SpecContrast

VANTAGE = [("up", "door_gone"), ("down", "door_gone"),
           ("left", "door_gone"), ("right", "door_gone")]


def fmt(d):
    return "{%s}" % ", ".join(f"{a}->{e}:{p}" for (a, e), p in sorted(d.items()))


for cls, name in ((EMCA, "default"), (EMCA_SpecContrast, "spec(S7)")):
    print(f"\n=== {name} identifier, original Terrarium, real agent ===")
    for seed in (1, 2, 3):
        ag = cls(seed)
        total, env = run_episode(ag, seed, steps=6000)
        causal = ag.causal_edges()
        print(f"seed {seed}: reward={total:.1f} deaths~{ag.stats.get('full_wipes', 0)}")
        print(f"  CAUSAL {fmt(causal)}")
        print(f"  press->lever: {('press', 'lever') in causal}; eat->ate: {('eat', 'ate') in causal}; "
              f"vantage present: {[v for v in VANTAGE if v in causal]}")
