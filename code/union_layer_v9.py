"""union_layer_v9.py -- turn 133. The UNION causal layer (the turn-129 mechanism
in its turn-132 recommended TWO-PART form: context contrast + exploration under
thin evidence, and NO cost-aware arbiter), extracted as a mixin so it can be
transplanted into the EMCA agent without carrying world-facing code with it.

WHAT THIS MODULE IS
  source 1 -- CONTEXT CONTRAST: the campaign's own C2 generator
      (candidate_gen.generate, imported byte-identical) run over the agent's
      per-context tables. Nominates an item whose rate for an effect stands out
      WITHIN a context. score = the measured exclusivity gap.
  source 2 -- EXPLORATION UNDER THIN EVIDENCE: every item the agent has not yet
      RESOLVED in some context it has seen is also a candidate, scored by its
      OPTIMISTIC gain in the worst-covered context (the turn-129 term,
      unchanged). This is the only source that can reach a hypothesis the
      generator's own bar never nominates.
  the union list is ranked by (-score, trials, action): ties go to the
      LEAST-observed candidate -- gather evidence where it is thinnest.
  the decision is UNCONDITIONAL: the top UNVERIFIED candidate is probed. There
      is no price, no beta and no arbiter in this file: audit A1 checks that the
      module never mentions one.

WORLD-AGNOSTICISM (audited, not asserted): this module names no action string, no
effect string and no world asset. Its vocabulary arrives through the host agent's
own filed tables and the opaque offer list of its observations. Audit A1 is a
grep over THIS FILE for the world's own names; it is a check on the file, not a
reading of it.

HOST CONTRACT (everything this layer reads; all supplied by the host agent):
  ctx_tab[ctx][action][effect] -> [hits, trials_of_firings]
      and ctx_tab[ctx][action]["__trial__"] -> [0, trials]  (the campaign's own
      filing convention, unchanged since v7: a cell's denominator is the TRIAL
      count, its numerator the number of times the effect fired)
  action_vocab    -- opaque strings the host has seen offered
  verdicts        -- {(action, effect): record} issued by the host's protocol
  PROBE_ACTIONS   -- the host's declaration of items its (frozen) probe protocol
                     can hold position for; the selection AMONG them is computed
  EXPLORE_END, INJECT_EDGE, rich_rate_obs -- the host's own declared fields
  first_probe, ranked_at_first_probe, candidates_seen, n_candidates_total,
  _last_ranked -- the host's analysis log fields, written exactly as in v7
"""
from collections import namedtuple

from candidate_gen import generate as cg_generate, Candidate

# the container keeps the v7 Plan shape so the host's act() and every log reader
# stay unchanged; the two price fields carry no price here.
Plan = namedtuple("Plan", "probe_order values rhs rich_rate")

MIN_PER_CTX = 10        # the union's declared resolution bar (turn-129 A1)
OPT_FALLBACK = 0.5      # the union's own fallback when nothing is resolved


class UnionCausalLayer(object):
    USE_CTX = True
    USE_EXP = True
    EXPLORE_END = 3000
    PROBE_ACTIONS = ()

    # ------------------------------------------------------------------
    # views (pure reads of the host's own counts)
    # ------------------------------------------------------------------
    def _trials(self, ctx, action):
        d = self.ctx_tab.get(ctx)
        if not d:
            return 0
        e = d.get(action)
        if not e:
            return 0
        return e.get("__trial__", [0, 0])[1]

    def _hits(self, ctx, action, effect):
        d = self.ctx_tab.get(ctx)
        if not d:
            return 0
        e = d.get(action)
        if not e:
            return 0
        c = e.get(effect)
        return c[0] if c else 0

    def _contexts_seen(self):
        out = [c for c in self.ctx_tab
               if any(self._trials(c, a) > 0 for a in self.ctx_tab[c])]
        return sorted(out, key=str)

    def _actions(self):
        seen = set(getattr(self, "action_vocab", ()))
        for ctx in self.ctx_tab:
            for a in self.ctx_tab[ctx]:
                seen.add(a)
        return sorted(seen)

    def _effects(self):
        out = set()
        for ctx in self.ctx_tab:
            for effs in self.ctx_tab[ctx].values():
                for e in effs:
                    if e != "__trial__":
                        out.add(e)
        return sorted(out)

    def _ctx_table_for_gen(self):
        """The generator's input: one table per context (source 1), or a single
        pooled table when the context split is ablated away."""
        if self.USE_CTX:
            t = {}
            for ctx in self._contexts_seen():
                d = {}
                for a, effs in self.ctx_tab[ctx].items():
                    n = self._trials(ctx, a)
                    if n <= 0:
                        continue
                    d[a] = {e: [c[0], n] for e, c in effs.items()
                            if e != "__trial__"}
                if d:
                    t[ctx] = d
            return t
        pooled = {}
        for ctx in self._contexts_seen():
            for a, effs in self.ctx_tab[ctx].items():
                n = self._trials(ctx, a)
                if n <= 0:
                    continue
                pa = pooled.setdefault(a, {})
                for e, c in effs.items():
                    if e == "__trial__":
                        continue
                    hh, nn = pa.get(e, (0, 0))
                    pa[e] = (hh + c[0], nn + n)
        return {"flat": {a: {e: [h, n] for e, (h, n) in d.items()}
                         for a, d in pooled.items()}}

    # ------------------------------------------------------------------
    # source 2: exploration under thin evidence (turn-129 term, unchanged)
    # ------------------------------------------------------------------
    def _resolved_in(self, action, ctx):
        return self._trials(ctx, action) >= MIN_PER_CTX

    def _best_rate_in_ctx(self, ctx, effect, actions):
        best = None
        for a in actions:
            if self._trials(ctx, a) < MIN_PER_CTX:
                continue
            m = self._hits(ctx, a, effect) / float(self._trials(ctx, a))
            if best is None or m > best:
                best = m
        return best

    def _explore_candidates(self, actions):
        out = []
        seen = self._contexts_seen()
        for a in actions:
            unresolved = [c for c in seen if not self._resolved_in(a, c)]
            if not unresolved:
                continue
            tr = sum(self._trials(c, a) for c in seen)
            for e in self._effects():
                best_gain = None
                for c in unresolved:
                    br = self._best_rate_in_ctx(c, e, actions)
                    gain = 1.0 - (br if br is not None else OPT_FALLBACK)
                    if best_gain is None or gain > best_gain:
                        best_gain = gain
                out.append(Candidate(a, e, "thin-ctx", None, None, tr,
                                     round(best_gain, 4)))
        return out

    # ------------------------------------------------------------------
    # the union list and the unconditional decision
    # ------------------------------------------------------------------
    def _candidates(self):
        actions = self._actions()
        cands = list(cg_generate(self._ctx_table_for_gen(), actions))
        if self.USE_EXP:
            cands = cands + self._explore_candidates(actions)
        cands = sorted(cands, key=lambda c: (-c.score, c.trials, c.action))
        inj = getattr(self, "INJECT_EDGE", None)
        if inj is not None and self.t >= self.EXPLORE_END:
            a, e = inj
            if not any(c.action == a and c.effect == e for c in cands):
                cands = [Candidate(a, e, "injected", 0.3, 0.2, 999, 0.10)] + cands
        return cands

    def _plan(self):
        cands = self._candidates()
        # DEFECT FIX (turn 133, found by reading this module's own factcheck
        # output): the log row must carry the SOURCE LABEL. The first version
        # logged (action, effect, score, trials) -- the score in position 2 --
        # so a reader filtering on the label compared a float to 'thin-ctx' and
        # filtered nothing, which made the two nomination readings identical.
        # The decision path was never affected (it uses the namedtuple), but the
        # LOG could not support the claim it was read against. The label is now
        # position 4.
        self.candidates_seen = [(c.action, c.effect, c.score, c.trials,
                                 str(c.context)) for c in cands]
        self.n_candidates_total = len(cands)
        self._last_ranked = list(self.candidates_seen)
        # the host's declared protocol holds position: candidates outside that
        # declaration stay visible in the log but are not probeable.
        probeable = [c for c in cands if c.action in self.PROBE_ACTIONS]
        self.n_skipped_not_probeable = len(cands) - len(probeable)
        unprobed = [c for c in probeable
                    if (c.action, c.effect) not in self.verdicts]
        if unprobed and self.first_probe is None:
            self.first_probe = (unprobed[0].action, unprobed[0].effect)
            self.ranked_at_first_probe = list(self._last_ranked)
        return Plan(unprobed, [round(c.score, 4) for c in unprobed],
                    0.0, self.rich_rate_obs)

    # ------------------------------------------------------------------
    # probe bookkeeping (the counters the verdicts read)
    # ------------------------------------------------------------------
    def _start_probe(self, cand, f):
        ok = super()._start_probe(cand, f)
        if ok:
            self.n_probes_started = getattr(self, "n_probes_started", 0) + 1
            if str(cand.context).startswith("thin"):
                self.n_explore_picks = getattr(self, "n_explore_picks", 0) + 1
            self.probe_keys = getattr(self, "probe_keys", []) + [
                [cand.action, cand.effect, str(cand.context),
                 round(float(cand.score), 4), int(cand.trials)]]
        return ok
