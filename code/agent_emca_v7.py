"""agent_emca_v7.py -- the SEPARABLE-EPISTEMICS arms (turn 118).

One lineage, one filing path; arms differ ONLY in the three things the
claims are about:

  GENERATION   -- is the candidate list a function of the agent's own
                  tables (candidate_gen.py) or a designer constant?
  VERIFICATION -- does a do-intervention verdict issued on those
                  SELF-GENERATED candidates reject the decoy?
  CHOICE       -- is "verify or exploit the permitted alternative"
                  computed from the agent's own epistemic state plus the
                  world's reward structure (arbitration.py), or scheduled?

ARM LINEAGE (all share the filing path, the exploration schedule, the
probe protocol, the survival competence, and the persistence across
deaths; the ONLY differences are generator / beta / permutation /
injection -- declared in research/PREREG_V7.md):

  AgentV7Full     -- self-generated candidates, beta=1, verifier on.
  AgentV7Beta0    -- same, beta=0 (the hardcode control: must not probe).
  AgentV7Perm     -- same, candidate scores permuted by seed (the
                     computed-decision control: must follow the permuted
                     argmax).
  AgentV7NoGen    -- the generator REPLACED by a fixed designer list
                     (behaviour as in v6; the hidden-hardcode control).
  AgentV7Oracle   -- the true edge INJECTED at t=2000 (analysis device:
                     the edge's gross value; never in fairness verdicts).
  AgentV7Forager  -- no generator, no verifier, no arbiter: greedily
                     stands on the permitted alternative (the reward
                     floor).
  RandomAgent     -- brute force (baselines.py).

WORLD-AGNOSTICISM: the agent never names an action or an effect. It
files whatever effects its observations carry (flags that are True) under
the action it took and the context it was in; the generator works on
those opaque strings. The only world-shaped inputs are the observable
`phase`, the view characters it navigates by, and the scent landmarks --
the same shared navigation knowledge every arm in the campaign has had.
"""
import math
from collections import defaultdict

from candidate_gen import generate, permute
import arbitration

from baselines import RandomAgent  # re-exported for the runner

MOVES = ("up", "down", "left", "right")
NONMOVE = ("wait", "press", "grasp")
ACTIONS = MOVES + NONMOVE
MOVE_DELTA = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

EXPLORE_END = 3000         # shared exploration schedule (prereg §3)
EXPLORE_DWELL = 60         # steps spent at each waypoint before rotating
STATION_DWELL = 420        # the aura data-gathering dwell (generator bar)
PROBE_BLOCK = 5            # alternated blocks of 5 target / 5 control
PROBE_MAX_BLOCKS = 80      # cap per candidate (~800 scheduled trials)
P_VERDICT = 0.05
RR_ACCEPT = 1.3
LOW_ENERGY = 35.0          # the shared survival threshold
# BOOKKEEPING flags the HARNESS puts in info: they describe the agent's
# own body/clock, not a world effect a cause could produce. Excluded from
# the filed tables for EVERY arm (declared; the world's epistemic flags
# are never named here -- the exclusion is by the harness's known keys).
HARNESS_KEYS = ("died", "t")


def _binocdf(k, n, p):
    """P(X <= k) for X ~ Binomial(n, p) -- exact, no scipy."""
    s = 0.0
    for i in range(0, k + 1):
        s += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return s


def fisher_exact_2x2(a_yes, c_yes, a_no, c_no):
    """One-sided (greater) Fisher exact for [[a_yes, a_no],[c_yes, c_no]]:
    P(target rate > control rate). Small exact sum over the hypergeometric;
    used identically to v3.2/v3.3/v6."""
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


class AgentV7Base:
    """The shared machinery. Subclasses flip generator/beta/permutation."""

    USE_GENERATOR = True
    BETA = 1.0
    PERMUTE_SEED = None
    INJECT_EDGE = None       # ("action","effect") injected at t>=2000
    USE_VERIFIER = True
    GREEDY_RICH = False      # forager

    def __init__(self, seed=0):
        self.seed = seed
        self.rng = __import__("random").Random(seed)
        self.t = 0
        # own tables: ctx -> action -> effect -> [hits, trials]
        self.ctx_tab = defaultdict(lambda: defaultdict(lambda: defaultdict(
            lambda: [0, 0])))
        self.verdicts = {}          # (action, effect) -> dict
        # PROBE LOG, PHASE-KEYED (turn-120 fix, all arms equally): the
        # do-intervention compares target vs control WITHIN the same
        # observable phase. Pooling across phases was the seed-2 false
        # positive: the decoy effect is a phase-gated world event, and
        # an unequal warm/cold split between the two arms made it look
        # exclusive (measured: target warm 0.556 vs ctrl 0.505, but
        # pooled 0.375 vs 0.344 -> p=0.026, RR=1.33 -> CAUSAL). Phase is
        # observable (shared navigation knowledge); no world tokens.
        self.probe_state = None
        self._probe_mark = None
        self.probe_log = defaultdict(lambda: {"target": defaultdict(
            lambda: [0, 0]), "ctrl": defaultdict(lambda: [0, 0])})
        self.probe_state = None
        self.probe_trials = 0
        self.probe_blocks_done = 0
        self.candidates_seen = []   # last generated list (for analysis)
        self.n_candidates_total = 0
        self._last_ranked = []
        # ANALYSIS FIELDS (turn 120): recorded so the independent verifier
        # can rebuild C1-ii (does the FIRST probe follow the ranked list?)
        # and the oracle decomposition from the JSON alone.
        self.first_probe = None     # (action, effect, rank_in_list, n_list)
        self.ranked_at_first_probe = None
        self.probe_order_log = []   # (action, effect, ranked_list_at_start)
        self.first_causal_t = None  # t of the first CAUSAL verdict
        self.rich_steps_agent = 0
        # observed alternative payoff (the agent's own reward stream)
        self.rich_reward = 0.0
        self.rich_steps = 0
        self.rich_rate_obs = 0.0
        # exploration bookkeeping
        self._explore_wp = 0
        self._dwell = 0
        self._rot = 0
        self._exploit_streak = None
        self._last_verdict_t = None
        self.log_extra = {}

    # ---------------- features (generic, world-agnostic names) --------
    def _feat(self, o):
        v = o["view"]
        c = v[4]
        f = {
            "in_aura": ("S" in v) or ("F" in v),
            "on_station": c in ("S", "F"),
            "on_rich": c == "R",
            "on_berry": c == "b",
            "phase": o["phase"],
            "energy": o["energy"],
            "afford": set(o["afford"]),
            "fruit_in_view": "F" in v,
            "rich_in_view": "R" in v,
            "berry_in_view": "b" in v,
        }
        f["ctx"] = (f["in_aura"],)   # the context a cause can live in
        return f

    # ---------------- navigation (shared, scent-based) ----------------
    def _nav(self, scent, key, f):
        g = (scent or {}).get(key)
        if not g:
            return None
        order = ("up", "down", "left", "right")
        for d in sorted(g, key=lambda k: (g[k], order.index(k) if k in order else 9)):
            if g[d] < 0 and d in f["afford"]:
                return d
        return None

    # ---------------- survival (shared) -------------------------------
    def _survival(self, o, f):
        """Returns a move/eat action when energy pressure rules, else None.
        Identical for every arm (prereg §3)."""
        if f["on_berry"] and "wait" in f["afford"]:
            return "wait"                       # stand to eat the berry
        if f["energy"] < LOW_ENERGY:
            if f["on_rich"] and "wait" in f["afford"]:
                return "wait"                   # rich tile also heals nothing,
                                                # but berry scent was preferred
            s = self._nav(o.get("scent"), "berry", f)
            if s:
                return s
        # opportunistic berry eat when passing
        if f["on_berry"]:
            return "wait" if "wait" in f["afford"] else None
        return None

    # ---------------- generation --------------------------------------
    def _candidates(self):
        if not self.USE_GENERATOR:
            # the v6-style designer list: the hidden-hardcode control
            return [self._designer_candidate()]
        table = self._agent_table()
        cands = generate(table, ACTIONS)
        if self.PERMUTE_SEED is not None:
            cands = permute(cands, self.PERMUTE_SEED)
        if self.INJECT_EDGE is not None and self.t >= EXPLORE_END:
            from candidate_gen import Candidate
            a, e = self.INJECT_EDGE
            if not any(c.action == a and c.effect == e for c in cands):
                cands = [Candidate(a, e, "injected", 0.3, 0.2, 999, 0.10)] + cands
        return cands

    def _agent_table(self):
        """The agent's OWN two-level table, built from ctx_tab:
        a per-context table (the true-edge contrast) and a pooled
        table (the context-merging decoy contrast). The trial
        denominator is the TRUE attempt count per (ctx, action), tracked
        separately from effect firings."""
        ctx_table = {}
        for ctx, acts in self.ctx_tab.items():
            t = {}
            for a, effs in acts.items():
                n = effs.get("__trial__", [0, 0])[1]
                if n <= 0:
                    continue
                t[a] = {e: [h, n] for e, (h, _n) in effs.items()
                        if e != "__trial__"}
            if t:
                ctx_table[ctx] = t
        return ctx_table

    def _designer_candidate(self):
        """The fixed list a v6-style arm would probe -- it names the
        designer's chosen action and effect, NOT the agent's data."""
        from candidate_gen import Candidate
        if self.t < EXPLORE_END:
            return None
        return Candidate("wait", "hum", "designer", 0.3, 0.2, 999, 0.10)

    # ---------------- the arbiter -------------------------------------
    def _plan(self):
        cands = self._candidates()
        cands = [c for c in cands if c is not None]
        self.candidates_seen = [(c.action, c.effect, c.score, c.trials)
                                for c in cands]
        self.n_candidates_total = len(cands)
        unprobed = [c for c in cands if (c.action, c.effect) not in self.verdicts]
        if not self.USE_VERIFIER:
            return arbitration.Plan([], [], 0.0, self.rich_rate_obs)
        p = arbitration.plan(unprobed, self.rich_rate_obs, beta=self.BETA)
        self._last_ranked = [(c.action, c.effect, c.score, c.trials)
                             for c in cands]
        if p.probe_order and self.first_probe is None:
            self.first_probe = (p.probe_order[0].action,
                                p.probe_order[0].effect)
            self.ranked_at_first_probe = list(self._last_ranked)
        return p

    # ---------------- probe machinery ---------------------------------
    def _start_probe(self, cand, f):
        # control: the first non-move alphabetically that is not the target
        ctrl = next((a for a in sorted(NONMOVE) if a != cand.action), None)
        if ctrl is None:
            return False
        # C1-ii ANALYSIS: log this probe start with the ranked list as it
        # existed now (the decision must follow the permuted ranking).
        self.probe_order_log.append(
            (cand.action, cand.effect, list(self._last_ranked)))
        self.probe_state = {"cand": cand, "ctrl": ctrl, "arm": "target",
                            "n_block": 0, "blocks": 0}
        return True

    def _probe_act(self, o, f):
        st = self.probe_state
        if st is None:
            return None
        if not f["in_aura"]:
            s = self._nav(o.get("scent"), "station", f)
            return s if s else None       # (None -> caller falls through)
        arm = st["arm"]
        act = st["cand"].action if arm == "target" else st["ctrl"]
        # PHASE FAIRNESS (toy fix, all arms equally): a decoy action is
        # affordable only in warm; if the paired control keeps accruing
        # trials in cold (where no glow can fire) the Fisher test is
        # biased toward accepting the decoy. If EITHER arm's action is
        # unaffordable now, this step scores for NEITHER -- a benign
        # non-move that keeps the blocks honest (block boundaries only
        # advance on scheduled steps).
        other = st["ctrl"] if arm == "target" else st["cand"].action
        if act not in f["afford"] or other not in f["afford"]:
            return "wait" if "wait" in f["afford"] else None
        st["n_block"] += 1
        if st["n_block"] >= PROBE_BLOCK:
            st["n_block"] = 0
            st["blocks"] += 1
            st["arm"] = "ctrl" if arm == "target" else "target"
            if st["blocks"] >= PROBE_MAX_BLOCKS:
                self._finish_probe()
        self.probe_trials += 1
        # EXPLICIT SCHEDULED-STEP MARKER (turn-120 fix, all arms equally):
        # scoring must be driven by "this step WAS a scheduled probe step",
        # not by comparing the action string -- the candidate action can
        # coincide with the decoy action and with other actions the agent
        # takes (fruit-eat, fall-through), which leaked unscored-by-intent
        # trials into an arm (measured seed 8: candidate action == decoy
        # action == 'wait', target 0.5625 vs ctrl 0.4125 -> false CAUSAL).
        self._probe_mark = (arm, act, f["phase"])
        return act

    def _finish_probe(self):
        st = self.probe_state
        key = (st["cand"].action, st["cand"].effect)
        log = self.probe_log[key]
        # PHASE-CONDITIONAL VERDICT (turn-120 fix, all arms equally): the
        # do-intervention is evaluated INSIDE the phase that actually
        # carries the effect (the stratum with the most effect firings
        # across both arms). Pooling phases let an unequal warm/cold
        # split between target and control fake exclusivity for a
        # phase-gated world event. World-agnostic: the stratum is chosen
        # from observed counts only.
        phases = sorted(set(log["target"]) | set(log["ctrl"]))
        strata = {}
        for ph in phases:
            ty, tn = log["target"][ph]
            cy, cn = log["ctrl"][ph]
            strata[ph] = (ty, tn, cy, cn)
        if not strata:
            self.verdicts[key] = {"verdict": "UNRESOLVED", "p": 1.0,
                                  "rr": 0.0, "target_yes": 0, "target_no": 0,
                                  "ctrl_yes": 0, "ctrl_no": 0,
                                  "blocks": st["blocks"]}
            self.probe_state = None
            self.probe_blocks_done += 1
            return
        active = max(strata, key=lambda ph: (min(strata[ph][0] + strata[ph][1],
                                                strata[ph][2] + strata[ph][3]),
                                             strata[ph][0] + strata[ph][2]))
        ty, tn, cy, cn = strata[active]
        if (ty + tn) == 0 or (cy + cn) == 0:
            self.verdicts[key] = {"verdict": "UNRESOLVED", "p": 1.0,
                                  "rr": 0.0, "target_yes": ty, "target_no": tn,
                                  "ctrl_yes": cy, "ctrl_no": cn,
                                  "blocks": st["blocks"], "phase": active}
            self.probe_state = None
            self.probe_blocks_done += 1
            return
        p = fisher_exact_2x2(ty, cy, tn, cn)
        ra = ty / (ty + tn)
        rc = cy / (cy + cn) if (cy + cn) else 0.0
        rr = (ra / rc) if rc > 0 else (float("inf") if ra > 0 else 0.0)
        if p < P_VERDICT and rr >= RR_ACCEPT:
            verdict = "CAUSAL"
        elif p < P_VERDICT and rr < RR_ACCEPT:
            verdict = "REJECT"
        elif p >= P_VERDICT and rr < RR_ACCEPT:
            verdict = "REJECT"
        else:
            verdict = "UNRESOLVED"
        self.verdicts[key] = {
            "verdict": verdict, "p": round(p, 5),
            "rr": round(rr, 3) if rr != float("inf") else "inf",
            "target_yes": ty, "target_no": tn, "ctrl_yes": cy,
            "ctrl_no": cn, "blocks": st["blocks"], "phase": active}
        self.probe_state = None
        self.probe_blocks_done += 1
        self._last_verdict_t = self.t
        if verdict == "CAUSAL" and self.first_causal_t is None:
            self.first_causal_t = self.t

    # ---------------- exploration schedule (shared) -------------------
    def _explore(self, o, f):
        """Rotating waypoints: rich (sample the alternative payoff),
        aura (try varied actions -> data for the generator), berry.

        TOY FIX (turn-118/119, all arms equally): _explore_wp was never
        advanced, so the agent dwelt at the FIRST waypoint forever and
        never sampled the aura -- the generator then had no in-context
        data at all. The waypoint now advances when each dwell expires."""
        wps = ["rich", "station", "berry"]
        key = wps[self._explore_wp % len(wps)]
        at_wp = {"rich": f["on_rich"], "station": f["in_aura"],
                 "berry": f["on_berry"]}[key]
        if self._dwell <= 0 and at_wp:
            # the station visit is the DATA-GATHERING visit for the
            # generator (C2), so it dwells longer than the others --
            # equal for every arm (PREREG §5: longer aura dwell).
            self._dwell = (STATION_DWELL if key == "station"
                           else (30 if key == "berry" else EXPLORE_DWELL))
        if self._dwell > 0:
            self._dwell -= 1
            if self._dwell == 0:
                self._explore_wp += 1      # next waypoint on the next step
                return None
            if key == "station" and f["in_aura"]:
                # rotate the non-move actions to sample the aura (only
                # those currently affordable -- the decoy action is
                # phase-gated; turn-120 fix)
                aff = [a for a in NONMOVE if a in f["afford"]]
                if not aff:
                    return None
                self._rot += 1
                return aff[self._rot % len(aff)]
            if key in ("rich", "berry") and at_wp \
                    and "wait" in f["afford"]:
                return "wait"
        s = self._nav(o.get("scent"), key, f)
        return s

    # ---------------- acting ------------------------------------------
    def act(self, o):
        f = self._feat(o)
        surv = self._survival(o, f)
        if surv is not None:
            return surv
        # an in-progress probe owns the agent (turn-120 fix: it must come
        # BEFORE the fruit-eat branch -- when the candidate action is
        # "wait", the auto fruit-eat also returns "wait" and leaked
        # unscored-by-intent trials into the probe's target arm, faking
        # exclusivity for a phase-gated decoy; measured seed 8: wait->glow
        # target 0.5625 vs ctrl 0.4125 -> false CAUSAL).
        if self.probe_state is not None:
            a = self._probe_act(o, f)
            if a is not None:
                return a
            # fall through when the probe returned None (out of aura,
            # nothing to do) -- the plan/explore layer will move it back
        # sight-shared prize: eat a bloomed fruit when standing on it
        if f["on_station"] and f["fruit_in_view"] and "wait" in f["afford"]:
            return "wait"
        if self.GREEDY_RICH:
            if f["on_rich"] and "wait" in f["afford"]:
                return "wait"
            s = self._nav(o.get("scent"), "rich", f)
            return s if s else self.rng.choice(MOVES)
        if self.t < EXPLORE_END:
            a = self._explore(o, f)
            if a is not None:
                return a
            return self.rng.choice(MOVES)
        # ---- post-exploration: the arbiter decides ----------------
        plan = self._plan()
        if plan.probe_order:
            cand = plan.probe_order[0]
            if self._start_probe(cand, f):
                a = self._probe_act(o, f)
                if a is not None:
                    return a
        # no candidate clears the bar -> exploit what we know
        accepted = [k for k, v in self.verdicts.items()
                    if v["verdict"] == "CAUSAL"]
        if accepted and not plan.probe_order:
            # EXPLOITATION (turn-120 fix, all arms equally): the verified
            # effect is obtained by repeating the verified action AT THE
            # STATION LANDMARK (the shared scent the agent has always
            # navigated by). The earlier version repeated the action
            # wherever the agent happened to be in the aura, so it never
            # stood on the station cell and the prize could never be
            # collected (measured: 93 blooms, 0 eaten, reward ~3). Now the
            # agent walks to the station and repeats the action there --
            # generic "obtain the effect we verified we can cause".
            a0 = sorted(accepted)[0][0]
            if f["on_station"] and a0 in f["afford"]:
                return a0
            s = self._nav(o.get("scent"), "station", f)
            if s:
                return s
        # otherwise: the permitted alternative
        if f["on_rich"] and "wait" in f["afford"]:
            return "wait"
        s = self._nav(o.get("scent"), "rich", f)
        if s:
            return s
        return self.rng.choice(MOVES)

    # ---------------- observing ---------------------------------------
    def observe(self, o, a, r, o2, done, info):
        self.t += 1
        f1 = self._feat(o)
        # CONTEXT ATTRIBUTION (turn-118/119 fix, all arms equally): the
        # world fires an aura effect from the position AFTER the move,
        # but `o` is the PRE-move view. Filing under the pre-move view
        # leaked hum into the outside context whenever a move crossed the
        # aura boundary (measured: hum 32/798 in the outside context),
        # which is what made the truth=off in-context nomination non-zero.
        # The agent has `o2` (its own post-action view), so the effect is
        # filed under the context it actually occurred in -- world-agnostic
        # (no tokens), identical for every arm.
        ctx = self._feat(o2)["ctx"] if o2 else f1["ctx"]
        # file the trial
        self.ctx_tab[ctx][a]["__trial__"][1] += 1
        # file every effect the world reported (opaque strings); the
        # harness's own bookkeeping flags are not world effects
        effects = sorted(k for k in info
                         if info[k] is True and k not in HARNESS_KEYS)
        for e in effects:
            c = self.ctx_tab[ctx][a].setdefault(e, [0, 0])
            c[0] += 1
            c[1] += 1
        # observed alternative payoff (the agent's own reward stream)
        if a in NONMOVE and f1["on_rich"] and r > 0:
            self.rich_reward += r
            self.rich_steps += 1
            self.rich_rate_obs = self.rich_reward / self.rich_steps        # score an in-progress probe trial (PHASE-KEYED, MARKER-DRIVEN --
        # turn-120 fix: only steps that the probe SCHEDULED are scored,
        # never steps the agent took for another reason)
        mark = getattr(self, "_probe_mark", None)
        self._probe_mark = None
        st = self.probe_state
        if st is not None and mark is not None:
            key = (st["cand"].action, st["cand"].effect)
            log = self.probe_log[key]
            hit = info.get(st["cand"].effect) is True
            arm_mark, act_mark, ph = mark
            if arm_mark == "target":
                log["target"][ph][0 if hit else 1] += 1
            elif arm_mark == "ctrl":
                log["ctrl"][ph][0 if hit else 1] += 1
        if info.get("died"):
            self.deaths = getattr(self, "deaths", 0) + 1
        # the injected-edge oracle device
        if self.INJECT_EDGE is not None and self.t >= EXPLORE_END:
            k = self.INJECT_EDGE
            if k not in self.verdicts:
                self.verdicts[k] = {"verdict": "CAUSAL", "p": 0.0,
                                    "rr": 1.5, "injected": True,
                                    "target_yes": 0, "target_no": 0,
                                    "ctrl_yes": 0, "ctrl_no": 0,
                                    "blocks": 0}


class AgentV7Full(AgentV7Base):
    pass


class AgentV7Beta0(AgentV7Base):
    BETA = 0.0


class AgentV7Perm(AgentV7Base):
    def __init__(self, seed=0):
        super().__init__(seed)
        self.PERMUTE_SEED = 1000 + seed


class AgentV7NoGen(AgentV7Base):
    USE_GENERATOR = False


class AgentV7Oracle(AgentV7Base):
    def __init__(self, seed=0, edge=("wait", "hum")):
        super().__init__(seed)
        self.INJECT_EDGE = edge


class AgentV7Forager(AgentV7Base):
    USE_VERIFIER = False
    GREEDY_RICH = True

    def _candidates(self):
        return []


class AgentV7Random(RandomAgent):
    pass