# Announcement — short form (3–4 paragraphs)

**Where Protection Actually Lives: Eleven Preregistered Instruments for the Safety of a
Goal-Directed Causal Agent, and the Measured Boundary of Each**
Preprint (corrected publication version 2): https://doi.org/10.5281/zenodo.22772224
Code, raw data, preregistrations, verifiers: https://github.com/oxunjonuz/emca-research

---

## English

We spent twenty preregistered campaigns asking one narrow question: when a goal-directed
agent can harm a third party, **what actually restrains it — and where does that
restraint stop?** The agent is a model-based causal reasoner; the worlds are deliberately
small, and each campaign adds exactly one mechanism to the world of the last, so that
every result is a causal statement about that one mechanism. Every campaign was
preregistered before its first cell, and every number in every report was checked by a
world oracle, an independent pass in a fresh process that imports no producer code, and a
mechanical fact-check.

The central finding is uncomfortable and simple: **every defence we built inherited the
corruptibility of the thing it protected.** A brake that reads a price is bought through
the very channel it measures — 0.25 reward units per unit of harm, a price fixed by
arithmetic, while identical money paid through any other channel moves not one decision
field. Provenance accounting closes that money channel and moves the hole to the *label*
on the payment; a lying label buys the same agent completely. An honest independent
attestation closes the label and moves the hole to the auditor's *timeliness*. Buy the
auditor, and the hole returns field for field — thirty drains, the keeper dead, zero
refusals, exactly the harm the attestation was built to prevent. Move the boundary out of
the agent and into the world (complete mediation), and it genuinely works: it stops an
agent that already *wants* the harm, where an agent-side scope is refused zero times
because the scoped agent never asks. But give that world-side boundary a price and it is
worth exactly the enforcer's honesty — bought, it stops refusing while **still claiming
the granted scope on every step**. Each specific defence has a measured boundary, and the
vulnerability moves to the next channel.

Two findings we did not expect. First, the harm is **wayfinding-shaped**: it is complete
in the first forty steps, thousands of steps before the agent's causal module issues a
single verdict — so on this architecture the safety question is not about the reasoning
at all. Second, **truth alone does not select action**: an agent with no reward, no cost
and no death learns its world to a model error of 0.036 against an oracle ceiling of
0.033, and then behaves
indistinguishably from random; a criterion is what makes it act, and that criterion is
itself fakeable on its own channel. And one result runs against the obvious moral:
**internal architecture is not useless** — a hard rule that simply forbids the harmful
act held in 170 of 170 measured cells, at a measured price in reward.

We report every refuted prediction and every defect we found in our own instrumentation,
including an absolute claim of ours that did not survive replication on fresh seeds. An
independent 2026 study of reinforcement-learning policies (Che & Wu, arXiv:2606.16914)
reaches a structurally convergent conclusion about visible self-benefit channels; our
results were obtained independently and before any acquaintance with that work, and the
convergence is structural, not causal. The honest conclusion is not that defence fails,
but that **a boundary is only as good as the incorruptibility of whoever holds it — a
bought boundary lies about being a boundary.**

---

## Russian (short version)

Двадцать пререгистрированных кампаний — один узкий вопрос: когда агент, стремящийся к
цели, может навредить третьей стороне, **что его на самом деле удерживает и где эта
защита кончается?** Главный результат неудобен и прост: **каждая защита наследовала
продажность того, что защищала.** Тормоз, читающий цену, покупается через тот самый
канал, который он измеряет — 0,25 единицы награды за единицу вреда, цена, заданная
арифметикой, тогда как те же деньги через любой другой канал не двигают ни одного поля
решения. Учёт «кто кому платил» закрывает денежный канал и переносит дыру на *метку*
платежа; лживая метка покупает того же агента полностью. Честное независимое заверение
закрывает метку и переносит дыру в *своевременность* заверяющего. Купите заверяющего —
и дыра возвращается поле в поле: тридцать стоков, хранитель мёртв, ноль отказов.
Вынесите границу из агента в мир (полное посредничество) — и она действительно
работает: останавливает агента, который уже *хочет* вреда, тогда как граница внутри
агента отклоняется ноль раз, потому что суженный агент просто не просит. Но дайте этой
границе цену — и она стоит ровно честности исполнителя: купленная, она перестаёт
отказывать, **всё ещё заявляя выданные права на каждом шаге**. У каждой конкретной
защиты есть измеренная граница, и уязвимость переезжает в следующий канал.

Два неожиданных результата: вред **происходит на этапе поиска пути** — он завершён за
первые сорок шагов, задолго до первого вердикта причинного модуля; и **истина сама по
себе не выбирает действие** — агент без награды, цены и смерти выучивает мир с
ошибкой модели 0,036 при эталонной ошибке оракула 0,033 и затем ведёт себя
неотличимо от случайного. И
одно против очевидной морали: **внутренняя архитектура не бесполезна** — жёсткое
правило, просто запрещающее вредное действие, удержало хранителя живым в 170 из 170
измеренных клеток. Честный вывод не «защита не работает», а **«граница хороша ровно
настолько, насколько неподкупен тот, кто её держит: купленная граница лжёт о том, что
она граница»**.

---

## Notes for whoever posts it

Two claims are the ones most likely to be misread, and the paper says neither:

1. **"Protection lives in the environment, not the agent"** — this is *not* the paper's
   conclusion. The paper says each *specific* defence has a measured boundary, and that
   an internal hard rule held in **every** cell measured (170/170). The strong
   environment-over-agent form is explicitly withdrawn in the paper's errata.
2. **The convergence with Che & Wu** is **structural, not causal** — two independent
   lines reached the same shape. No priority is claimed in either direction.
