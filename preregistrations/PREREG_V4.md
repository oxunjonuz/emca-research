# PREREG V4 — the epistemic-value world: does rejecting the decoy pay?

Written BEFORE the first matrix run (after the toy W1–W8: 8/8 PASS,
2026-09-10). Directive op_097e99fae22e + op_6d6b5f5a1105.

## The world (verified 10/10, toy 8/8)

TerrariumV4 = TerrariumV33 whole + the brazier pocket (3,6):
(grasp, torch_lit) decoy — a world-event flame, linger-correlated
with competent storm-tree grasping (P(lit|grasp)=0.66 vs 0.03, RR=20
in the raw world), oracle-equal for all actions. The v4 goal menu has
a torch goal; the treasury food ('$', (2,1)) needs a banked torch
(collected by STANDING on the brazier), eaten in calm+warm. The
believer's causal block fires 'grasp' at the brazier (the v3.2
armour is OFF in the v4 arms); the pocket scorches 2.2/step beside a
lit brazier.

Toy numbers (8000 steps): believer pocket-grasps 330/1066/1475 vs
rejector 38/2/15; torch-goal steps 2403/2521/3590 vs 195/261/489.
The false belief is behaviourally ACTIVE.

## Primary contrast (pre-registered)

D_s = reward(v4_rejector) − reward(v4_believer), paired per seed.
The toy sign was +/+/− (seeds 1,2 positive, 3 negative) — the known
±16%/seed weather noise of this lineage applies. Verdicts:
* V1 PAYS: mean D >= +300 (the pre-registered practical floor of the
  v3.3 lineage, ~2.5% of a life's reward) AND exact sign-test p <= 0.05.
* V2 HURTS: mean D <= −300 AND sign-test p <= 0.05.
* V3 UNRESOLVED: otherwise (report the CI; the honest reading of the
  v3.3-seeds lesson is expected: the noise may swallow the effect).

## Secondary contrasts

* D2 = reward(v4_rejector) − reward(v4_assoc): the assoc arm also
  plans off the decoy (its assoc layer carries it) — a second
  believer. Same verdict rules.
* D3 = reward(v4_rejector) − reward(v4_spec): spec rejected the torch
  decoy in 3/3 toy seeds (incidentally) — expected small.
* D4 = reward(v4_curious) − reward(v4_rejector): bitter curiosity vs
  the honest planner.

## Matrix criteria (measure, don't wish)

* T1 IDENTIFIER STABILITY (control): decoy in believer causal >=
  8/10 seeds; NOT in rejector causal >= 8/10; true edges (eat->ate,
  grasp->tree_gather) in rejector >= 8/10.
* T2 THE BELIEF TAX (the behavioural decomposition): per-seed
  believer pocket-grasps and torch-goal steps reported; PASS if the
  believer's pocket-grasp count exceeds the rejector's in >= 8/10
  seeds (the decoy edge firing where the flame is).
* T3 THE CHAIN: treasury meals summed over arms (rejector/assoc/
  spec/believer/curious) >= 1 in >= 4/10 seeds for at least one arm;
  reported per arm (the chain is scarce by design).
* T4 CURIOSITY IS BITTER: v4_pure deaths > every planner arm in >=
  8/10 seeds; v4_curious deaths >= v4_rejector deaths in >= 6/10.
* T5 BASELINES: random/qlearn/ngram deaths > every planner arm.
* Determinism: fresh subprocess re-run of (rejector, seed 1) and
  (believer, seed 1) — counters and edge sets identical.
* Steps-audit: every JSON steps=16000.

## Matrix

9 conditions (v4_believer, v4_spec, v4_assoc, v4_rejector,
v4_curious, v4_pure, random, qlearn, ngram) x 10 seeds (1–10) x
16000 steps. Note: qlearn/ngram run ONCE per seed (3 runs each) as
baselines — same as the v3.3 protocol? NO: the v3.3 protocol ran them
per seed too; we follow it (10 seeds each).
