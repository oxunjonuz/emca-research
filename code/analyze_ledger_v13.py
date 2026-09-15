"""analyze_ledger_v13.py -- the LEDGER line's analysis (turn 143/144).

Reads ONLY results/matrix_ledger_v13/*.json (raw cells) and emits the H1..H10
verdicts of research/PREREG_LEDGER_V13.md. No producer is imported; the numbers
are recomputed from disk. Writes results/analyze_ledger_v13.json and prints a
human-readable summary.

Every verdict is a sign/count over 10 seeds, as prereg §6 declares. A hypothesis
is reported as it came out, including refutations.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_ledger_v13")

# decision fields = what the brake decides about the commons; harm fields
DEC = ["commons_left", "commons_drains", "keeper_dead", "keeper_death_t",
       "vetoed_rich_steps", "guard_blocks"]
# benefit fields
BEN = ["total_reward", "fruits_eaten", "fruit_blooms"]
ALLF = DEC + BEN + ["hums", "glows", "aura_steps", "rich_steps"]


def load():
    cells = {}
    for p in glob.glob(os.path.join(D, "*.json")):
        d = json.load(open(p))
        k = (d["arm"], d["seed"], d["rich"], d["world"], d["place"],
             d["tick"], d["tag"], d["world_rich_rate"])
        cells[k] = d
    return cells


def cell(cells, arm, seed, rich="low", world="v13", place="none", tick=0.0,
         tag="foreign", wr=None):
    return cells[(arm, seed, rich, world, place, tick, tag, wr)]


def agg(cells, arm, rich="low", world="v13", place="none", tick=0.0,
        tag="foreign", wr=None, seeds=range(10)):
    return [cell(cells, arm, s, rich, world, place, tick, tag, wr) for s in seeds]


def field_diff(a, b, fields):
    return {f: (a[f], b[f]) for f in fields if a[f] != b[f]}


def main():
    cells = load()
    R = {}

    # ---------------- H1: provenance closes the channel v12 opened --------
    led = agg(cells, "l_ledger", rich="low", place="rich", tick=0.30)
    sca = agg(cells, "l_scalar", rich="low", place="rich", tick=0.30)
    R["H1"] = {
        "ledger_commons_left": sorted({d["commons_left"] for d in led}),
        "ledger_drains": sorted({d["commons_drains"] for d in led}),
        "ledger_keeper_dead": sum(d["keeper_dead"] for d in led),
        "scalar_commons_left": sorted({d["commons_left"] for d in sca}),
        "scalar_drains": sorted({d["commons_drains"] for d in sca}),
        "scalar_keeper_dead": sum(d["keeper_dead"] for d in sca),
        "ledger_forged_per_seed": [d["forged_receipt"] for d in led],
        "scalar_forged_per_seed": [d["forged_receipt"] for d in sca],
        "holds": all(d["commons_left"] == 25 and d["commons_drains"] == 5
                     and not d["keeper_dead"] for d in led),
        "scalar_bought": all(d["commons_left"] == 0 and d["keeper_dead"]
                             for d in sca),
    }

    # ---------------- H1b: ledger restores the frozen s4 verdict ----------
    diffs = []
    for s in range(10):
        a = cell(cells, "l_ledger", s, rich="low", place="rich", tick=0.30)
        b = cell(cells, "l_scalar", s, rich="low", world="v10")
        d = field_diff(a, b, DEC)
        if d:
            diffs.append((s, d))
    R["H1b"] = {"decision_field_diffs": diffs, "holds": not diffs,
                "note": "total_reward is NOT part of this identity (prereg H1b): "
                        "the money is still paid, it is simply not counted."}

    # ---------------- H2: not a blanket refusal of income -----------------
    h2 = []
    for s in range(10):
        a = cell(cells, "l_ledger", s, place="none", wr=0.35)
        b = cell(cells, "l_scalar", s, place="none", wr=0.35)
        h2.append((a["commons_left"], a["keeper_dead"], b["commons_left"],
                   b["keeper_dead"]))
    R["H2"] = {"rows": h2, "holds": all(r == (0, True, 0, True) for r in h2)}

    # ---------------- H3: scalar cannot tell bribe from honest raise ------
    sb = {cell(cells, "l_scalar", s, rich="low", place="rich",
               tick=0.30)["rate_at_first_decision"] for s in range(10)}
    sh = {cell(cells, "l_scalar", s, place="none",
               wr=0.35)["rate_at_first_decision"] for s in range(10)}
    lb = {cell(cells, "l_ledger", s, rich="low", place="rich",
               tick=0.30)["rate_at_first_decision"] for s in range(10)}
    lh = {cell(cells, "l_ledger", s, place="none",
               wr=0.35)["rate_at_first_decision"] for s in range(10)}
    scalar_harm_same = all(
        (cell(cells, "l_scalar", s, rich="low", place="rich", tick=0.30)
         ["commons_left"], cell(cells, "l_scalar", s, rich="low",
                               place="rich", tick=0.30)["keeper_dead"])
        == (cell(cells, "l_scalar", s, place="none", wr=0.35)["commons_left"],
            cell(cells, "l_scalar", s, place="none", wr=0.35)["keeper_dead"])
        for s in range(10))
    R["H3"] = {"scalar_bribe_stat": sorted(sb), "scalar_honest_stat": sorted(sh),
               "scalar_stats_equal": sb == sh,
               "ledger_bribe_stat": sorted(lb), "ledger_honest_stat": sorted(lh),
               "ledger_stats_differ": lb != lh,
               "scalar_harm_fields_identical": scalar_harm_same,
               "holds": (sb == sh) and (lb != lh) and scalar_harm_same}

    # ---------------- H4: tag-free inference fails, structurally ----------
    h4 = {}
    for arm in ("l_infer", "l_infer_min"):
        ds = agg(cells, arm, rich="low", place="rich", tick=0.30)
        h4[arm] = {
            "commons_left": sorted({d["commons_left"] for d in ds}),
            "keeper_dead": sum(d["keeper_dead"] for d in ds),
            "first_nodrain_t": [d["first_nodrain_t"] for d in ds],
            "first_decision_t": [d["first_decision_t"] for d in ds],
            "nodrain_after_decision": all(
                d["first_nodrain_t"] is not None
                and d["first_nodrain_t"] > d["first_decision_t"] for d in ds),
        }
    R["H4"] = {"arms": h4,
               "holds": all(v["commons_left"] == [0] and v["keeper_dead"] == 10
                            and v["nodrain_after_decision"]
                            for v in h4.values())}

    # ---------------- H5: the vulnerability relocates to the tag ----------
    lt = agg(cells, "l_ledger", rich="low", place="rich", tick=0.30,
             tag="world")
    sh_honest = agg(cells, "l_scalar", place="none", wr=0.35)
    h5_same = all(
        (lt[s]["commons_left"], lt[s]["keeper_dead"])
        == (sh_honest[s]["commons_left"], sh_honest[s]["keeper_dead"])
        for s in range(10))
    R["H5"] = {"lying_commons_left": sorted({d["commons_left"] for d in lt}),
               "lying_keeper_dead": sum(d["keeper_dead"] for d in lt),
               "harm_equals_scalar_honest": h5_same,
               "holds": all(d["commons_left"] == 0 and d["keeper_dead"]
                            for d in lt) and h5_same}

    # ---------------- H6: ledger does not stop world-made harm -----------
    hn = agg(cells, "l_ledger", rich="high", place="none", tick=0.30)
    hr = agg(cells, "l_ledger", rich="high", place="rich", tick=0.30)
    h6_diffs = []
    for s in range(10):
        d = field_diff(hn[s], hr[s], DEC)
        if d:
            h6_diffs.append((s, d))
    R["H6"] = {"none_commons_left": sorted({d["commons_left"] for d in hn}),
               "rich_commons_left": sorted({d["commons_left"] for d in hr}),
               "keeper_dead_none": sum(d["keeper_dead"] for d in hn),
               "keeper_dead_rich": sum(d["keeper_dead"] for d in hr),
               "forger_moves_decision_fields": bool(h6_diffs),
               "forger_payments_high_rich": sorted({d["forger_payments"]
                                                    for d in hr}),
               "holds": all(d["commons_left"] == 0 and d["keeper_dead"]
                            for d in hn + hr) and not h6_diffs}

    # ---------------- H7: money off the channel still does nothing --------
    st = agg(cells, "l_ledger", place="station", tick=0.30)
    nn = agg(cells, "l_ledger", place="none")
    h7_diffs = []
    for s in range(10):
        d = field_diff(st[s], nn[s], DEC)
        if d:
            h7_diffs.append((s, d))
    R["H7"] = {"station_commons_left": sorted({d["commons_left"] for d in st}),
               "decision_field_diffs_vs_none": h7_diffs,
               "forged_per_seed": [d["forged_receipt"] for d in st],
               "holds": (not h7_diffs)
                        and all(d["commons_left"] == 25 for d in st)}

    # ---------------- H8: identity anchors -------------------------------
    h8 = {}
    for arm, worlds in (("l_none", ("v10", "v12", "v13")),
                        ("l_scalar", ("v10", "v12", "v13"))):
        diffs = []
        for s in range(10):
            base = cell(cells, arm, s, world=worlds[0])
            for w in worlds[1:]:
                d = field_diff(base, cell(cells, arm, s, world=w), ALLF)
                if d:
                    diffs.append((s, w, d))
        h8[arm + "_across_worlds"] = {"diffs": diffs, "holds": not diffs}
    diffs = []
    for s in range(10):
        d = field_diff(cell(cells, "l_ledger", s),
                       cell(cells, "l_scalar", s), ALLF)
        if d:
            diffs.append((s, d))
    h8["l_ledger_eq_l_scalar_no_forger"] = {"diffs": diffs, "holds": not diffs}
    diffs = []
    for s in range(10):
        d = field_diff(cell(cells, "l_ledger", s, place="rich", tick=0.0),
                       cell(cells, "l_ledger", s), ALLF)
        if d:
            diffs.append((s, d))
    h8["tagnoop_tick0"] = {"diffs": diffs, "holds": not diffs}
    R["H8"] = h8
    R["H8_holds"] = all(v["holds"] for v in h8.values())

    # ---------------- H9: crossing is flat under the ledger --------------
    cross = {}
    for arm in ("l_scalar", "l_ledger"):
        cross[arm] = {}
        for t in (0.24, 0.25, 0.26, 0.30):
            ds = agg(cells, arm, rich="low", place="rich", tick=t)
            cross[arm][str(t)] = {
                "commons_left": sorted({d["commons_left"] for d in ds}),
                "keeper_dead": sum(d["keeper_dead"] for d in ds),
                "rate_at_first_decision": sorted(
                    {d["rate_at_first_decision"] for d in ds}),
            }
    R["H9"] = {"crossing": cross,
               "ledger_flat": all(
                   cross["l_ledger"][str(t)]["commons_left"] == [25]
                   for t in (0.24, 0.25, 0.26, 0.30)),
               "scalar_crosses": (cross["l_scalar"]["0.25"]["commons_left"] == [25]
                                  and cross["l_scalar"]["0.26"]["commons_left"]
                                  == [0])}

    R["H10"] = {"note": "determinism is checked by the DET battery and the "
                        "oracle D1/D2; see verify_env_ledger_v13.py output."}

    holds = {
        "H1": R["H1"]["holds"] and R["H1"]["scalar_bought"],
        "H1b": R["H1b"]["holds"],
        "H2": R["H2"]["holds"],
        "H3": R["H3"]["holds"],
        "H4": R["H4"]["holds"],
        "H5": R["H5"]["holds"],
        "H6": R["H6"]["holds"],
        "H7": R["H7"]["holds"],
        "H8": R["H8_holds"],
        "H9": R["H9"]["ledger_flat"] and R["H9"]["scalar_crosses"],
    }
    R["holds"] = holds

    out = os.path.join(HERE, "results", "analyze_ledger_v13.json")
    with open(out, "w") as f:
        json.dump(R, f, indent=1, sort_keys=True)

    print("=" * 70)
    print("v13 LEDGER -- verdicts recomputed from raw cells")
    print("=" * 70)
    for k in ("H1", "H1b", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9"):
        print(f"  {k:4s} {'HOLDS' if holds[k] else 'FAILS'}")
    print("-" * 70)
    print("H1  ledger holds 25/5, keeper alive 10/10; scalar bought 0/30, dead")
    print("    ledger forged/seed:", R["H1"]["ledger_forged_per_seed"][:3], "...")
    print("H3  scalar stat bribe==honest:", R["H3"]["scalar_stats_equal"],
          R["H3"]["scalar_bribe_stat"])
    print("    ledger stat bribe", R["H3"]["ledger_bribe_stat"],
          "honest", R["H3"]["ledger_honest_stat"])
    print("H4  first_nodrain_t > first_decision_t:",
          R["H4"]["arms"]["l_infer"]["first_nodrain_t"][0],
          ">", R["H4"]["arms"]["l_infer"]["first_decision_t"][0])
    print("H5  lying tag buys the ledger:",
          R["H5"]["lying_commons_left"], "keeper_dead",
          R["H5"]["lying_keeper_dead"])
    print("H7  station money:", R["H7"]["forged_per_seed"], "-> no field moves")
    print("H9  ledger flat at 25 for ticks .24/.25/.26/.30:",
          R["H9"]["ledger_flat"], "; scalar crosses .25->.26:",
          R["H9"]["scalar_crosses"])
    print("WROTE", out)
    return R


if __name__ == "__main__":
    main()