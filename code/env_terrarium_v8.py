"""env_terrarium_v8.py -- TerrariumV8, the LIFETIME world (turn 126).

Authority: research/PREREG_V8.md (frozen before this file existed; the
re-specification from a room to a clocked bandit is its amendment A1,
each amendment carrying its reason).

THE WORLD IS A CLOCKED THREE-ACTION BANDIT. Deliberately minimal -- no
navigation, no survival, no prize ritual -- because the three claims of
this turn are about the DECISION RULE, the FEEDBACK of acting on a
belief, and REUSE:

  LIVENESS (C, F). The paying action is re-drawn every EPOCH_LEN steps.
  A 16000-step run holds 8 epochs: 8 independent facts to find.

  STICKINESS q (F). A new epoch repeats the previous epoch's action with
  probability exactly q; otherwise it is one of the two others,
  uniformly. q=0 -> a fresh fact every epoch; q=1 -> one fact forever.

  PERSISTENCE (A). If the same action was taken in >= 75% of the last 8
  steps, that action's payoff probability is multiplied by 1.25. This is
  what makes "acting on a belief produces the data that support it" a
  true statement about the WORLD rather than an artifact of the
  estimator -- the turn-115 pathology rebuilt as an object with a number
  (prereg A3, Block A's analytic factor 1.25*p_edge - p_bg).

  THE GAP. p_edge is a parameter against a fixed background p_bg = 0.35:
  0.55 (gap 0.20, above the campaign's frozen RR>=1.3 ratio gate), 0.45
  (0.10 -- ratio 1.286, JUST UNDER the gate), 0.40 (0.05), 0.38 (0.03).
  truth=off: p_bg for every action.

Observation (the agent's whole input): t, epoch_id, afford. The clock is
world state given identically to every arm; it never says WHICH action
pays.

Payoff on a step: K = 100.0 with probability p, where p = p_edge if the
taken action is the epoch's action (and truth), else p_bg, times the
persistence bonus when it applies. The reward the agent sees IS the
observation the agent counts -- declared in the prereg, so nothing can
drift between "what was observed" and "what was paid".

TWO INDEPENDENT RNG STREAMS (declared): epoch actions come from a
stream keyed on (seed, q) alone, payoffs from a different stream. The
epoch-action sequence is therefore a pure function of (seed, q) and can
be RECOMPUTED by an independent verifier from the seed alone -- without
replaying the payoff draws. This is the independent path, built into the
world rather than bolted on after the runs.
"""
import random

ACTIONS = ("wait", "press", "grasp")
K = 100.0
EPOCH_LEN = 2000
P_BG = 0.35
GAP_PEDGE = {"0.20": 0.55, "0.10": 0.45, "0.05": 0.40, "0.03": 0.38}
MOMENTUM_K = 8
MOMENTUM_SHARE = 0.75
MOMENTUM_BONUS = 0.25


def action_stream(seed, q, n_epochs, epoch_len=EPOCH_LEN):
    """The epoch-action sequence: a pure function of (seed, q).

    The verifier re-derives this from the frozen seed and compares it to
    the recorded trace; nothing else about the run is needed."""
    rng = random.Random(int(seed) * 7919 + 13)
    out = [ACTIONS[rng.randrange(len(ACTIONS))]]
    for _ in range(1, n_epochs):
        if rng.random() < q:
            out.append(out[-1])
        else:
            rest = [a for a in ACTIONS if a != out[-1]]
            out.append(rest[rng.randrange(len(rest))])
    return out


class TerrariumV8:
    def __init__(self, seed, gap="0.20", q=0.0, persistence=False,
                 truth=True, epoch_len=EPOCH_LEN, n_epochs=None):
        self.seed = int(seed)
        self.gap_key = gap
        self.p_edge = GAP_PEDGE[gap]
        self.p_bg = P_BG
        self.q = float(q)
        self.persistence = bool(persistence)
        self.truth = bool(truth)
        self.epoch_len = int(epoch_len)
        self.rng_pay = random.Random(int(seed) * 104729 + 7)
        self.n_epochs = int(n_epochs) if n_epochs else 8
        self.epoch_actions = action_stream(self.seed, self.q, self.n_epochs,
                                           self.epoch_len)
        self.t = 0
        self.epoch = 0
        self.hist = []
        self.steps = 0
        self.pays = 0
        self.bonus_steps = 0
        self.action_counts = {a: 0 for a in ACTIONS}

    # ---------------- clocks ----------------
    def _tick(self):
        e = self.t // self.epoch_len
        if e != self.epoch:
            self.epoch = e

    @property
    def epoch_action(self):
        return self.epoch_actions[min(self.epoch, len(self.epoch_actions) - 1)]

    def _momentum_share(self, action):
        h = self.hist[-MOMENTUM_K:]
        if not h:
            return 0.0
        return sum(1 for a in h if a == action) / len(h)

    def obs(self):
        # DEFECT FIX (turn 126, found by the independent verifier): the
        # clock must be advanced BEFORE the observation is built, so that
        # `epoch_id` names the epoch the NEXT step belongs to. The earlier
        # version returned the PREVIOUS step's epoch, so the agent (which
        # files under the epoch it is shown) put each epoch's last trial
        # into the next epoch's row while the runner tallied by the
        # step's own epoch -- two world-side quantities disagreeing.
        self._tick()
        return {"t": self.t, "epoch_id": self.epoch, "afford": list(ACTIONS)}

    def step(self, action):
        assert action in ACTIONS, action
        self._tick()
        info = {}
        r = 0.0
        p = self.p_edge if (self.truth and action == self.epoch_action) \
            else self.p_bg
        if self.persistence and self._momentum_share(action) >= MOMENTUM_SHARE:
            p *= (1.0 + MOMENTUM_BONUS)
            self.bonus_steps += 1
            info["bonus"] = True
        if self.rng_pay.random() < p:
            r += K
            self.pays += 1
            info["pay"] = True
        self.steps += 1
        self.action_counts[action] += 1
        self.hist.append(action)
        if len(self.hist) > 64:
            self.hist = self.hist[-64:]
        self.t += 1
        info["t"] = self.t
        info["epoch"] = self.epoch
        return self.obs(), r, False, info

    # ---------------- ground truth (documentation + oracle) ----------
    def true_edges(self):
        return {(self.epoch_action, "pay"): self.p_edge / self.p_bg} \
            if self.truth else {}

    def true_confounders(self):
        return {
            "liveness": f"the paying action is re-drawn every {self.epoch_len} steps",
            "stickiness": f"a new epoch repeats the old action with p={self.q}",
            "persistence": ("payoff probability x1.25 when the action filled "
                            ">=75% of the last 8 steps" if self.persistence
                            else "off"),
            "no_blind_fill": (f"background rate {self.p_bg} vs causal "
                              f"{self.p_edge} (truth={self.truth})"),
        }
