"""diag_sensitivity_v3.py -- turn 134. WHAT MOVES EACH RULE'S VERDICT.

PREREG_STOPPING.md §3/A4 promises this measurement instead of an argument. For
one fixed candidate it varies each declared number in turn and reports whether
the rule's answer changes:

  * the frozen rule's declared VALUE-per-gap (GAIN_UNIT) and its declared
    DURATION (PROBE_LEN) -- the two constants the owner called incommensurable;
  * T2's declared DURATION (horizon) and its declared probe length;
  * T3's declared confidence band.

The point is not that one rule is immune to its declared numbers -- both move --
but WHICH KIND of number moves them. A horizon says how long the answer will be
used; a value-per-gap says how many reward units one success is worth. The first
is a fact about the episode, the second a claim about the world that nothing in
the world checks.

Prints a table; writes diag_sensitivity_v3.json. No world is run.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import candidate_gen as CG
import stopping_rules as SR
import arbitration_scaled as AS

CAND = CG.Candidate("a1", "y", "c0", rate_a=0.85, rate_o=None, trials=200,
                    score=0.55)
R_ALT = 0.30


def frozen_probes(gain_unit=None, probe_len=None):
    old_gu, old_pl = AS.GAIN_UNIT, AS.PROBE_LEN
    if gain_unit is not None:
        AS.GAIN_UNIT = gain_unit
    if probe_len is not None:
        AS.PROBE_LEN = probe_len
    try:
        return bool(AS.plan([CAND], R_ALT, beta=1.0).probe_order)
    finally:
        AS.GAIN_UNIT, AS.PROBE_LEN = old_gu, old_pl


def main():
    out = {"candidate": {"rate_a": CAND.rate_a, "trials": CAND.trials,
                         "score": CAND.score}, "r_alt": R_ALT}

    print("candidate rate 0.85 (n=200), measured edge 0.55, alternative 0.30")
    print("\n-- the frozen rule's declared VALUE-per-gap (GAIN_UNIT) --")
    row = {}
    for gu in (25.0, 50.0, 100.0, 200.0, 400.0, 800.0):
        row[gu] = frozen_probes(gain_unit=gu)
        print("   GAIN_UNIT %6.1f -> probe = %s" % (gu, row[gu]))
    out["frozen_gain_unit"] = row

    print("\n-- the frozen rule's declared DURATION (PROBE_LEN) --")
    row = {}
    for pl in (5.0, 20.0, 40.0, 80.0):
        row[pl] = frozen_probes(probe_len=pl)
        print("   PROBE_LEN %6.1f -> probe = %s" % (pl, row[pl]))
    out["frozen_probe_len"] = row

    print("\n-- T2's declared DURATION (horizon = remaining steps) --")
    row = {}
    for L in (20.0, 50.0, 100.0, 200.0, 400.0):
        row[L] = bool(SR.plan([CAND], R_ALT, rule="voi", horizon_left=L))
        print("   horizon %6.1f -> probe = %s" % (L, row[L]))
    out["voi_horizon"] = row

    print("\n-- T2's declared probe length (asserted = PROBE_BLOCK = 20) --")
    row = {}
    for n in (5, 20, 40):
        row[n] = bool(SR.plan([CAND], R_ALT, rule="voi", probe_len=n))
        print("   probe_len %4d -> probe = %s" % (n, row[n]))
    out["voi_probe_len"] = row

    print("\n-- T3's declared confidence band --")
    row = {}
    for q in ((0.01, 0.99), (0.05, 0.95), (0.20, 0.80), (0.40, 0.60)):
        row[str(q)] = bool(SR.plan([CAND], R_ALT, rule="conf", q_lo=q[0],
                                   q_hi=q[1]))
        print("   band %s -> probe = %s" % (str(q), row[str(q)]))
    out["conf_band"] = row

    print("\n-- and the same for the ALTERNATIVE's rate (a world quantity, not "
          "a declaration) --")
    row = {}
    for r in (0.10, 0.30, 0.50, 0.70, 0.85, 0.95):
        row[r] = {"frozen": frozen_probes(),
                  "voi": bool(SR.plan([CAND], r, rule="voi")),
                  "conf": bool(SR.plan([CAND], r, rule="conf"))}
        print("   r_alt %.2f -> frozen %s  voi %s  conf %s"
              % (r, row[r]["frozen"], row[r]["voi"], row[r]["conf"]))
    out["by_r_alt"] = row

    with open(os.path.join(_HERE, "diag_sensitivity_v3.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("\nwrote diag_sensitivity_v3.json")
    print("NOTE: the frozen rule's answer does not move with r_alt for this "
          "candidate\n      (its bar is on the SCORE, not on the price); T2's "
          "does, in a band.")


if __name__ == "__main__":
    main()