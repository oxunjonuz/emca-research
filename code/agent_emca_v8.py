"""agent_emca_v8.py -- the continuous-confidence arms (turn 126).

ONE class, `AgentV8`. An arm is the tuple (mode, tau, cache, kappa); the
shared machinery -- the count store, the gathering rotation, the epoch
bookkeeping, the belief store -- is identical for every arm. The SINGLE
difference between the graded and threshold modes is the decision rule.

Modes (PREREG_V8 §2):
  graded        belief = argmax_a z_a, weight gamma = max(0, 2*Phi(z)-1);
                acts on the belief with probability min(1, tau*gamma),
                else gathers. Control pooled over the other two actions.
  graded1       as graded, but z is computed against a SINGLE control
                action (the first other action alphabetically) -- the
                same contrast form the frozen threshold rule uses, so
                that contrast form and decision rule are two separate
                factors.
  threshold     the campaign's FROZEN v7 rule on the same target-vs-
                first-other 2x2: belief exists iff exact one-sided
                Fisher p < 0.05 AND RR >= 1.3; weight 1.0.
  thresholdpool the same rule with the control pooled over the other two
                actions ("better statistics, same decision bar").
  coin          the same |gamma| as graded, but the SIGN is drawn per
                epoch from the agent's own RNG and the ACTION is drawn
                per epoch from the same RNG: acts with probability |gamma|
                on an action that carries no information. The null
                device: it separates "the evidence is informative" from
                "acting at all pays".
  oracle        the epoch's action given free, weight 1 (ceiling).
  rot           tau = 0: never acts on a belief, always gathers (floor).

cache (Block F): 'fresh' clears the counts at every epoch change;
'carry' multiplies the previous epoch's counts by kappa at the change
(the found fact is reused at half weight, immediately, for free).

No world tokens: the module names actions only through the opaque
strings the observation carries, and it reads no world constant.
"""
import math
import random
from collections import defaultdict

PHI_SCALE = 1.0


def _ncdf(x):
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def gamma_of(z):
    """The two-sided-equivalent posterior mass: 0 when the evidence points
    the wrong way, rising to (but never reaching) 1 with the evidence."""
    return max(0.0, 2.0 * _ncdf(z) - 1.0)


def two_prop_z(h_a, n_a, h_o, n_o):
    """One-sided z of (rate_a - rate_o) with the PROPER two-proportion se
    (the turn-118/119 lesson: a p=0.5 bound inflates noise)."""
    if n_a <= 0 or n_o <= 0:
        return 0.0
    r_a, r_o = h_a / n_a, h_o / n_o
    se = ((r_a * (1 - r_a) / n_a) + (r_o * (1 - r_o) / n_o)) ** 0.5
    if se <= 0:
        return 0.0
    return (r_a - r_o) / se


def fisher_exact_2x2(a_yes, c_yes, a_no, c_no):
    """One-sided (greater) Fisher exact for [[a_yes, a_no],[c_yes, c_no]]
    -- byte-for-byte the rule the frozen v7 verifier uses."""
    n = a_yes + a_no + c_yes + c_no
    if n == 0:
        return 1.0
    r1, c1 = a_yes + a_no, a_yes + c_yes
    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)
    p = 0.0
    denom = math.comb(n, c1)
    for x in range(a_yes, hi + 1):
        p += math.comb(r1, x) * math.comb(n - r1, c1 - x) / denom
    return min(1.0, max(0.0, p))


MIN_N = 20          # the candidate's evidence bar (frozen, PREREG_V8 §2)
RR_ACCEPT = 1.3     # the campaign's frozen ratio gate (unchanged)


class AgentV8:
    def __init__(self, seed=0, mode="graded", tau=1.0, cache="fresh",
                 kappa=0.5):
        self.seed = int(seed)
        self.mode = mode
        self.tau = float(tau)
        self.cache = cache
        self.kappa = float(kappa)
        self.rng = random.Random(1000 + self.seed)
        # counts per action: [hits, trials]
        self.cnt = {a: [0, 0] for a in ("wait", "press", "grasp")}
        self.epoch_seen = 0
        self.t = 0
        self._rot = 0
        # --- belief state
        self.belief_action = None
        self.belief_gamma = 0.0
        self.belief_z = 0.0
        self._epoch_rng_action = None
        # --- bookkeeping / analysis
        self.epoch_log = []          # one row per epoch
        self.steps_gathering = 0
        self.steps_belief = 0
        self.steps_coin_belief = 0
        self._epoch_start_t = 0
        self._frozen_belief = None   # threshold mode: the frozen verdict
        self._z_hist = []
        self.bonus_steps_seen = 0
        self._first_call = True

    # ---------------- statistics from the agent's own counts ----------
    def _stats(self):
        """Return {action: (z, gamma, hits, trials, rate)} plus the
        pooled 'others' figures, all from the agent's own counts."""
        out = {}
        tot_h = sum(h for h, _ in self.cnt.values())
        tot_n = sum(n for _, n in self.cnt.values())
        for a, (h, n) in self.cnt.items():
            oh, on = tot_h - h, tot_n - n
            z = two_prop_z(h, n, oh, on)
            out[a] = (z, gamma_of(z), h, n, (h / n if n else 0.0))
        return out

    def _stats_single(self):
        """z against the FIRST other action alphabetically -- the frozen
        rule's contrast form."""
        keys = sorted(self.cnt)
        out = {}
        for a in keys:
            others = [b for b in keys if b != a]
            c = others[0]
            h, n = self.cnt[a]
            hc, nc = self.cnt[c]
            z = two_prop_z(h, n, hc, nc)
            out[a] = (z, gamma_of(z), h, n, (h / n if n else 0.0), c)
        return out

    # ---------------- belief formation (mode-specific) ----------------
    def _form_belief(self):
        if self.mode == "oracle":
            return                      # set externally per epoch
        if self.mode == "rot":
            self.belief_action, self.belief_gamma, self.belief_z = None, 0.0, 0.0
            return
        if self.mode in ("graded", "coin"):
            st = self._stats()
            best = None
            for a, (z, g, h, n, rate) in st.items():
                if n < MIN_N:
                    continue
                if best is None or z > st[best][0]:
                    best = a
            if best is None:
                self.belief_action, self.belief_gamma, self.belief_z = None, 0.0, 0.0
                return
            z, g = st[best][0], st[best][1]
            if self.mode == "coin":
                # the MAGNITUDE is real, the direction is a coin: the
                # acted action is drawn once per epoch from the agent's
                # own RNG and carries no information, while |gamma| --
                # and therefore the tendency to act at all -- is exactly
                # the graded arm's. This is the null device.
                self.belief_action = self._epoch_rng_action
                self.belief_gamma = g
                self.belief_z = z          # recorded for the analysis only
                return
            self.belief_action, self.belief_gamma, self.belief_z = best, g, z
            return
        if self.mode == "graded1":
            st = self._stats_single()
            best = None
            for a, (z, g, h, n, rate, c) in st.items():
                if n < MIN_N:
                    continue
                if best is None or z > st[best][0]:
                    best = a
            if best is None:
                self.belief_action, self.belief_gamma, self.belief_z = None, 0.0, 0.0
                return
            self.belief_action = best
            self.belief_gamma = st[best][1]
            self.belief_z = st[best][0]
            return
        if self.mode in ("threshold", "thresholdpool"):
            keys = sorted(self.cnt)
            cand = None
            for a in keys:
                h, n = self.cnt[a]
                if n < MIN_N:
                    continue
                if cand is None or (h / n) > (self.cnt[cand][0] / self.cnt[cand][1]):
                    cand = a
            if cand is None:
                self.belief_action, self.belief_gamma, self.belief_z = None, 0.0, 0.0
                return
            h, n = self.cnt[cand]
            others = [b for b in keys if b != cand]
            if self.mode == "threshold":
                c = others[0]
                hc, nc = self.cnt[c]
                z = two_prop_z(h, n, hc, nc)
            else:
                hc = sum(self.cnt[c][0] for c in others)
                nc = sum(self.cnt[c][1] for c in others)
                z = two_prop_z(h, n, hc, nc)
            self.belief_z = z
            r_a = h / n
            r_c = (hc / nc) if nc else 0.0
            rr = (r_a / r_c) if r_c > 0 else float("inf")
            p = fisher_exact_2x2(h, hc, n - h, nc - hc) if nc else 1.0
            if p < 0.05 and rr >= RR_ACCEPT:
                self.belief_action = cand
                self.belief_gamma = 1.0      # a verdict is certain
            else:
                self.belief_action = None
                self.belief_gamma = 0.0
            return
        raise ValueError(self.mode)

    # ---------------- the action ----------------
    def act(self, o):
        """Epoch bookkeeping (DEFECT FIX, turn 126, found by the
        independent verifier): the epoch a step belongs to is
        `o["epoch_id"]`, and the boundary must be handled HERE, before the
        step's trial is filed -- the earlier version detected the change
        one step later, so the last trial of each epoch was filed into the
        NEXT epoch's row (measured: epoch 0 logged 2001 trials instead of
        2000, and every boundary row was off by one). Reward totals, the
        gathering share and every cross-arm contrast are unaffected (they
        are per-run sums); the per-epoch battery is not."""
        self.t += 1
        eid = o["epoch_id"]
        if eid != self.epoch_seen or self._first_call:
            if not self._first_call:
                self._close_epoch()
            self._new_epoch(eid)
            self._first_call = False
        self._form_belief()
        if self.belief_action is not None and self.belief_gamma > 0:
            p_belief = min(1.0, self.tau * self.belief_gamma)
            if self.rng.random() < p_belief:
                self.steps_belief += 1
                if self.mode == "coin":
                    self.steps_coin_belief += 1
                    return self._epoch_rng_action
                return self.belief_action
        self.steps_gathering += 1
        self._rot += 1
        return ("wait", "press", "grasp")[self._rot % 3]

    def _new_epoch(self, eid):
        self.epoch_seen = eid
        self._epoch_start_t = self.t - 1
        if self.cache == "carry":
            for a in self.cnt:
                self.cnt[a][0] = int(self.cnt[a][0] * self.kappa)
                self.cnt[a][1] = int(self.cnt[a][1] * self.kappa)
        else:
            for a in self.cnt:
                self.cnt[a] = [0, 0]
        self._epoch_rng_action = self.rng.choice(sorted(self.cnt))
        self._rot = 0

    def _close_epoch(self):
        """Record the epoch's outcome for the analysis blocks (A, F)."""
        tot_n = sum(n for _, n in self.cnt.values())
        if tot_n == 0:
            self.epoch_log.append({"epoch": self.epoch_seen, "n": 0,
                                   "counts": {a: list(v) for a, v in
                                              self.cnt.items()},
                                   "belief": None, "gamma": 0.0, "z": 0.0})
            return
        self.epoch_log.append({
            "epoch": self.epoch_seen,
            "belief": self.belief_action,
            "gamma": round(self.belief_gamma, 5),
            "z": round(self.belief_z, 5),
            "counts": {a: list(v) for a, v in self.cnt.items()},
            "n": tot_n,
        })

    def observe(self, o, a, r, o2, done, info):
        self.cnt[a][1] += 1
        if r > 0:
            self.cnt[a][0] += 1
        if info.get("bonus"):
            self.bonus_steps_seen += 1
