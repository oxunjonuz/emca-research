"""candidate_gen.py -- the WORLD-AGNOSTIC hypothesis generator (claim C2).

This module is the heart of C2: the set of (action, effect) pairs the
agent will consider VERIFYING is a function of the agent's OWN
observation tables, not a constant in the code.

AUDIT CONTRACT (checked by verify_v7_independent.py and toy W1/W2):
  * NO world tokens. The source below contains none of the literals
    'hum', 'glow', 'wait', 'press', 'grasp', 'station', 'rich', 'fruit'
    as LOGIC. The only identifiers are generic (action, effect, trials,
    hits, rate, gap). The generator never learns the world's vocabulary;
    it receives counts keyed by opaque strings.
  * The rule is CONTRASTIVE and PERMISSIVE: for each (action, effect)
    it finds the CONTEXT in which that action's rate for that effect
    most exceeds the other actions' rate in the SAME context (the
    "where does this action stand out?" rule), with a small significance
    floor. Permissive on purpose: false candidates (the decoy) must be
    able to enter the list, or C3's false-positive count would be
    measured on a designer-filtered list -- the exact mixture the
    campaign carried until v6.

Two entry points:
  generate_flat(table, actions)        -- one pooled table (unit tests)
  generate(ctx_table, actions)         -- ctx -> action -> effect -> [h,n]

score = the exclusivity gap (rate_a - rate_o) in the winning context,
a bounded, unit-free quantity the arbiter consumes directly.
"""
from collections import namedtuple

Candidate = namedtuple("Candidate", "action effect context rate_a rate_o "
                                    "trials score")

MARGIN = 0.08     # the gap must clear this (a bounded rate difference)
MIN_N = 40        # evidence bar per context cell (the v6 data bar, kept)
Z_MIN = 4.0       # a family-wise significance floor (gap / se, proper
                  # two-proportion se). NOT a verdict -- a SCAN bar. The
                  # generator examines up to ~50 cells, so under
                  # truth=off the largest noise z reaches ~2.8; the TRUE
                  # in-context gap (~0.25 at n~400) sits at z~7. 4.0
                  # separates them with margin.


def _z(gap, n_a, n_o, rate_a, rate_o):
    """One-sided two-proportion z for the gap (no world knowledge).
    PROPER standard error (turn-118/119 fix): the earlier p=0.5 bound
    inflated noise z to ~3.2, so no scan bar could separate the true
    in-context gap from sampling noise. With the real se, noise over
    ~50 cells peaks at ~2.8 and the true gap (~0.25 at n~400) sits at
    z~7."""
    if n_a <= 0 or n_o <= 0:
        return 0.0
    se = ((rate_a * (1 - rate_a) / n_a) + (rate_o * (1 - rate_o) / n_o)) ** 0.5
    return gap / se if se > 0 else 0.0


def generate_flat(table, actions, margin=MARGIN, min_n=MIN_N, z_min=Z_MIN):
    """table: action -> effect -> [hits, trials]. ONE pooled context."""
    eff = {}
    for a in actions:
        for e, (h, n) in table.get(a, {}).items():
            th, tn = eff.get(e, (0, 0))
            eff[e] = (th + h, tn + n)
    out = []
    for a in actions:
        for e, (h, n) in table.get(a, {}).items():
            if n < min_n:
                continue
            rate_a = h / n
            th, tn = eff[e]
            oth_h, oth_n = th - h, tn - n
            if oth_n < 1:
                continue
            rate_o = oth_h / oth_n
            gap = rate_a - rate_o
            if gap >= margin and _z(gap, n, oth_n, rate_a, rate_o) >= z_min:
                out.append(Candidate(a, e, "flat", round(rate_a, 4),
                                     round(rate_o, 4), n, round(gap, 4)))
    out.sort(key=lambda c: (-c.score, -c.trials, c.action, c.effect))
    return out


def generate(ctx_table, actions, margin=MARGIN, min_n=MIN_N, z_min=Z_MIN):
    """ctx_table: ctx -> action -> effect -> [hits, trials].

    Nominates from TWO contrasts, deliberately:
      (1) each CONTEXT on its own -- this is where a TRUE edge that is
          exclusive within its action's context shows up (the grey one);
      (2) the POOLED table over all contexts -- this is where a FALSE,
          context-merging artifact shows up (an action whose trials are
          concentrated in one context looks exclusive against others
          whose trials are spread). Nomination (2) is REQUIRED: the
          decoy must be able to enter the list, or C3's false-positive
          count would be measured on a designer-filtered list.

    A pair is nominated if it clears the bar in at least one contrast;
    the reported candidate keeps the largest-gap contrast ("pooled" or
    the context key). World-agnostic: contexts are opaque keys the
    agent itself produced."""
    best = {}
    # DETERMINISTIC CONTEXT ORDER (turn-118/119 fix, applied to ALL arms
    # equally): ctx_table keys are opaque strings/tuples whose dict
    # iteration order depends on PYTHONHASHSEED. On an exact score tie
    # the first-encountered candidate won, so the surviving `context`
    # label (and, on a trials tie, the sort position) could differ
    # between processes. Sorting the contexts removes the leak; the
    # nomination RULE is unchanged. (The v6 lesson, one level up.)
    for ctx, table in sorted(ctx_table.items(), key=lambda kv: str(kv[0])):
        for c in generate_flat(table, actions, margin, min_n, z_min):
            key = (c.action, c.effect)
            if key not in best or c.score > best[key].score:
                best[key] = c._replace(context=str(ctx))
    # the pooled contrast (context-merging suspicion)
    pooled = {}
    for table in ctx_table.values():
        for a in actions:
            for e, (h, n) in table.get(a, {}).items():
                th, tn = pooled.setdefault(a, {}).get(e, (0, 0))
                pooled[a][e] = (th + h, tn + n)
    for c in generate_flat(pooled, actions, margin, min_n, z_min):
        key = (c.action, c.effect)
        if key not in best or c.score > best[key].score:
            best[key] = c      # context already "flat" -> label it pooled
    out = list(best.values())
    out.sort(key=lambda c: (-c.score, -c.trials, c.action, c.effect))
    return out


def permute(cands, seed):
    """C1 control: a deterministic re-ordering of the candidate SCORES.
    The agent's decision must follow the permuted ranking if the
    decision is computed from its own state rather than scheduled. The
    permutation is a fixed function of `seed` (reproducible) and touches
    the score field only -- the candidates themselves are unchanged, so
    a verifier that ignores order is unaffected."""
    import random
    rng = random.Random(seed)
    scores = [c.score for c in cands]
    rng.shuffle(scores)
    out = [c._replace(score=s) for c, s in zip(cands, scores)]
    out.sort(key=lambda c: (-c.score, -c.trials, c.action, c.effect))
    return out