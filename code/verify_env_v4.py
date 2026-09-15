"""Independent verification of TerrariumV4's mechanics (the same
protocol as verify_env_v33): the do-oracle, the decoy's correlation
structure, the brute-force gates, the competent chain, determinism.
No agent code is imported -- the world is driven directly."""
import random
from collections import defaultdict

from env_terrarium_v4 import (
    TerrariumV4, TRAP_CELL, TREASURY_POS, BLOCKED_CELLS, SCORCH_COST,
)
from env_terrarium_v3 import ACTIONS, MAP, W, H

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + " " + name
          + ("  " + detail if detail else ""))


def force_weather(env, weather, dwell=10000):
    env.weather = weather
    env.weather_dwell = dwell
    env.torch_lit = (weather == "storm")
    env.torch_dwell = dwell if weather == "storm" else 0
    if weather == "storm" and env.tree is None:
        # spawn a storm tree near the bell (the trap's linger anchor)
        from env_terrarium_v3 import TREE_SPAWN_MAX_DIST, BELL_POS
        cands = [(r, c) for r in range(1, H - 1) for c in range(1, W - 1)
                 if MAP[r][c] == "." and (r, c) != BELL_POS
                 and (r, c) not in (BLOCKED_CELLS, ) and (r, c) != TRAP_CELL
                 and (r, c) != TREASURY_POS
                 and abs(r - BELL_POS[0]) + abs(c - BELL_POS[1])
                 <= TREE_SPAWN_MAX_DIST]
        env.tree = cands[0]


def pin_energy(env, e):
    env.energy = e


# ---------------------------------------------------------------------------
# V1. The do-oracle: P(torch_lit | do(a)) is EQUAL for every action.
#    The agent is pinned at a cell dist<=1 of the brazier, the weather
#    is FORCED storm, the flame cycle frozen ON (torch_lit held True),
#    energy pinned -- the ONLY channel from action to torch state is
#    the env's own pulse machine, which ignores actions.
def oracle_torch():
    counts = {a: [0, 0] for a in ACTIONS}
    for seed in range(3):
        for a in ACTIONS:
            for rep in range(300):
                env = TerrariumV4(seed)
                force_weather(env, "storm", dwell=10**9)
                env.torch_lit = False
                env.torch_dwell = 0
                # pin the agent beside the brazier, energy high
                for pos in [(3, 5), (3, 7), (2, 6), (4, 6)]:
                    if MAP[pos[0]][pos[1]] == "." and pos != TRAP_CELL:
                        env.pos = list(pos)
                        break
                pin_energy(env, 90.0)
                env.torches = 3      # full stack: no collect interference
                before = env.torch_lit
                o, r, done, info = env.step(a)
                after = env.torch_lit
                counts[a][1] += 1
                if info.get("torch_lit") is True or after != before:
                    counts[a][0] += 1
    ps = {a: c[0] / c[1] for a, c in counts.items()}
    spread = max(ps.values()) - min(ps.values())
    check("V1 do-oracle P(torch_lit|do(a)) equal for all actions",
          spread <= 0.03, f"spread={spread:.3f} "
          + " ".join(f"{a}:{p:.2f}" for a, p in ps.items()))


# ---------------------------------------------------------------------------
# V2. Brute force cannot bank torches / eat the treasury: random lives
#    collect ~0 torches and 0 treasury meals in 5 x 3000 steps.
def brute_force():
    coll, treasury = [], []
    for seed in range(1, 6):
        env = TerrariumV4(seed)
        rng = random.Random(seed)
        tc = te = deaths = 0
        for t in range(3000):
            o = env.obs()
            a = rng.choice(ACTIONS)
            o2, r, done, info = env.step(a)
            if info.get("torch_collect"):
                tc += 1
            if info.get("treasury_ate"):
                te += 1
            if info.get("died"):
                deaths += 1
                env = TerrariumV4(seed * 100 + t)
        coll.append(tc)
        treasury.append(te)
    # the honest bar: random banks ~1-3 by chance standing; the
    # TREASURY meal (the chain's end) is what brute force cannot do
    check("V2 brute force banks ~no torches", max(coll) <= 3,
          f"collected={coll}")
    check("V2b brute force eats ~no treasury", max(treasury) == 0,
          f"eaten={treasury}")


# ---------------------------------------------------------------------------
# V3. The competent chain: a scripted agent (the world-knowledge
#    route: walk to the brazier in a storm, stand one step, walk to
#    the treasury in calm+warm) banks torches and eats.
def scripted_chain():
    def greedy_step(env, target):
        # pure manhattan descent, allowed by gates
        r, c = env.pos
        tr, tc2 = target
        best = None
        for dr, dc, a in ((-1, 0, "up"), (1, 0, "down"),
                          (0, -1, "left"), (0, 1, "right")):
            nr, nc = r + dr, c + dc
            if (nr, nc) in BLOCKED_CELLS:
                continue
            ch = MAP[nr][nc]
            if ch == "#" or (ch == "D" and not env.door_open):
                continue
            d = abs(nr - tr) + abs(nc - tc2)
            if best is None or d < best[0]:
                best = (d, a)
        return best[1]

    total = 0
    deaths_all = []
    WAIT_CELL = (3, 7)          # dist 2 from the brazier: no scorch
    for seed in range(1, 4):
        env = TerrariumV4(seed)
        banked = eaten = deaths = 0
        for t in range(16000):
            o = env.obs()
            lit = env.torch_lit
            d = abs(env.pos[0] - TRAP_CELL[0]) + abs(env.pos[1] - TRAP_CELL[1])
            if env.torch_bank >= 1:
                if env.weather == "calm" and env.season == "warm":
                    if tuple(env.pos) == TREASURY_POS:
                        a = "eat"
                    else:
                        a = greedy_step(env, TREASURY_POS)
                elif d >= 2:
                    if env.tree and env.weather == "storm":
                        tr, tc = env.tree
                        if abs(env.pos[0] - tr) + abs(env.pos[1] - tc) <= 1:
                            a = "grasp"
                        else:
                            a = greedy_step(env, env.tree)
                    else:
                        a = "wait"
                else:
                    a = greedy_step(env, WAIT_CELL)
            elif env.weather == "storm":
                if lit and env.energy >= 40 and env.torches > 0:
                    if tuple(env.pos) == TRAP_CELL:
                        a = "wait"
                    else:
                        a = greedy_step(env, TRAP_CELL)
                elif env.tree:
                    tr, tc = env.tree
                    if abs(env.pos[0] - tr) + abs(env.pos[1] - tc) <= 1:
                        a = "grasp"
                    else:
                        a = greedy_step(env, env.tree)
                elif tuple(env.pos) == WAIT_CELL or d >= 2:
                    a = "wait"
                else:
                    a = greedy_step(env, WAIT_CELL)
            else:
                f = [k for k in env.berries]
                if f and env.energy < 80:
                    tgt = min(f, key=lambda p: abs(p[0] - env.pos[0])
                              + abs(p[1] - env.pos[1]))
                    a = greedy_step(env, tgt)
                elif env.tree:
                    if tuple(env.pos) == env.tree:
                        a = "eat"
                    else:
                        a = greedy_step(env, env.tree)
                else:
                    a = "wait"
            if a == "eat" and tuple(env.pos) == TREASURY_POS \
                    and "eat" not in o["afford"]:
                a = "wait"
            o2, r, done, info = env.step(a)
            if info.get("torch_collect"):
                banked += 1
            if info.get("treasury_ate"):
                eaten += 1
            if info.get("died"):
                deaths += 1
                env = TerrariumV4(seed * 7 + t)
        deaths_all.append(deaths)
        total += eaten
    check("V3 the competent chain eats the treasury", total >= 6,
          f"meals over 3 seeds={total} deaths={deaths_all}")


# ---------------------------------------------------------------------------
# V4. The scorch pocket: standing dist<=1 of a LIT brazier costs
#    exactly SCORCH_COST per step; the map is otherwise unchanged.
def scorch_math():
    env = TerrariumV4(11)
    force_weather(env, "storm", dwell=10**9)
    env.torch_lit = True
    env.torch_dwell = 10**9
    env.pos = [3, 7]          # dist 1 from the brazier (3,6)
    pin_energy(env, 50.0)
    e0 = env.energy
    o, r, done, info = env.step("wait")
    paid = e0 - env.energy
    # a storm step drains fury 3.0 + metab 0.4 (3.4 total); the scorch
    # adds 2.2 -> 5.6 total drain (paid is the energy DELTA e0 - e1)
    from env_terrarium_v33 import STORM_FURY_V33
    from env_terrarium_v3 import METAB
    expected = abs(STORM_FURY_V33) + METAB + SCORCH_COST
    check("V4 scorch price exact (2.2 + fury on top)",
          abs(paid - expected) < 1e-6,
          f"paid={paid:.2f} expected={expected:.2f}")
    check("V4b scorched flag emitted", info.get("scorched") is True)


# ---------------------------------------------------------------------------
# V5. The linger correlation is present in the raw world: P(torch_lit
#    | grasp at the storm tree) >> P(torch_lit | other) for a scripted
#    linger-forager -- the decoy's bait, measured without any agent.
def linger_correlation():
    # scripted forager: wanders in calm, sits at the storm tree
    # grasping in storms (the ONLY competent behaviour -- exactly what
    # the v3.3 arms do)
    acc = {"grasp": [0, 0], "other": [0, 0]}
    for seed in range(3):
        env = TerrariumV4(seed)
        rng = random.Random(seed)
        for t in range(16000):
            o = env.obs()
            if env.weather == "storm" and env.tree:
                tr, tc2 = env.tree
                if abs(env.pos[0] - tr) + abs(env.pos[1] - tc2) <= 1:
                    a = "grasp"
                else:
                    # descend to the tree
                    r, c = env.pos
                    best = None
                    for dr, dc, mv in ((-1, 0, "up"), (1, 0, "down"),
                                       (0, -1, "left"), (0, 1, "right")):
                        nr, nc = r + dr, c + dc
                        if MAP[nr][nc] == "#" or (nr, nc) in BLOCKED_CELLS:
                            continue
                        d = abs(nr - tr) + abs(nc - tc2)
                        if best is None or d < best[0]:
                            best = (d, mv)
                    a = best[1] if best else "wait"
            else:
                a = rng.choice(ACTIONS)
            o2, rr, done, info = env.step(a)
            lit = info.get("torch_lit") is True
            k = "grasp" if a == "grasp" else "other"
            acc[k][1] += 1
            if lit:
                acc[k][0] += 1
            if info.get("died"):
                env = TerrariumV4(seed * 13 + t)
    p_g = acc["grasp"][0] / max(1, acc["grasp"][1])
    p_o = acc["other"][0] / max(1, acc["other"][1])
    rr = p_g / max(p_o, 1e-9)
    check("V5 the linger bait exists (P(lit|grasp) >> P(lit|other))",
          rr >= 1.6, f"P(lit|grasp)={p_g:.3f} P(lit|other)={p_o:.3f} RR={rr:.2f}")


# ---------------------------------------------------------------------------
# V6. The gate walls: the warm zone is reachable only through the
#    corridor; the treasury is enclosed by walls on 2 sides (from MAP).
def gates():
    check("V6 gate walls block (2,3),(2,4)",
          MAP[2][3] == "#" and MAP[2][4] == "#",
          f"MAP[2][3]={MAP[2][3]} MAP[2][4]={MAP[2][4]}")
    # reachability: BFS from (1,1) with gates -- the treasury is reachable
    from collections import deque
    seen = {(1, 1)}
    q = deque([(1, 1)])
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen:
                ch = MAP[nr][nc]
                if ch == "#" or (nr, nc) in BLOCKED_CELLS:
                    continue
                if ch == "D":
                    continue       # the door stays shut for this check
                seen.add((nr, nc))
                q.append((nr, nc))
    check("V6b treasury reachable by BFS (no door)",
          TREASURY_POS in seen and TRAP_CELL in seen,
          f"treasury={'yes' if TREASURY_POS in seen else 'NO'} "
          f"brazier={'yes' if TRAP_CELL in seen else 'NO'}")


# ---------------------------------------------------------------------------
# V7. Determinism: same seed, same scripted action stream -> identical
#    info/reward stream.
def determinism():
    outs = []
    for rep in range(2):
        env = TerrariumV4(42)
        rng = random.Random(7)
        h = []
        for t in range(2000):
            a = rng.choice(ACTIONS)
            o, r, done, info = env.step(a)
            h.append((round(r, 6),
                      tuple(sorted(k for k in info if info[k] is True))))
            if done:
                env = TerrariumV4(42 * 3 + t)
        outs.append(h)
    check("V7 determinism (2 fresh envs, identical streams)",
          outs[0] == outs[1])


if __name__ == "__main__":
    oracle_torch()
    brute_force()
    scripted_chain()
    scorch_math()
    linger_correlation()
    gates()
    determinism()
    print(f"VERIFY_V4: {len(PASS)} PASS, {len(FAIL)} FAIL")
    if FAIL:
        print("FAILED:", FAIL)
