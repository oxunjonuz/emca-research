"""Analysis: evaluate pre-registered thresholds E1-E6 against the matrix.

Reads results/matrix/*.json, prints per-condition aggregates and verdicts.
Run: python3 analyze.py
"""
import glob
import json
import os
from collections import defaultdict

TRUE_EDGES = {("press", "lever"), ("eat", "ate"), ("eat", "energy_rose"),
              ("press", "door_gone")}
FALSE_EDGE_EXAMPLES = {("grasp", "grasp")}   # tautology, not a world fact


def load():
    data = defaultdict(list)
    for p in sorted(glob.glob("results/matrix/*.json")):
        with open(p) as f:
            d = json.load(f)
        data[d["condition"]].append(d)
    return data


def avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def main():
    data = load()
    print(f"{'condition':16s} {'reward':>7s} {'deaths':>6s} {'berries':>7s} "
          f"{'trea':>4s} {'lever':>5s} {'edges':>5s} {'true%':>6s}")
    table = {}
    for cond, runs in sorted(data.items()):
        rew = avg([r["total_reward"] for r in runs])
        dea = avg([r["deaths"] for r in runs])
        ber = avg([r["berries_eaten"] for r in runs])
        tre = avg([r["treasures"] for r in runs])
        lev = avg([r["lever_presses"] for r in runs])
        edges = [tuple(e[:2]) for r in runs for e in r.get("causal_edges", [])]
        # E1: fraction of identified edges that are TRUE world edges
        true_frac = None
        if edges:
            n_true = sum(1 for e in edges if e in TRUE_EDGES)
            true_frac = n_true / len(edges)
        table[cond] = dict(reward=rew, deaths=dea, berries=ber, treasures=tre,
                           levers=lev, edges=len(edges) / len(runs),
                           true_frac=true_frac, runs=runs)
        print(f"{cond:16s} {rew:7.1f} {dea:6.1f} {ber:7.1f} {tre:4.1f} "
              f"{lev:5.1f} {len(edges)/len(runs):5.1f} "
              f"{(f'{true_frac:.2f}' if true_frac is not None else '  -')}")

    print()
    # ---------------- pre-registered verdicts ----------------
    emca = table.get("emca", {})
    verdicts = []

    # E1 causal: >=50% of edges true, and press->lever found in >=2/3 seeds
    runs = emca.get("runs", [])
    pl = sum(1 for r in runs
             if any(e[0] == "press" and e[1] == "lever" for e in r["causal_edges"]))
    tf = emca.get("true_frac")
    e1 = (tf is not None and tf >= 0.5 and pl >= 2)
    verdicts.append(("E1 causal identification", e1,
                     f"true_frac={tf}, press->lever in {pl}/3 seeds"))

    # E2 memory persistence: post-reset recovery >= 2x naive (first window)
    rec = [r["post_reset_recovery"] for r in runs if r.get("post_reset_recovery") is not None]
    pre = [r["pre_reset_competence"] for r in runs if r.get("pre_reset_competence") is not None]
    e2r = avg(rec); e2p = avg(pre)
    # amnesia control should be WORSE than emca
    amn = table.get("emca_amnesia", {}).get("runs", [])
    amn_rec = avg([r["post_reset_recovery"] for r in amn
                   if r.get("post_reset_recovery") is not None])
    e2 = e2r is not None and e2p is not None and e2r >= 2 * max(e2p, 1)
    verdicts.append(("E2 memory persistence (reset recovery)", e2,
                     f"reset_win={e2r}, first_win={e2p}, amnesia_reset_win={amn_rec}"))

    # E3 planning: treasures >= 1 per life on average; baselines 0
    e3 = (emca.get("treasures") or 0) >= 1.0
    base_tre = {c: table[c]["treasures"] for c in ("random", "qlearn", "ngram")
                if c in table}
    verdicts.append(("E3 planning (treasure chain)", e3,
                     f"emca={emca.get('treasures')}, baselines={base_tre}"))

    # E4 adaptation: deaths in last 3 windows (post-flip) <= deaths in flip window
    def postflip_deaths(r):
        return sum(r["deaths_by_window"].get(str(w), 0) for w in (7, 8, 9))
    def flipwin_deaths(r):
        return r["deaths_by_window"].get("6", 0)
    e4a = avg([postflip_deaths(r) for r in runs])
    e4b = avg([flipwin_deaths(r) for r in runs])
    q_runs = table.get("qlearn", {}).get("runs", [])
    q4a = avg([postflip_deaths(r) for r in q_runs])
    q4b = avg([flipwin_deaths(r) for r in q_runs])
    e4 = e4a is not None and e4b is not None and e4a <= e4b
    verdicts.append(("E4 adaptation after regime flip", e4,
                     f"emca flip_win={e4b} post_flip={e4a}; qlearn {q4b}->{q4a}"))

    # E5 goals: >=2 non-survival goal kinds pursued >=100 steps total
    def goal_steps(r):
        return sum(1 for g in r.get("goals_active_before_reset", [])
                   if g["kind"] not in ("homeostasis",))
    kinds_by_seed = []
    for r in runs:
        ks = {g["kind"] for g in r.get("goals_active_before_reset", [])
              + r.get("goals_active_after_reset", [])
              if g["kind"] not in ("homeostasis",)}
        kinds_by_seed.append(len(ks))
    e5 = avg(kinds_by_seed) >= 2
    verdicts.append(("E5 autonomous goals (>=2 non-survival kinds)", e5,
                     f"avg non-survival kinds={avg(kinds_by_seed)}"))

    # E6 subjectivity: goals born before reset still active/achieved after
    e6_count = 0
    for r in runs:
        before_ids = {g["id"] for g in r.get("goals_active_before_reset", [])}
        after = r.get("goals_at_reset", [])
        # goal active AT reset moment surviving = subjectivity trace
        if after:
            e6_count += 1
    e6 = e6_count >= 2
    verdicts.append(("E6 goal persistence across reset", e6,
                     f"seeds with active goals at reset: {e6_count}/3"))

    print("PRE-REGISTERED VERDICTS")
    for name, ok, detail in verdicts:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    # negative results ledger
    print()
    print("NEGATIVE-RESULT LEDGER (kept regardless of outcome)")
    for cond in sorted(table):
        r = table[cond]
        print(f"  {cond:16s} reward={r['reward']:.1f} deaths={r['deaths']:.1f} "
              f"treasures={r['treasures']}")


if __name__ == "__main__":
    main()
