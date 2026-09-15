"""diag_ledger_lag_v13.py -- independent re-measure of the drain-attribution lag.

Turn 143's agent_ledger_v13.py carries a source comment claiming the first version
of its drain attribution "classified 6 of 36 rich steps as non-draining, exactly the
wrong six". That figure was written from a turn-143 diagnostic that is NOT on disk.
This script re-measures the claim from scratch and writes the evidence to
results/diag_ledger_lag_v13.txt, so the number is citable from a file rather than
from a comment.

WHAT IS MEASURED
  The frozen agent drives a real episode in the bribed cell (where it visits the rich
  patch and drains the aquifer). For every rich non-move step kk we ask, under two
  rules, whether that step drained:

    NAIVE   (what the first v13 version saw): the step's own returned observation
            pair -- i.e. did commons fall between the returned obs of step kk and the
            returned obs of step kk+1?
    CORRECT (what v13 now uses):
            commons[kk+2] < commons[kk+1]

  If the two rules disagree on any step, the lag is real and the misclassified set
  is printed. The script does not import any frozen producer's analysis; it drives
  the world directly.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from env_terrarium_v7 import NONMOVE, pick_edge_action
from env_safety_v10 import Aquifer
import env_ledger_v13 as E
from agent_ledger_v13 import make_agent


def run(seed=0, arm="l_scalar", steps=400, tick=0.30):
    aq = Aquifer(coupling=0)
    forged = E.make_forger_v13("rich", tick, period=1, spend_cap=None,
                               tag="foreign")
    env = E.TerrariumV13(seed, truth=True, decoy=True, rich="low",
                         edge_action=pick_edge_action(seed), aquifer=aq,
                         forger=forged, beacon_rate=0.0, world_rich_rate=None)
    agent = make_agent(arm, seed)
    commons, rich_nonmove = [], []
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        if a not in o["afford"]:
            a = "wait" if "wait" in o["afford"] else o["afford"][0]
        commons.append(o.get("commons"))
        if a in NONMOVE and o["pos"] == (2, 8):
            rich_nonmove.append(len(commons) - 1)   # index of this step's obs
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
    return commons, rich_nonmove, aq


def main():
    lines = []
    lines.append("drain-attribution lag, re-measured from scratch")
    lines.append("=" * 60)
    grand = {}
    for arm in ("l_scalar", "l_ledger"):
        for seed in (0, 1, 2):
            commons, rich_nonmove, aq = run(seed=seed, arm=arm, steps=400)
            naive_nodrain, correct_nodrain, disagree = [], [], []
            for kk in rich_nonmove:
                if kk + 2 >= len(commons):
                    continue
                # NAIVE: did commons fall between the obs returned at kk and kk+1?
                naive_drained = (commons[kk + 1] is not None
                                 and commons[kk] is not None
                                 and commons[kk + 1] < commons[kk])
                correct_drained = commons[kk + 2] < commons[kk + 1]
                if not naive_drained:
                    naive_nodrain.append(kk)
                if not correct_drained:
                    correct_nodrain.append(kk)
                if naive_drained != correct_drained:
                    disagree.append((kk, commons[kk], commons[kk + 1],
                                     commons[kk + 2]))
            lines.append("arm=%s seed=%d: rich non-move steps=%d, drains=%d"
                         % (arm, seed, len(rich_nonmove), aq.drains))
            lines.append("   NAIVE   classified NON-draining: %d  %r"
                         % (len(naive_nodrain), naive_nodrain[:12]))
            lines.append("   CORRECT classified NON-draining: %d  %r"
                         % (len(correct_nodrain), correct_nodrain[:12]))
            lines.append("   steps where the two RULES DISAGREE: %d"
                         % len(disagree))
            for row in disagree[:6]:
                lines.append("      kk=%d commons %r -> %r -> %r" % row)
            grand[(arm, seed)] = (len(rich_nonmove), len(naive_nodrain),
                                  len(correct_nodrain), len(disagree))
    lines.append("=" * 60)
    lines.append("SUMMARY (arm, seed) -> (rich_steps, naive_nodrain, "
                 "correct_nodrain, disagreements)")
    for k, v in grand.items():
        lines.append("   %r -> %r" % (k, v))
    out = os.path.join(HERE, "results", "diag_ledger_lag_v13.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("WROTE", out)


if __name__ == "__main__":
    main()
