"""diag_w4g.py -- decisive ablation: is the seed-8 decoy FP carried by the
SHARED RNG STREAM, or by the agent's behaviour?

Two worlds, identical except for one thing:

  REAL   : TerrariumV7 as written -- hum and glow draw from one shared
           stream, and an unaffordable action consumes NO draws while an
           affordable one consumes them (the decoy action is affordable
           only in warm), so the two probe arms advance the stream by
           different amounts.
  DECORR : the glow coin for each in-aura warm step is drawn from its own
           independent stream (seeded from the world seed). Everything else
           is byte-identical. Under exchangeability this makes glow an
           honest iid p=0.5 event for every arm.

If the FP disappears under DECORR, the leak is stream coupling, not the
world law and not the arbiter.
"""
import random

from env_terrarium_v7 import (TerrariumV7, pick_edge_action,
                              pick_decoy_action, P_HUM_EDGE, P_HUM_BG,
                              P_HUM_FLAT, P_GLOW_WARM, POOL_GAIN,
                              POOL_DRAIN, FRUIT_NEED, FRUIT_LIFE,
                              FRUIT_REWARD, FRUIT_ENERGY, FRUIT_COOLDOWN,
                              BERRY_ENERGY, BERRY_REGEN, ENERGY_COST,
                              AURA_NONMOVE_COST, MOVES, NONMOVE, STATION,
                              RICH, BERRY_TILES)
from agent_emca_v7 import AgentV7Full


class TerrariumV7Decorr(TerrariumV7):
    """Identical to TerrariumV7 except the glow coin is independent."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.glow_rng = random.Random(10 ** 6 + self.seed)

    def step(self, action):
        # copy of the parent's step with `self.glow_rng.random()` for glow
        assert action in MOVES + NONMOVE, action
        if not self.alive:
            return self.obs(), 0.0, True, {}
        info = {}
        r = 0.0
        available = self._affordable(action)
        if action in MOVES and available:
            dr, dc = {"up": (-1, 0), "down": (1, 0),
                      "left": (0, -1), "right": (0, 1)}[action]
            nr, nc = self.pos[0] + dr, self.pos[1] + dc
            if 0 <= nr < 11 and 0 <= nc < 11:
                self.pos = (nr, nc)
        in_aura = self._in_aura()
        is_nonmove = action in NONMOVE
        if in_aura:
            self.aura_steps += 1
        if in_aura and available:
            p_hum = (P_HUM_EDGE if action == self.edge_action
                     else P_HUM_BG) if self.truth else P_HUM_FLAT
            if self.rng.random() < p_hum:
                info["hum"] = True
                self.hums += 1
            if self.decoy and self.phase == "warm" \
                    and self.glow_rng.random() < P_GLOW_WARM:   # <-- the ONLY change
                info["glow"] = True
                self.glows += 1
            if info.get("hum"):
                self.pool = min(FRUIT_NEED, self.pool + POOL_GAIN)
            else:
                self.pool = max(0, self.pool - POOL_DRAIN)
            if self.pool >= FRUIT_NEED and not self.fruit and self.cooldown <= 0:
                self.fruit = True
                self.fruit_fuel = FRUIT_LIFE
                self.pool = 0
                self.fruit_blooms += 1
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
        if is_nonmove and self.pos == RICH and available:
            r += self.rich_rate
            self.rich_total += self.rich_rate
        if is_nonmove and available and self.pos in BERRY_TILES \
                and self.berry_gone[self.pos] == 0:
            self.energy = min(100.0, self.energy + BERRY_ENERGY)
            self.berry_gone[self.pos] = BERRY_REGEN
            self.berry_eats += 1
            info["berry"] = True
        for c2 in BERRY_TILES:
            if self.berry_gone[c2] > 0:
                self.berry_gone[c2] -= 1
        self.energy -= ENERGY_COST
        if in_aura and is_nonmove:
            self.energy -= AURA_NONMOVE_COST
        self.t += 1
        if self.energy <= 0:
            self.alive = False
            info["died"] = True
        info["t"] = self.t
        return self.obs(), r, not self.alive, info


def run(seed, cls, truth=False, decoy=True, rich="low", steps=16000):
    ea = pick_edge_action(seed)
    ag = AgentV7Full(seed)
    env = cls(seed, truth=truth, decoy=decoy, rich=rich, edge_action=ea)
    for t in range(steps):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = cls(seed + 1000 + t, truth=truth, decoy=decoy, rich=rich,
                      edge_action=ea)
    return ag


for label, cls in (("REAL  ", TerrariumV7), ("DECORR", TerrariumV7Decorr)):
    print(f"=== {label} : null regime truth=off, seeds 0..19 ===")
    fps = []
    for seed in range(20):
        ag = run(seed, cls)
        for (a, e), v in ag.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fps.append((seed, a, v["p"], v["rr"],
                            v["target_yes"], v["target_no"],
                            v["ctrl_yes"], v["ctrl_no"]))
    print(f"   glow CAUSALs: {len(fps)} / 20 runs")
    for f in fps:
        print("     ", f)

print("\n=== seed 8 detail, DECORR ===")
ag = run(8, TerrariumV7Decorr)
for (a, e), v in ag.verdicts.items():
    print("   ", a, e, v["verdict"], "p=", v["p"], "rr=", v["rr"],
          v["target_yes"], v["target_no"], v["ctrl_yes"], v["ctrl_no"])
