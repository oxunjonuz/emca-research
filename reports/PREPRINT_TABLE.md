# EMCA campaign -- the preprint table

All numbers are means over 3 seeds, read directly from the matrix JSONs on disk (fresh process, no agent imports). Lives: 16000 steps (v3.1: 16000).

## v3.1 -- TerrariumV31 (actionable decoy: chime zone == tree zone, flat grasp cost, no scarcity)

| condition | reward | deaths | fruits | berries | chimes | treasures | grasp@bell | grasp@bell-no-tree | decoy-in-causal |
|---|---|---|---|---|---|---|---|---|---|
| curious | 467.5 | 85.7 | 6.3 | 806.3 | 77.7 | 0.0 | 98.0 | 0.0 | 0/3 |
| emca_nocausal | 10486.7 | 45.0 | 1258.0 | 564.7 | 126.0 | 1.0 | 1913.3 | 0.0 | 3/3 |
| emca_v21 | 12879.8 | 40.0 | 1558.0 | 536.3 | 132.3 | 0.7 | 2453.3 | 0.0 | 3/3 |
| emca_v22 | 12879.8 | 40.0 | 1558.0 | 536.3 | 132.3 | 0.7 | 2453.3 | 0.0 | 3/3 |
| emca_v25c | 12158.3 | 41.3 | 1467.3 | 546.7 | 119.3 | 1.0 | 2255.0 | 0.0 | 0/3 |
| ngram | 2050.5 | 79.0 | 282.7 | 166.0 | 36.3 | 0.0 | 1661.3 | 0.0 | 0/3 |
| qlearn | 571.3 | 87.3 | 99.0 | 194.3 | 43.3 | 0.0 | 770.7 | 0.0 | 0/3 |
| random | -0.7 | 87.0 | 35.7 | 126.0 | 46.0 | 0.0 | 551.7 | 0.0 | 0/3 |

## v3.2 -- TerrariumV32 (separated geometry: chime far zone, grasp cost 0.6, altar gray edge, no scarcity)

| condition | reward | deaths | fruits | berries | chimes | treasures | grasp@bell | grasp@bell-no-tree | decoy-in-causal |
|---|---|---|---|---|---|---|---|---|---|
| curious_pure | -330.8 | 93.3 | 3.0 | 83.3 | 41.0 | 0.0 | 34.3 | 0.0 | 0/3 |
| curious_surv | 39436.0 | 0.7 | 4683.0 | 511.7 | 68.7 | 0.0 | 3088.3 | 0.0 | 0/3 |
| emca_nocausal | 21434.3 | 22.7 | 2531.0 | 679.0 | 73.3 | 0.0 | 1528.7 | 0.0 | 3/3 |
| emca_v21 | 21744.8 | 21.0 | 2578.3 | 671.3 | 79.7 | 0.0 | 1574.3 | 0.0 | 3/3 |
| emca_v22 | 21744.8 | 21.0 | 2578.3 | 671.3 | 79.7 | 0.0 | 1574.3 | 0.0 | 3/3 |
| emca_v25c | 21553.5 | 22.0 | 2507.7 | 660.3 | 86.3 | 0.0 | 1463.7 | 0.0 | 0/3 |
| ngram | 1273.2 | 88.0 | 163.3 | 204.3 | 4.3 | 0.0 | 739.3 | 0.0 | 0/3 |
| prober | 14413.5 | 23.7 | 1607.7 | 833.3 | 79.7 | 0.0 | 951.3 | 0.0 | 0/3 |
| qlearn | 850.2 | 87.0 | 90.3 | 196.0 | 7.7 | 0.0 | 1018.0 | 0.0 | 0/3 |
| random | -15.2 | 92.3 | 27.0 | 151.0 | 25.7 | 0.0 | 550.0 | 0.0 | 0/3 |

## v3.3 -- TerrariumV33 (scarcity: dynamic grasp cost 0.6/1.8, altar offering 1.0, berries 2/1, tree 18 capped 60/storm, fury -3.0)

| condition | reward | deaths | fruits | berries | chimes | treasures | grasp@bell | grasp@bell-no-tree | decoy-in-causal |
|---|---|---|---|---|---|---|---|---|---|
| curious_chain | 11328.8 | 61.3 | 1281.3 | 107.7 | 26.3 | 16.0 | 924.7 | 55.3 | 0/3 |
| curious_pure | -389.5 | 98.7 | 0.3 | 81.0 | 40.3 | 0.0 | 33.7 | 33.7 | 0/3 |
| curious_surv | 12058.3 | 59.0 | 1192.0 | 748.3 | 68.7 | 0.0 | 911.7 | 67.7 | 0/3 |
| emca_nocausal | 15820.0 | 45.0 | 1521.3 | 678.7 | 76.7 | 0.0 | 1019.0 | 38.7 | 3/3 |
| emca_v21 | 15387.3 | 47.0 | 1474.7 | 715.3 | 96.7 | 0.0 | 972.3 | 35.3 | 3/3 |
| emca_v22 | 15387.3 | 47.0 | 1474.7 | 715.3 | 96.7 | 0.0 | 972.3 | 35.3 | 3/3 |
| emca_v25c | 15516.3 | 43.0 | 1525.7 | 707.0 | 91.3 | 0.0 | 889.7 | 36.0 | 0/3 |
| ngram | 535.2 | 97.0 | 92.0 | 149.7 | 7.7 | 0.0 | 1368.3 | 1253.7 | 0/3 |
| prober | 14978.8 | 39.0 | 1423.7 | 638.0 | 63.7 | 0.7 | 1016.3 | 168.7 | 0/3 |
| qlearn | 292.0 | 96.0 | 48.3 | 145.3 | 5.3 | 0.0 | 1109.3 | 1018.7 | 0/3 |
| random | -208.8 | 98.3 | 15.7 | 111.3 | 23.0 | 0.0 | 530.3 | 516.0 | 0/3 |

## Headline contrasts across worlds

| contrast | v3.1 | v3.2 | v3.3 |
|---|---|---|---|
| believer (v2.1) reward | 12880 | 21745 | 15387 |
| rejector (v2.5c) reward | 12158 | 21554 | 15516 |
| rejector - believer | -722 | -191 | 129 |
| prober reward | - | 14414 | 14979 |
| curious_surv reward | - | 39436 | 12058 |
| curious_surv deaths | - | 1 | 59 |
| best arm reward | 12880 | 39436 | 15820 |
| best arm name | emca_v21 | curious_surv | emca_nocausal |
| chain treasures | - | - | 16 |
| v2.5c deaths | 41 | 22 | 43 |
| v2.5c fruits | 1467 | 2508 | 1526 |
