"""agent_v15.py -- the SEAM agent.

Representation-space prediction (JEPA) + epistemic action selection with
NO prior preferences (active inference minus priors) + a CONTEXT INDEX
(the campaign's v3-v9 specificity).

There is NO reward, NO energy, NO death and NO preferred state in this
file. The agent's only quantity is the expected information gain of its
OWN model. No line of code knows what is "good". The one design
parameter that is NOT epistemic is `ig_eps`, the information threshold
below which the agent declares "nothing left to learn" and therefore has
no reason to act -- that threshold is a criterion, and the prereg
declares it as such.
"""
import math

ACTIONS = ("a0", "a1", "a2", "a3")
REL_MARGIN = 0.20


def _logbeta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _beta_pdf(x, a, b):
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return math.exp((a - 1.0) * math.log(x) + (b - 1.0) * math.log(1.0 - x)
                    - _logbeta(a, b))


def bern_entropy(p):
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))


def beta_bernoulli_ig(a, b, grid=256):
    """Expected information gain (nats) of one more Bernoulli draw about
    theta ~ Beta(a,b): H(pred) - E_theta[H(theta)]. Zero when the
    posterior is certain; ~0.19 for Beta(1,1)."""
    mean = a / (a + b)
    h_pred = bern_entropy(mean)
    s = 0.0
    w = 0.0
    for i in range(1, grid):
        x = i / grid
        pdf = _beta_pdf(x, a, b)
        s += pdf * bern_entropy(x)
        w += pdf
    if w <= 0.0:
        return 0.0
    return max(0.0, h_pred - s / w)


class AgentV15:
    def __init__(self, mode, discount=0.99, ig_eps=0.01, oracle=False):
        assert mode in ("rand", "naive_info", "ig_ctx", "ig_pooled", "confirm",
                        "ig_relevant")
        self.mode = mode
        self.discount = discount
        self.ig_eps = ig_eps
        self.counts = {}
        self.visits = {a: 0 for a in ACTIONS}
        self.last_unmotivated = False
        if oracle:
            self._seed_oracle()

    def _seed_oracle(self, n=400.0):
        """Analysis device only: pre-fill the model with the TRUE rates so
        the metric's ceiling can be measured. Never in a fairness verdict."""
        for phase, rate in (("A", 0.9), ("B", 0.1)):
            self.counts[(phase, "a0")] = (1.0 + rate * n, 1.0 + (1.0 - rate) * n)

    def _key(self, phase, action):
        if self.mode == "ig_pooled":
            return ("*", action)
        return (phase, action)

    def _ab(self, key):
        return self.counts.get(key, (1.0, 1.0))

    def predict(self, phase, action):
        a, b = self._ab(self._key(phase, action))
        return a / (a + b)

    def _score(self, phase, action):
        key = self._key(phase, action)
        a, b = self._ab(key)
        if self.mode == "naive_info":
            return bern_entropy(a / (a + b))
        if self.mode == "confirm":
            p = a / (a + b)
            return -min(p, 1.0 - p)
        if self.mode == "ig_relevant":
            # THE CRITERION ARM. Pure IG is not enough to steer action
            # once truth is learned (see RESULTS_V15): every channel's
            # IG decays to the same floor. To prefer the TRUE channel the
            # agent must add a second term -- "which channel's rate
            # DIFFERS ACROSS CONTEXTS" -- i.e. a relevance criterion.
            # That criterion is a preference over which states matter,
            # and it is exactly what the seam question asks about.
            if not self._relevant(action):
                return 0.0
            return beta_bernoulli_ig(a, b)
        return beta_bernoulli_ig(a, b)

    def _relevant(self, action):
        """Context-contrast relevance, computed from the agent's own
        tables: a channel is 'relevant' if its learned rate in A and B
        differ by more than REL_MARGIN. This is a criterion the agent
        imposes on the world -- not information, but preference."""
        if self.mode != "ig_relevant":
            return True
        pa = self.predict("A", action)
        pb = self.predict("B", action)
        return abs(pa - pb) > REL_MARGIN

    def choose(self, phase, rng):
        self.last_unmotivated = False
        if self.mode == "rand":
            return rng.choice(ACTIONS)
        scores = {a: self._score(phase, a) for a in ACTIONS}
        best = max(scores.values())
        if self.mode in ("ig_ctx", "ig_pooled") and best < self.ig_eps:
            self.last_unmotivated = True
            return rng.choice(ACTIONS)
        cands = [a for a in ACTIONS if scores[a] == best]
        cands.sort(key=lambda a: (self.visits[a], a))
        return cands[0]

    def observe(self, phase, action, val):
        key = self._key(phase, action)
        a, b = self._ab(key)
        a = 1.0 + (a - 1.0) * self.discount
        b = 1.0 + (b - 1.0) * self.discount
        if val:
            a += 1.0
        else:
            b += 1.0
        self.counts[key] = (a, b)
        self.visits[action] += 1