"""Terrarium v7 -- the SEPARABLE-EPISTEMICS world (turn 118, msg_00118).

Why a NEW minimal world instead of a v6 heir (declared deviation in
research/PREREG_V7.md): V7 must separate three claims that the whole
campaign has carried MIXED --

  C2 GENERATION  -- the set of hypotheses to verify is a FUNCTION OF THE
                    AGENT'S OWN TABLES (candidate_gen.py), not a
                    constant in the code. In every earlier world the
                    probed edge was named by the designer (v6's
                    gray_edges() literally appends SPRING_EDGE).
  C3 VERIFICATION -- a do-intervention verdict issued on SELF-GENERATED
                    candidates, with the false-positive count measured
                    against a decoy that IS in that self-generated list.
  C1 CHOICE      -- the decision "verify or exploit the permitted
                    alternative" is COMPUTED from the agent's own
                    epistemic state and the world's reward structure,
                    not scheduled.

The v6 stack (v2+v3+v4+v5+v6 mixins) is deliberately NOT inherited: a
generator that must be audited for world-agnosticism and an arbiter
that must be audited line by line are cleaner in a small world with a
small, explicit interface. The deviation is frozen in the prereg before
any run.

THE WORLD (11x11 open room, no walls -- navigation is not the subject):
  * STATION 'S' at (5,5); its AURA is the 3x3 around it (containing
    the station cell itself). Two effects live in the aura only:
      hum  -- the TRUE GREY CAUSE (truth=on): P(hum | edge_action) =
              0.30 vs P(hum | any other action) = 0.20 -> RR = 1.5, the
              GREY zone (the campaign's stratified gate RR>=2 cannot
              take it, pooled over ALL contexts is diluted by the
              outside-aura zeros; the CONTEXT (in-aura) contrast is
              exactly 1.5 -- still grey). With truth=off P(hum) = 0.25
              for EVERY action: no edge at all.
      glow -- the DECOY (decoy=on): P = 0.50 in the WARM phase and 0 in
              the cold phase, for EVERY action in the aura -- a pure
              world event. decoy_action is affordable ONLY in warm, so
              the within-aura pooled contrast decoy_action->glow looks
              exclusive (0.50 vs 0.50*warm_share ~ 0.25); inside the
              warm context alone every action is equal -> the
              do-intervention (alternating blocks in the aura) rejects
              it. This is the campaign's decoy anatomy rebuilt small.
    edge_action is RANDOMISED BY SEED over (wait, press, grasp) -- the
    anti-hardcode core: no agent can "know" which action is the cause.
  * THE POOL (the prize route). In the aura: a hum fills +3, a no-hum
    step drains -1; the pool is FROZEN outside the aura. Pool >= 24
    blooms the fruit 'F' on the station cell (+50 reward, +60 energy,
    eaten by any non-move action while standing there; lives 80 steps;
    then the station sleeps 2000). Arithmetic: the true action nets
    0.30*3 - 0.70 = +0.20/step; ANY blind blend nets <= 3*0.25 - 0.75
    = 0.00/step -- blind patience and brute force structurally cannot
    fill the vessel. Only the causal action can.
  * THE PERMITTED ALTERNATIVE -- the rich patch 'R' at (2,8): any
    non-move action while standing on it yields rich_rate per step
    (0.05 = "low", 0.60 = "high"). This is the alternative the agent is
    ALLOWED to choose instead of verifying: probing costs the steps it
    could have spent standing there. The C1 conflict lives here.
  * Survival (a SHARED competence, identical for every arm): -0.05
    energy/step; -0.05 extra for a non-move action in the aura; berries
    ('b', 7 tiles) restore +10 by standing on them (each regenerates
    300 steps after being eaten); death at 0 energy. The economy is
    gentle on purpose: the claims are epistemic, not metabolic; but
    foraging trips cost real steps, so probing is never free.

Observation (the agent's whole input):
  view (3x3 row-major string, centre = the agent), energy, afford (the
  actions currently available), phase ("warm"/"cold"), pos, and scent
  {station: {dir: delta}, rich: {dir: delta}, berry: {dir: delta}} --
  world knowledge of WHERE the landmarks are (shared by every arm,
  exactly as in v4-v6). The POOL IS NOT OBSERVABLE; the fruit ('F') is
  (sight is shared; what blooms it is the dispute).

The world is a PARAMETERISED object (truth / decoy / rich / seed), so
the same code yields the regimes the three claims need; every regime is
oracle-verified (verify_env_v7.py) before any agent runs.
"""
import random

W = H = 11
MOVES = ("up", "down", "left", "right")
NONMOVE = ("wait", "press", "grasp")
ACTIONS = MOVES + NONMOVE
STATION = (5, 5)
RICH = (2, 8)
BERRY_TILES = ((1, 1), (3, 2), (7, 9), (9, 4), (4, 8), (8, 1), (2, 5))

P_HUM_BG = 0.35            # P(hum | any action but the cause, truth=on)
P_HUM_EDGE = 0.60          # P(hum | the cause) -- RR = 1.71, GREY
P_HUM_FLAT = 0.40          # truth=off: one rate for every action
P_GLOW_WARM = 0.50         # the decoy: a world event, action-independent
POOL_GAIN = 1              # SMALL jumps vs the threshold: the pool is
POOL_DRAIN = 1             # DRIFT-dominated, not noise-dominated (NV7)
FRUIT_NEED = 24
FRUIT_REWARD = 50.0
FRUIT_ENERGY = 60.0
FRUIT_LIFE = 80
FRUIT_COOLDOWN = 2000

BERRY_ENERGY = 10.0
BERRY_REGEN = 300
ENERGY_COST = 0.05
AURA_NONMOVE_COST = 0.05

PHASE_SPAN = 600
RICH_RATES = {"low": 0.05, "high": 0.60}
EDGE_CHOICES = ("wait", "press", "grasp")

# flags that are WORLD EVENTS of the epistemic kind (the agent files
# these); bookkeeping flags ('died', 't') are excluded by the agent


def pick_edge_action(seed):
    """The TRUE cause is a function of the SEED, not of the code: the
    anti-hardcode control (prereg C2)."""
    return EDGE_CHOICES[int(seed) % 3]


def pick_decoy_action(seed):
    ea = pick_edge_action(seed)
    rest = [a for a in EDGE_CHOICES if a != ea]
    return rest[(int(seed) // 3) % len(rest)]


class TerrariumV7:
    """One life may end in death; the RUNNER respawns a fresh world and
    keeps the agent (persistence: the agent's tables, candidates and
    verdicts are the point of the claims, so they survive)."""

    def __init__(self, seed, truth=True, decoy=True, rich="low",
                 edge_action=None, decoy_action=None,
                 phase_span=PHASE_SPAN):
        self.seed = int(seed)
        self.rng = random.Random(self.seed)
        self.truth = bool(truth)
        self.decoy = bool(decoy)
        self.rich_mode = rich
        self.rich_rate = RICH_RATES[rich]
        self.edge_action = edge_action or pick_edge_action(self.seed)
        self.decoy_action = decoy_action or pick_decoy_action(self.seed)
        if self.decoy_action == self.edge_action:
            self.decoy_action = [a for a in EDGE_CHOICES
                                 if a != self.edge_action][0]
        self.phase_span = phase_span
        self.t = 0
        self.energy = 100.0
        self.pos = (9, 9)
        self.alive = True
        self.pool = 0
        self.fruit = False
        self.fruit_fuel = 0
        self.cooldown = 0
        self.berry_gone = {c: 0 for c in BERRY_TILES}
        # counters
        self.hums = 0
        self.glows = 0
        self.fruits_eaten = 0
        self.fruit_blooms = 0
        self.rich_total = 0.0
        self.berry_eats = 0
        self.aura_steps = 0

    # ---------------- geometry / phase / affordance ----------------
    def _in_aura(self, pos=None):
        r, c = pos or self.pos
        return abs(r - STATION[0]) <= 1 and abs(c - STATION[1]) <= 1

    @property
    def phase(self):
        return "warm" if (self.t // self.phase_span) % 2 == 0 else "cold"

    def _affordable(self, action):
        if action in MOVES:
            return True
        if self.decoy and action == self.decoy_action:
            return self.phase == "warm"
        return True

    def afford(self):
        return [a for a in ACTIONS if self._affordable(a)]

    # ---------------- observation ----------------
    def obs(self):
        r, c = self.pos
        chars = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    chars.append(".")
                    continue
                if (rr, cc) == STATION:
                    chars.append("F" if self.fruit else "S")
                elif (rr, cc) == RICH:
                    chars.append("R")
                elif (rr, cc) in BERRY_TILES and self.berry_gone[(rr, cc)] == 0:
                    chars.append("b")
                else:
                    chars.append(".")
        scent = {"station": self._scent_to(STATION),
                 "rich": self._scent_to(RICH),
                 "berry": self._scent_to(self._nearest_berry())}
        return {"view": "".join(chars), "energy": round(self.energy, 3),
                "afford": self.afford(), "phase": self.phase,
                "pos": (r, c), "scent": scent}

    def _nearest_berry(self):
        best, bd = BERRY_TILES[0], 999
        for t in BERRY_TILES:
            if self.berry_gone[t] > 0:
                continue
            d = abs(t[0] - self.pos[0]) + abs(t[1] - self.pos[1])
            if d < bd:
                best, bd = t, d
        return best

    def _scent_to(self, target):
        r, c = self.pos
        tr, tc = target
        base = abs(tr - r) + abs(tc - c)
        out = {}
        for d, (dr, dc) in (("up", (-1, 0)), ("down", (1, 0)),
                            ("left", (0, -1)), ("right", (0, 1))):
            nr, nc = r + dr, c + dc
            out[d] = (abs(tr - nr) + abs(tc - nc)) - base
        return out

    # ---------------- dynamics ----------------
    def step(self, action):
        assert action in ACTIONS, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        info = {}
        r = 0.0
        available = self._affordable(action)
        if action in MOVES and available:
            dr, dc = {"up": (-1, 0), "down": (1, 0),
                      "left": (0, -1), "right": (0, 1)}[action]
            nr, nc = self.pos[0] + dr, self.pos[1] + dc
            if 0 <= nr < H and 0 <= nc < W:
                self.pos = (nr, nc)
        in_aura = self._in_aura()
        is_nonmove = action in NONMOVE
        if in_aura:
            self.aura_steps += 1
        # ---- the aura effects (only in the aura, only if affordable) --
        if in_aura and available:
            if self.truth:
                p_hum = P_HUM_EDGE if action == self.edge_action \
                    else P_HUM_BG
            else:
                p_hum = P_HUM_FLAT
            if self.rng.random() < p_hum:
                info["hum"] = True
                self.hums += 1
            if self.decoy and self.phase == "warm" \
                    and self.rng.random() < P_GLOW_WARM:
                info["glow"] = True
                self.glows += 1
            # ---- the pool ----
            if info.get("hum"):
                self.pool = min(FRUIT_NEED, self.pool + POOL_GAIN)
            else:
                self.pool = max(0, self.pool - POOL_DRAIN)
            if self.pool >= FRUIT_NEED and not self.fruit \
                    and self.cooldown <= 0:
                self.fruit = True
                self.fruit_fuel = FRUIT_LIFE
                self.pool = 0
                self.fruit_blooms += 1
        # ---- the fruit (eaten by a non-move action on the station) ----
        if self.fruit and is_nonmove and self.pos == STATION and available:
            self.fruit = False
            self.fruit_fuel = 0
            self.energy = min(100.0, self.energy + FRUIT_ENERGY)
            r += FRUIT_REWARD
            self.fruits_eaten += 1
            self.cooldown = FRUIT_COOLDOWN
            info["fruit"] = True
        if self.fruit:
            self.fruit_fuel -= 1
            if self.fruit_fuel <= 0:
                self.fruit = False
                self.fruit_fuel = 0
        if self.cooldown > 0:
            self.cooldown -= 1
        # ---- the permitted alternative ----
        if is_nonmove and self.pos == RICH and available:
            r += self.rich_rate
            self.rich_total += self.rich_rate
        # ---- berries ----
        if is_nonmove and available and self.pos in BERRY_TILES \
                and self.berry_gone[self.pos] == 0:
            self.energy = min(100.0, self.energy + BERRY_ENERGY)
            self.berry_gone[self.pos] = BERRY_REGEN
            self.berry_eats += 1
            info["berry"] = True
        for c2 in BERRY_TILES:
            if self.berry_gone[c2] > 0:
                self.berry_gone[c2] -= 1
        # ---- energy ----
        self.energy -= ENERGY_COST
        if in_aura and is_nonmove:
            self.energy -= AURA_NONMOVE_COST
        self.t += 1
        if self.energy <= 0:
            self.alive = False
            info["died"] = True
        info["t"] = self.t
        return self.obs(), r, not self.alive, info

    # ---------------- ground truth (documentation + the oracle) ------
    def true_causal_edges(self):
        out = {}
        if self.truth:
            out[(self.edge_action, "hum")] = P_HUM_EDGE / P_HUM_BG
        return out

    def true_confounders(self):
        out = {}
        if self.decoy:
            out["glow_decoy"] = (
                f"({self.decoy_action}, glow): glow is a WARM-phase world "
                f"event at p={P_GLOW_WARM} for EVERY action in the aura; "
                f"{self.decoy_action} is affordable only in warm, so the "
                f"in-aura pooled contrast looks exclusive (0.50 vs "
                f"~0.50*warm_share) while the within-warm contrast is "
                f"exactly 0.0")
        out["grey_zone"] = (
            f"hum: P={P_HUM_EDGE} on {self.edge_action} vs {P_HUM_BG} "
            f"otherwise (in-aura RR=1.5, grey: the strat gate RR>=2 "
            f"cannot take it)" if self.truth else
            f"truth=off: P(hum)={P_HUM_FLAT} for every action -- no cause")
        out["blind_fill"] = ("any action blend nets <= 3*0.25-0.75 = 0.00 "
                             "/step: blind patience and brute force cannot "
                             "fill the pool (verified NV2/NV3)")
        return out
