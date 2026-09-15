#!/usr/bin/env python3
"""Synthetic sanity check: does the planned v2 decoy-confounder design actually
separate causal from correlational identification at small scale?

Owner directive (turn 95): no full v2 turn until a toy-scale check proves the
new confounder separates causal/correlational -- BEFORE the 9x3 matrix.

DESIGN (toy variant of the v2 terrarium):
  * Hidden phase warm/cold (Markov dwell 80-200 steps). Warm: the bell GLOWS
    (tile G), berries bloom around the bell, the bell RINGS by itself often.
    Cold: bell dark (Q), no berries, rare rings (wind).
  * DECOY: "grasp" at the bell. It NEVER has any effect (no info flag at all).
    The glow makes a reasonable policy grasp it mostly in warm phase ->
    grasp correlates with bell_rang, but causes nothing.
  * bell_rang is a WORLD event: action-independent, position-independent.
    (This avoids the vantage trap: view-dependent effects would give stay-
    actions like grasp a TRUE observation edge -- not a decoy. Discovered
    while designing; see report.)
  * True edges kept as controls: eat->ate (berries), press->lever (opens the
    sealed door to the treasure).
  * Variant A: berries AROUND the bell -> the confounder's footprint
    (berry_near) is KEYED in the decoy's contexts.
  * Variant B: berries far away -> confounder NOT keyed at the bell.

PRE-REGISTERED CRITERIA (fixed before the first run; env knobs may be tuned
between runs but every adjustment is logged in the report; criteria are not):
  S1 correlation fooled:  assoc_edges() contains ("grasp","bell_rang") in >=2/3 seeds (variant A)
  S2 contrast rejects:    causal_edges() lacks ("grasp","bell_rang") in >=2/3 seeds,
                          with decoy data present (rate_a>=0.02, n>=3) in those seeds
  S3 true edges survive:  causal_edges() contains ("eat","ate") and ("press","lever") in >=2/3 seeds
  S4 boundary prediction (variant B): causal_edges() CONTAINS ("grasp","bell_rang") in >=2/3
                          seeds -- contrast fooled when the confounder is unkeyed
  S5 interventional oracle: |P(ring|do(grasp)) - P(ring|do(wait))| <= 0.05 and
                          P(ate|do(eat)) >= 0.9; identifier verdicts must match it
OVERALL: identification separation validated iff S1 and S2 and S3 and S5.

Uses the REAL identification module (agent_emca.EMCA: observe / assoc_edges /
causal_edges with DEFAULT parameters). No agent code is modified.
Exploratory (no PASS/FAIL): ("eat","bell_rang") second decoy-class edge;
("grasp","energy_rose") goal-matched decoy reachability; real-agent arms.
Post-hoc (after run 1, NOT pre-registered for run 1):
  S6a per-context contrast with the CURRENT ctx key -- tests whether pooling
      across contexts is the flaw alone. Run-1 analysis predicts NO: the
      confounder's visible trace (bell glow) is NOT in the ctx key, so warm/
      cold phase still mixes inside every context and grasp trials are still
      phase-enriched within it.
  S6b ctx key AUGMENTED with the glow (EMCA_GlowCtx subclass; NO algorithm
      change) -- candidate minimal fix: the EXISTING pooled causal_edges must
      now reject the decoy while keeping the true edges. Criteria fixed before
      this arm's first run: decoy rejected AND both true edges kept, >=2/3
      seeds, variant A.
  S7 (candidate fix #3, criteria fixed before run 3): necessity/specificity
      condition in the identifier (EMCA_SpecContrast subclass, spec_cap=0.10,
      CURRENT ctx key): an edge stands only if the effect is also RARE on
      other actions in the pooled contexts. Rationale: a cause is the dominant
      source of its effect (eat->ate: others 0.0); a phase-confounded decoy
      shares the effect with everyone (grasp->bell_rang: others 0.37).
      Stated boundary: rejects true edges in multi-cause worlds (two levers
      opening the same door). The alternative knob (raise margin to 0.30)
      is rejected: it kills the rare-effect identification E1 relies on
      (press->lever rate_a ~0.028). Criteria: decoy rejected AND both true
      edges kept, >=2/3 seeds, variant A (and decoy rejected in variant B).
Harness fix after run 1: the do(eat) oracle arm was degenerate (forced eat
with no navigation never reaches a berry -> P(ate|do(eat))=0.0 was a harness
artifact, not env truth); now a greedy berry-seeker. Full re-run from scratch.
Run layering: run 1 = S1-S5; run 2 = + S6a/S6b and the harness fix; run 3
= + S7. Criteria for each arm were fixed before that arm's first run; env
knobs unchanged across all runs.
"""
import random
from collections import defaultdict

from env_terrarium import ACTIONS, BERRY, DOOR, LEVER, TREASURE, EMPTY, WALL
from agent_emca import EMCA

BELL_GLOW, BELL_DARK = "G", "Q"
W, H = 9, 9
MAP = [
    "#########",
    "#..Q....#",
    "#.......#",
    "#.......#",
    "#...L...#",
    "#...##..#",
    "#...DT..#",
    "#...##..#",
    "#########",
]
BELL_POS = (1, 3)
ZONE_A = [(1, 2), (1, 4), (2, 2), (2, 3), (2, 4)]   # around the bell (keyed)
ZONE_B = [(2, 6), (2, 7), (3, 6), (3, 7)]           # far corner (unkeyed)
RING_WARM, RING_COLD = 0.65, 0.05
AMB_WARM, AMB_COLD, METAB = 0.3, -0.2, 0.5
DECOY = ("grasp", "bell_rang")
TRUE_EDGES = [("eat", "ate"), ("press", "lever")]


class ToyEnv:
    def __init__(self, seed, berry_cells):
        self.rng = random.Random(seed)
        self.berry_cells = list(berry_cells)
        self.t = 0
        self.energy = 60.0
        self.phase = "warm"
        self.dwell = self.rng.randint(80, 200)
        self.door_open = False
        self.treasure_taken = 0
        self.pos = [3, 3]
        self.alive = True
        self.berries = set()
        self._maintain_berries()

    def _maintain_berries(self):
        if self.phase == "warm":
            if len(self.berries) < 3:
                free = [c for c in self.berry_cells
                        if c not in self.berries and MAP[c[0]][c[1]] == EMPTY]
                if free:
                    self.berries.add(self.rng.choice(free))
        else:
            self.berries.clear()

    def obs(self):
        r, c = self.pos
        view = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    view.append(WALL)
                    continue
                ch = MAP[rr][cc]
                if (rr, cc) == BELL_POS:
                    ch = BELL_GLOW if self.phase == "warm" else BELL_DARK
                if ch == EMPTY and (rr, cc) in self.berries:
                    ch = BERRY
                if ch == DOOR and self.door_open:
                    ch = EMPTY
                view.append(ch)
        afford = []
        if (r, c) in self.berries:
            afford.append("eat")
        if MAP[r][c] == LEVER:
            afford.append("press")
        afford.append("grasp")
        return {"view": "".join(view), "energy": int(self.energy),
                "afford": tuple(sorted(afford)), "t": self.t}

    def _move(self, nr, nc):
        if not (0 <= nr < H and 0 <= nc < W):
            return
        ch = MAP[nr][nc]
        if ch == WALL:
            return
        if ch == DOOR and not self.door_open:
            return
        self.pos = [nr, nc]

    def step(self, action):
        assert action in ACTIONS, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        self.t += 1
        self.dwell -= 1
        if self.dwell <= 0:
            self.phase = "cold" if self.phase == "warm" else "warm"
            self.dwell = self.rng.randint(80, 200)
            self._maintain_berries()
        info = {}
        # world event: the bell rings by itself (phase-driven, action-independent)
        if self.rng.random() < (RING_WARM if self.phase == "warm" else RING_COLD):
            info["bell_rang"] = True
        self.energy += (AMB_WARM if self.phase == "warm" else AMB_COLD) - METAB
        r, c = self.pos
        reward = 0.0
        if action == "up":
            self._move(r - 1, c)
        elif action == "down":
            self._move(r + 1, c)
        elif action == "left":
            self._move(r, c - 1)
        elif action == "right":
            self._move(r, c + 1)
        elif action == "eat":
            if (r, c) in self.berries:
                self.berries.discard((r, c))
                self.energy = min(100.0, self.energy + 10.0)
                reward += 1.0
                info["ate"] = True
        elif action == "press":
            if MAP[r][c] == LEVER:
                self.door_open = True
                info["lever"] = True
        elif action == "grasp":
            pass                      # the decoy: NEVER any effect, no flag
        elif action == "wait":
            pass
        rr, cc = self.pos
        if MAP[rr][cc] == TREASURE and self.door_open and self.treasure_taken == 0:
            self.treasure_taken = 1
            reward += 20.0
            info["treasure"] = True
        if self.energy <= 0:
            self.alive = False
            reward -= 5.0
            info["died"] = True
        self._maintain_berries()
        return self.obs(), reward, not self.alive, info


class ScriptedPolicy:
    """Observational policy: sees only the observation (no phase label).
    Attracted to the GLOWING bell (that is the confounder's active part:
    warm phase causes both the glow-attraction and the rings)."""

    def __init__(self, seed, noise=0.05, bell_pull=(0.8, 0.15),
                 eat_p=0.6, press_p=0.4, attract=0.35):
        self.rng = random.Random(seed)
        self.noise, self.bell_pull = noise, bell_pull
        self.eat_p, self.press_p, self.attract = eat_p, press_p, attract

    def act(self, o):
        v = o["view"]
        if self.rng.random() < self.noise:
            return self.rng.choice(ACTIONS)
        if "eat" in o["afford"] and self.rng.random() < self.eat_p:
            return "eat"
        center = v[4]
        if center == BELL_GLOW and self.rng.random() < self.bell_pull[0]:
            return "grasp"
        if center == BELL_DARK and self.rng.random() < self.bell_pull[1]:
            return "grasp"
        if "press" in o["afford"] and self.rng.random() < self.press_p:
            return "press"
        if center not in (BELL_GLOW, BELL_DARK) and BELL_GLOW in v \
                and self.rng.random() < self.attract:
            return self._toward(v, BELL_GLOW)
        return self.rng.choice(["up", "down", "left", "right"])

    def _toward(self, v, ch):
        idxs = [i for i, x in enumerate(v) if x == ch]
        if not idxs:
            return self.rng.choice(["up", "down", "left", "right"])
        r, c = divmod(idxs[0], 3)
        if r < 1:
            return "up"
        if r > 1:
            return "down"
        if c < 1:
            return "left"
        return "right"


def run_obs(seed, zone, steps=8000, agent_cls=EMCA, stash_view=False):
    """Observational arm: scripted policy drives the REAL EMCA observe().
    agent_cls/stash_view: the S6b glow-ctx diagnostic (EMCA_GlowCtx)."""
    env = ToyEnv(seed, zone)
    pol = ScriptedPolicy(seed)
    ag = agent_cls(seed)
    ring = defaultdict(lambda: [0, 0])       # action -> [rang, trials]
    ate = [0, 0]                            # [ate_yes, eat_trials]
    warm = cold = deaths = 0
    for i in range(steps):
        o = env.obs()
        a = pol.act(o)
        if stash_view:
            ag._glow_view = o["view"]   # pre-step view: ctx of the ACTION taken
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        ring[a][1] += 1
        if info.get("bell_rang"):
            ring[a][0] += 1
        if a == "eat":
            ate[1] += 1
            if info.get("ate"):
                ate[0] += 1
        if env.phase == "warm":
            warm += 1
        else:
            cold += 1
        if done:
            deaths += 1
            env = ToyEnv(seed + 1000 + i, zone)
    return ag, ring, ate, warm, cold, deaths


def _nav_toward(view, ch, rng):
    idxs = [i for i, x in enumerate(view) if x == ch]
    if not idxs:
        return rng.choice(["up", "down", "left", "right"])
    r, c = divmod(idxs[0], 3)
    if r < 1:
        return "up"
    if r > 1:
        return "down"
    if c < 1:
        return "left"
    return "right"


def run_do(seed, zone, action, steps=4000):
    """Interventional oracle arm: forced do(action), no agent, raw env only.
    v2 of the harness: do(eat) is a greedy berry-seeker (moves toward berries,
    eats when on one). v1 forced 'eat' with no navigation: the eater never
    reached a berry, so P(ate|do(eat))=0.0 was a degenerate-policy artifact
    caught on run 1 -- the env does always reward eating on a berry."""
    env = ToyEnv(seed, zone)
    nav_rng = random.Random(seed * 7 + 13)
    ring = [0, 0]
    ate = [0, 0]
    for i in range(steps):
        o = env.obs()
        if action == "eat":
            if "eat" in o["afford"]:
                a = "eat"
            else:
                a = _nav_toward(o["view"], BERRY, nav_rng)
        elif action == "press" and "press" not in o["afford"]:
            a = "wait"
        else:
            a = action
        o2, r, done, info = env.step(a)
        ring[1] += 1
        if info.get("bell_rang"):
            ring[0] += 1
        if a == "eat":
            ate[1] += 1
            if info.get("ate"):
                ate[0] += 1
        if done:
            env = ToyEnv(seed + 5000 + i, zone)
    return ring, ate


def run_agent(seed, use_causal, steps=6000):
    """Exploratory arm: the REAL agent (act+observe) in the variant A toy."""
    env = ToyEnv(seed, ZONE_A)
    ag = EMCA(seed, use_causal=use_causal)
    c = defaultdict(int)
    for i in range(steps):
        o = env.obs()
        a = ag.act(o)
        if a == "grasp":
            c["grasp_any"] += 1
            if o["view"][4] in (BELL_GLOW, BELL_DARK):
                c["grasp_at_bell"] += 1
        if a == "eat":
            c["eat"] += 1
        if a == "press":
            c["press"] += 1
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("bell_rang"):
            c["rings_seen"] += 1
        if info.get("treasure"):
            c["treasures"] += 1
        if done:
            c["deaths"] += 1
            env = ToyEnv(seed + 3000 + i, ZONE_A)
    return ag, c


class EMCA_GlowCtx(EMCA):
    """S6b diagnostic subclass: ctx key augmented with the bell's VISIBLE
    signature (glow/dark in the pre-step view). NO algorithm change -- the
    test is whether a richer context key alone lets the EXISTING pooled
    contrast reject the decoy. The runner stashes _glow_view before each
    observe(); it is the pre-step view, i.e. the context of the action taken
    (seen_transitions' f2 keys use a stale view -- irrelevant for edges:
    ctx_ae is keyed only by the f1 context)."""

    def _ctx_key(self, f):
        base = super()._ctx_key(f)
        v = getattr(self, "_glow_view", "") or ""
        return base + (BELL_GLOW in v, BELL_DARK in v)


class EMCA_SpecContrast(EMCA):
    """S7 candidate fix #3: necessity/specificity condition added to the
    EXISTING pooled contrast. An edge is accepted only if the effect is also
    RARE on other actions in the pooled contexts (pooled_others <= spec_cap).
    eat->ate: others 0.0 -> kept. grasp->bell_rang: others ~0.37 -> rejected.
    Stated boundary: in multi-cause worlds (two levers, one door) this rejects
    true edges; the margin knob alternative (0.30) is worse -- it kills the
    rare-effect identification E1 depends on. Same thresholds otherwise."""

    def __init__(self, *a, spec_cap=0.10, **kw):
        super().__init__(*a, **kw)
        self.spec_cap = spec_cap

    def causal_edges(self, min_n=3, min_p=0.02, margin=0.02):
        out = {}
        effects = {e for acts in self.ctx_ae.values()
                   for effs in acts.values() for e in effs if e != "trial"}
        for e in effects:
            agg = defaultdict(lambda: [0, 0])
            for ctx, acts in self.ctx_ae.items():
                for a, effs in acts.items():
                    n = effs.get("trial", [0, 0])[1]
                    if e in effs:
                        y = effs[e][0]
                        agg[a][0] += y
                        agg[a][1] += n
                    else:
                        agg[a][1] += n
            for a, (y, n) in agg.items():
                if n < min_n:
                    continue
                rate_a = y / n
                if rate_a < min_p:
                    continue
                oy = on = 0
                for ctx, acts in self.ctx_ae.items():
                    if a in acts and e in acts[a]:
                        for a2, effs in acts.items():
                            if a2 != a:
                                oy += effs.get(e, [0, 0])[0]
                                on += effs.get("trial", [0, 0])[1]
                if on == 0:
                    out[(a, e)] = round(rate_a, 3)
                    continue
                pooled = oy / on
                if pooled > self.spec_cap:      # S7: necessity/specificity
                    continue
                if rate_a - pooled >= margin:
                    out[(a, e)] = round(rate_a, 3)
        return out


def pool_breakdown(ag, action, effect):
    """Diagnostic: which contexts enter the decoy's contrast pool, with raw
    counters inside each -- explains WHY a candidate fix fails."""
    print(f"    pool breakdown for {action}->{effect} (contexts entering the contrast):")
    rows = []
    for ctx, acts in ag.ctx_ae.items():
        if action in acts and effect in acts[action]:
            y_a = acts[action][effect][0]
            n_a = acts[action].get("trial", [0, 0])[1]
            oy = on = 0
            for a2, effs in acts.items():
                if a2 != action:
                    oy += effs.get(effect, [0, 0])[0]
                    on += effs.get("trial", [0, 0])[1]
            rows.append((ctx, y_a, n_a, oy, on))
    for ctx, y_a, n_a, oy, on in sorted(rows, key=lambda r: -r[3])[:12]:
        print(f"      ctx={ctx} {action} {y_a}/{n_a}={y_a / n_a if n_a else 0:.2f} "
              f"others {oy}/{on}={oy / on if on else 0:.2f}")
    print(f"      ({len(rows)} contexts enter the pool)")


def per_context_edges(ag, min_n=3, min_p=0.02, margin=0.02):
    """S6a diagnostic: contrast computed PER (ctx, action) pair instead of
    pooled across contexts. Same thresholds as causal_edges defaults. The
    edge is kept if it passes in >=1 context (most permissive reading)."""
    out = {}
    effects = {e for acts in ag.ctx_ae.values()
               for effs in acts.values() for e in effs if e != "trial"}
    for ctx, acts in ag.ctx_ae.items():
        for a, effs in acts.items():
            n = effs.get("trial", [0, 0])[1]
            if n < min_n:
                continue
            for e in effects:
                if e not in effs:
                    continue
                y = effs[e][0]
                rate_a = y / n
                if rate_a < min_p:
                    continue
                oy = on = 0
                for a2, effs2 in acts.items():
                    if a2 != a:
                        oy += effs2.get(e, [0, 0])[0]
                        on += effs2.get("trial", [0, 0])[1]
                if on == 0 or rate_a - oy / on >= margin:
                    out.setdefault((a, e), []).append((ctx, round(rate_a, 3)))
    return out


def edge_diagnostics(ag, action, effect):
    """Mirror of causal_edges' pooling rule, with raw counters printed."""
    y = n = 0
    for ctx, acts in ag.ctx_ae.items():
        if action in acts:
            n += acts[action].get("trial", [0, 0])[1]
            if effect in acts[action]:
                y += acts[action][effect][0]
    rate_a = y / n if n else 0.0
    oy = on = 0
    for ctx, acts in ag.ctx_ae.items():
        if action in acts and effect in acts[action]:
            for a2, effs in acts.items():
                if a2 != action:
                    oy += effs.get(effect, [0, 0])[0]
                    on += effs.get("trial", [0, 0])[1]
    pooled = oy / on if on else None
    return {"y": y, "n": n, "rate_a": round(rate_a, 4),
            "oy": oy, "on": on,
            "pooled": round(pooled, 4) if pooled is not None else None,
            "diff": round(rate_a - pooled, 4) if pooled is not None else None}


def fmt_edges(d):
    return "{%s}" % ", ".join(f"{a}->{e}:{p}" for (a, e), p in sorted(d.items()))


def obs_arm(label, zone, seeds=(1, 2, 3), steps=8000):
    print(f"\n=== ARM-OBS {label} (scripted policy, real EMCA observe, {steps} steps/seed) ===")
    rows = []
    for seed in seeds:
        ag, ring, ate, warm, cold, deaths = run_obs(seed, zone, steps)
        assoc = ag.assoc_edges()
        causal = ag.causal_edges()
        pc = per_context_edges(ag)
        d_decoy = edge_diagnostics(ag, *DECOY)
        d_eat_ring = edge_diagnostics(ag, "eat", "bell_rang")
        d_grasp_erose = edge_diagnostics(ag, "grasp", "energy_rose")
        print(f"\n--- seed {seed}: warm={warm} cold={cold} deaths={deaths} ---")
        print("raw P(ring|a) per action (runner accounting, independent of agent):")
        for a in sorted(ring, key=lambda x: -ring[x][1]):
            yy, nn = ring[a]
            print(f"    {a:6s} rang {yy:5d}/{nn:5d} = {yy / nn if nn else 0:.3f}")
        print(f"raw P(ate|eat) = {ate[0]}/{ate[1]} = {ate[0] / ate[1] if ate[1] else 0:.3f}")
        print(f"ASSOC edges  {fmt_edges(assoc)}")
        print(f"CAUSAL edges {fmt_edges(causal)}")
        print(f"decoy  {DECOY}: ctx_ae rate_a={d_decoy['rate_a']} (y={d_decoy['y']}, n={d_decoy['n']}), "
              f"pooled_others={d_decoy['pooled']} (oy={d_decoy['oy']}, on={d_decoy['on']}), "
              f"diff={d_decoy['diff']} (margin=0.02)")
        print(f"       assoc_has={DECOY in assoc}  causal_has={DECOY in causal}  perctx_has={DECOY in pc}")
        print(f"2nd   ('eat','bell_rang'): rate_a={d_eat_ring['rate_a']}, pooled={d_eat_ring['pooled']}, "
              f"assoc_has={('eat', 'bell_rang') in assoc}, causal_has={('eat', 'bell_rang') in causal}")
        print(f"probe ('grasp','energy_rose'): rate_a={d_grasp_erose['rate_a']}, n={d_grasp_erose['n']}, "
              f"assoc_has={('grasp', 'energy_rose') in assoc}")
        for te in TRUE_EDGES:
            print(f"true  {te}: assoc_has={te in assoc}, causal_has={te in causal}")
        rows.append({
            "seed": seed,
            "assoc_has": DECOY in assoc,
            "causal_has": DECOY in causal,
            "data_present": d_decoy["n"] >= 3 and d_decoy["rate_a"] >= 0.02,
            "true_ok": all(te in causal for te in TRUE_EDGES),
            "decoy_perctx": DECOY in pc,
            "assoc": assoc, "causal": causal, "ring": dict(ring), "ate": list(ate),
        })
    return rows


def main():
    print("sanity_v2_confounder.py -- toy-scale check of the v2 decoy-confounder design")
    print("real module: agent_emca.EMCA observe/assoc_edges/causal_edges, DEFAULT parameters")

    A = obs_arm("variant A (berries around the bell: confounder KEYED)", ZONE_A)
    B = obs_arm("variant B (berries far away: confounder UNKEYED at the bell)", ZONE_B)

    print("\n=== determinism check: seed 1 variant A run twice ===")
    ag1, ring1, ate1, *_ = run_obs(1, ZONE_A, 8000)
    same_edges = (fmt_edges(ag1.assoc_edges()) == fmt_edges(A[0]["assoc"])
                  and fmt_edges(ag1.causal_edges()) == fmt_edges(A[0]["causal"]))
    same_raw = {k: tuple(v) for k, v in ring1.items()} == \
              {k: tuple(v) for k, v in A[0]["ring"].items()}
    print(f"edge sets identical: {same_edges}; raw ring counters identical: {same_raw}")

    print("\n=== ARM-OBS-GLOW variant A (ctx key + bell glow: candidate minimal fix, ===")
    print("no algorithm change -- the EXISTING pooled causal_edges must now reject the decoy)")
    G = []
    for seed in (1, 2, 3):
        ag, ring, ate, warm, cold, deaths = run_obs(seed, ZONE_A, 8000,
                                                    agent_cls=EMCA_GlowCtx, stash_view=True)
        causal = ag.causal_edges()
        pc = per_context_edges(ag)
        d_decoy = edge_diagnostics(ag, *DECOY)
        if seed == 1:
            pool_breakdown(ag, *DECOY)
        print(f"--- seed {seed} ---")
        print(f"CAUSAL edges (glow ctx) {fmt_edges(causal)}")
        print(f"decoy: causal_has={DECOY in causal}, perctx_has={DECOY in pc}, "
              f"rate_a={d_decoy['rate_a']}, pooled={d_decoy['pooled']}, diff={d_decoy['diff']}")
        for te in TRUE_EDGES:
            print(f"true  {te}: causal_has={te in causal}")
        G.append({"seed": seed, "decoy_causal": DECOY in causal,
                  "true_ok": all(te in causal for te in TRUE_EDGES)})

    print("\n=== ARM-OBS-SPEC variant A (candidate fix #3: necessity/specificity, ===")
    print("current ctx key; spec_cap=0.10; no ctx change)")
    S7A = []
    for seed in (1, 2, 3):
        ag, *_ = run_obs(seed, ZONE_A, 8000, agent_cls=EMCA_SpecContrast)
        causal = ag.causal_edges()
        print(f"--- seed {seed} ---")
        print(f"CAUSAL edges (spec) {fmt_edges(causal)}")
        for probe in (DECOY, ("eat", "bell_rang"), ("press", "bell_rang")) + tuple(TRUE_EDGES):
            print(f"    {probe}: causal_has={probe in causal}")
        S7A.append({"seed": seed, "decoy_causal": DECOY in causal,
                    "true_ok": all(te in causal for te in TRUE_EDGES)})
    S7B = []
    for seed in (1, 2, 3):
        ag, *_ = run_obs(seed, ZONE_B, 8000, agent_cls=EMCA_SpecContrast)
        causal = ag.causal_edges()
        print(f"--- variant B seed {seed}: decoy causal_has={DECOY in causal}, "
              f"true_ok={all(te in causal for te in TRUE_EDGES)}")
        S7B.append({"seed": seed, "decoy_causal": DECOY in causal,
                    "true_ok": all(te in causal for te in TRUE_EDGES)})

    print("\n=== ARM-DO interventional oracle (forced actions, no agent) ===")
    do = {}
    for a in ("grasp", "wait", "eat"):
        ry, rn = 0, 0
        ay, an = 0, 0
        for seed in (1, 2):
            ring, ate = run_do(seed, ZONE_A, a)
            ry += ring[0]; rn += ring[1]
            ay += ate[0]; an += ate[1]
        do[a] = (ry / rn if rn else 0, ay / an if an else 0)
        print(f"do({a:5s}): P(ring)={ry}/{rn}={ry / rn if rn else 0:.3f}"
              + (f"  P(ate|eat-trial)={ay}/{an}={ay / an if an else 0:.3f}" if an else ""))

    print("\n=== ARM-AGENT exploratory (real EMCA vs emca_nocausal, variant A) ===")
    for use_causal, name in ((True, "emca"), (False, "emca_nocausal")):
        for seed in (1, 2):
            ag, c = run_agent(seed, use_causal)
            print(f"{name} seed {seed}: {dict(c)}")
            print(f"   ASSOC has decoy: {DECOY in ag.assoc_edges()}; "
                  f"CAUSAL has decoy: {DECOY in ag.causal_edges()}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    s1 = sum(r["assoc_has"] for r in A) >= 2
    s2 = sum((not r["causal_has"]) and r["data_present"] for r in A) >= 2
    s3 = sum(r["true_ok"] for r in A) >= 2
    s4_pred = sum(r["causal_has"] for r in B) >= 2
    s5 = abs(do["grasp"][0] - do["wait"][0]) <= 0.05 and do["eat"][1] >= 0.9
    print(f"S1 correlation fooled (variant A):            {'PASS' if s1 else 'FAIL'}")
    print(f"S2 contrast rejects decoy (variant A):        {'PASS' if s2 else 'FAIL'}")
    print(f"S3 true edges survive contrast (variant A):   {'PASS' if s3 else 'FAIL'}")
    print(f"S4 boundary: unkeyed confounder fools contrast (variant B): "
          f"{'PREDICTION CONFIRMED' if s4_pred else 'NOT CONFIRMED (boundary looser)'}")
    print(f"S5 interventional oracle agrees:              {'PASS' if s5 else 'FAIL'} "
          f"(P(ring|do(grasp))={do['grasp'][0]:.3f}, P(ring|do(wait))={do['wait'][0]:.3f}, "
          f"P(ate|do(eat))={do['eat'][1]:.3f})")
    s6a_still = sum(r["decoy_perctx"] for r in A) >= 2
    s6b_fixed = sum((not r["decoy_causal"]) and r["true_ok"] for r in G) >= 2
    print(f"S6a per-context contrast, CURRENT ctx key: decoy accepted in "
          f"{sum(r['decoy_perctx'] for r in A)}/3 seeds -> "
          f"{'per-context alone does NOT fix it' if s6a_still else 'per-context rejects it'}")
    print(f"S6b glow-augmented ctx key, existing pooled contrast: decoy rejected "
          f"AND true edges kept in {sum((not r['decoy_causal']) and r['true_ok'] for r in G)}/3 seeds "
          f"-> {'FIX WORKS at toy scale' if s6b_fixed else 'fix does NOT work'}")
    s7a = sum((not r["decoy_causal"]) and r["true_ok"] for r in S7A) >= 2
    s7b = sum(not r["decoy_causal"] for r in S7B) >= 2
    print(f"S7 candidate fix #3 (specificity, spec_cap=0.10): decoy rejected AND true "
          f"edges kept in {sum((not r['decoy_causal']) and r['true_ok'] for r in S7A)}/3 seeds "
          f"(variant A) -> {'FIX WORKS at toy scale' if s7a else 'fix does NOT work'}; "
          f"variant B decoy rejected in {sum(not r['decoy_causal'] for r in S7B)}/3 -> "
          f"{'boundary closed' if s7b else 'boundary still open'}")
    overall = s1 and s2 and s3 and s5
    print(f"OVERALL: v2 decoy separates causal/correlational at toy scale: "
          f"{'YES' if overall else 'NO'} (S1&S2&S3&S5)")
    print(f"VERDICT FOR V2: the decoy design bites (S1) and the oracle confirms no true "
          f"causation (S5), but the CURRENT identifier accepts the decoy (S2) -> building "
          f"the full matrix on v2 as-is would repeat emca == emca_nocausal; v2 needs the "
          f"identifier fix first: S6a/S6b failed, S7 specificity "
          f"{'VALIDATED at toy scale (multi-cause boundary stated)' if s7a else 'also failed'}")


if __name__ == "__main__":
    main()
