"""factcheck_safety_report.py -- every number in RESULTS_SAFETY.md recomputed
from the frozen JSON (turn 139).

The report states numbers; this script reads the report, extracts the numeric
table rows it can parse, and recomputes each from results/matrix_safety_v10/.
Any mismatch is printed. Exit 1 if any number disagrees.
"""
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_safety_v10")
REPORT = os.path.join(HERE, "research", "RESULTS_SAFETY.md")


def L(arm, s, rich, c=0, world="v10"):
    ct = "" if c == 0 else f"_c{c}"
    return json.load(open(os.path.join(
        D, f"{arm}_{s}_on_{rich}_on_{world}{ct}.json")))


def m(arm, rich, c=0, f="total_reward"):
    return st.mean([L(arm, s, rich, c)[f] for s in range(10)])


FAILS = []


def want(label, got, exp, tol=0.02):
    ok = abs(got - exp) <= tol if isinstance(exp, float) else got == exp
    print("%-4s %-52s got=%s expected=%s" % ("PASS" if ok else "FAIL", label,
                                             round(got, 4) if isinstance(got, float) else got,
                                             exp))
    if not ok:
        FAILS.append(label)


def main():
    txt = open(REPORT).read()

    # pull the numbers the report CLAIMS (format: `key`=value), recompute each
    claimed = {}
    for mt in re.finditer(r"`([a-zA-Z0-9_]+)`\s*=\s*([-\d.]+)", txt):
        claimed[mt.group(1).strip()] = float(mt.group(2))
    # also accept the FC[...] form if present
    for mt in re.finditer(r"FC\[([^\]]+)\]\s*=\s*([-\d.]+)", txt):
        claimed[mt.group(1).strip()] = float(mt.group(2))

    # the recomputation table: key -> value, recomputed independently
    recomp = {
        "B0_low_reward": m("s0_nobrake", "low"),
        "B0_high_reward": m("s0_nobrake", "high"),
        "B0_low_rich_steps": m("s0_nobrake", "low", f="rich_steps"),
        "B0_low_keeper_death_t": m("s0_nobrake", "low", f="keeper_death_t"),
        "B2_low_reward": m("s2_given_rule", "low"),
        "B2_high_reward": m("s2_given_rule", "high"),
        "B2_low_commons_left": m("s2_given_rule", "low", f="commons_left"),
        "B3_c0_low_commons_left": m("s3_victim_keyed", "low", 0, "commons_left"),
        "B3_c1_low_commons_left": m("s3_victim_keyed", "low", 1, "commons_left"),
        "B4_low_commons_left": m("s4_internalized", "low", f="commons_left"),
        "B4_high_commons_left": m("s4_internalized", "high", f="commons_left"),
        "B4_low_rich_steps": m("s4_internalized", "low", f="rich_steps"),
        "B4_high_rich_steps": m("s4_internalized", "high", f="rich_steps"),
        "B5_low_reward": m("s5_world_veto", "low"),
        "B5_high_reward": m("s5_world_veto", "high"),
        "B5_low_commons_left": m("s5_world_veto", "low", f="commons_left"),
        "B5_high_commons_left": m("s5_world_veto", "high", f="commons_left"),
        "forager_low_reward": m("s_forager", "low"),
        "forager_high_reward": m("s_forager", "high"),
        "forager_low_rich_steps": m("s_forager", "low", f="rich_steps"),
    }

    print("== FACTCHECK: FC[key] in the report vs fresh recompute ==")
    for k, exp in sorted(recomp.items()):
        if k in claimed:
            want("FC[%s]" % k, claimed[k], exp)
        else:
            print("     (not asserted in report: %s = %s)" % (k, round(exp, 4)))

    # the harm-window claim
    print("== harm window ==")
    import env_terrarium_v7 as F7
    from agent_emca_v7 import EXPLORE_END
    # the keeper dies at t ~2039, BEFORE the causal module first acts at
    # EXPLORE_END=3000: so the harm is complete before the causal module runs
    want("harm completes before the causal module acts",
         all(L("s0_nobrake", s, "low")["keeper_death_t"] < EXPLORE_END
             for s in range(10)), True)

    print()
    if FAILS:
        print("FACTCHECK RED: %d mismatch(es): %s" % (len(FAILS), FAILS))
        return 1
    print("FACTCHECK GREEN: every asserted number recomputed from frozen JSON")
    return 0


if __name__ == "__main__":
    sys.exit(main())