# linaige_results.md - one-shot transfer test, frozen parameters (run 24 Oct 2026 22:29)

params_frozen.json frozen_at 2026-10-23T03:31:33+05:30. LINAIGE v2, 15 continuous stretches >= 60 s; 30 s warm-up per stretch; frames marked 'h' (hard to label) not scored.
B-paper and B-code were given dht = frame median + 1.2 C (assumption, from Papanashi's pod). Intervals: 20 s moving-block bootstrap (2000), paired across methods, within stretches. Truth = people_number (0-3).

## ALL sessions pooled

| Method | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |
|---|---|---|---|---|---|
| Ours-v1 | 71.0 [66.9, 75.1] | 0.979 [0.916, 1.055] | 29.0 [24.9, 33.1] | 31.2 [24.8, 41.5] | 28.6 [26.9, 31.4] |
| Ours-v2 | 50.1 [47.0, 53.4] | 0.577 [0.544, 0.619] | 49.9 [46.6, 53.0] | 74.4 [71.5, 79.1] | 44.9 [41.3, 48.3] |
| B-paper | 61.1 [59.3, 65.0] | 0.961 [0.918, 1.042] | 38.9 [35.0, 40.7] | 91.5 [89.9, 92.9] | 39.7 [35.2, 41.7] |
| B-code | 53.5 [51.7, 57.9] | 0.755 [0.721, 0.824] | 46.5 [42.1, 48.3] | 91.0 [89.4, 92.4] | 44.0 [39.6, 46.2] |

## Session1

| Method | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |
|---|---|---|---|---|---|
| Ours-v1 | 72.6 [68.0, 76.0] | 0.995 [0.909, 1.071] | 27.4 [24.0, 32.0] | 17.6 [9.6, 30.5] | 26.4 [25.6, 27.8] |
| Ours-v2 | 53.5 [50.0, 56.7] | 0.614 [0.570, 0.660] | 46.5 [43.3, 50.0] | 69.9 [65.7, 75.9] | 39.2 [36.3, 41.7] |
| B-paper | 60.9 [59.1, 64.1] | 0.952 [0.895, 1.015] | 39.1 [35.9, 40.9] | 91.2 [88.9, 92.8] | 38.7 [35.4, 40.8] |
| B-code | 54.2 [51.3, 58.1] | 0.724 [0.675, 0.782] | 45.8 [41.9, 48.7] | 90.2 [88.1, 92.2] | 42.1 [37.8, 45.3] |

## Session2

| Method | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |
|---|---|---|---|---|---|
| Ours-v1 | 66.0 [43.2, 86.5] | 0.824 [0.500, 1.072] | 34.0 [13.5, 56.8] | 76.1 [57.3, 91.5] | 52.4 [37.1, 69.1] |
| Ours-v2 | 24.5 [8.8, 37.5] | 0.255 [0.094, 0.390] | 75.5 [62.5, 91.2] | 94.0 [85.2, 99.2] | 80.5 [53.7, 93.4] |
| B-paper | 41.0 [27.0, 57.8] | 0.484 [0.300, 0.700] | 59.0 [42.2, 73.0] | 98.9 [96.5, 100.0] | 60.6 [26.3, 73.3] |
| B-code | 25.1 [12.4, 36.2] | 0.270 [0.133, 0.396] | 74.9 [63.8, 87.6] | 99.3 [97.9, 100.0] | 76.4 [41.3, 87.5] |

## Session3

| Method | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |
|---|---|---|---|---|---|
| Ours-v1 | 28.2 [19.6, 71.9] | 0.444 [0.440, 0.737] | 71.8 [28.1, 80.4] | 0.0 [0.0, 0.0] | 25.0 [25.0, 50.0] |
| Ours-v2 | 24.6 [19.6, 55.0] | 0.387 [0.372, 0.606] | 75.4 [45.0, 80.4] | 36.0 [22.2, 47.6] | 31.4 [25.0, 62.0] |
| B-paper | 50.4 [40.6, 68.4] | 0.757 [0.566, 1.066] | 49.6 [31.6, 59.4] | 61.5 [51.9, 95.0] | 54.3 [34.4, 67.3] |
| B-code | 33.8 [26.8, 44.7] | 0.433 [0.321, 0.583] | 66.2 [55.3, 73.2] | 73.5 [61.6, 89.3] | 37.3 [25.0, 73.0] |

## Session4

| Method | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |
|---|---|---|---|---|---|
| Ours-v1 | 76.9 [71.7, 81.5] | 1.060 [0.973, 1.181] | 23.1 [18.5, 28.3] | 3.8 [0.0, 10.9] | 25.0 [25.0, 25.0] |
| Ours-v2 | 64.8 [60.2, 70.0] | 0.788 [0.730, 0.873] | 35.2 [30.0, 39.8] | 54.2 [46.1, 62.9] | 30.7 [28.8, 32.2] |
| B-paper | 81.1 [78.1, 87.6] | 1.444 [1.335, 1.685] | 18.9 [12.4, 21.9] | 88.6 [84.8, 91.0] | 19.5 [10.8, 26.6] |
| B-code | 74.2 [71.9, 82.7] | 1.293 [1.242, 1.483] | 25.8 [17.3, 28.1] | 87.8 [83.9, 90.2] | 33.3 [23.4, 37.7] |

## Session5

| Method | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |
|---|---|---|---|---|---|
| Ours-v1 | 70.5 [62.3, 84.9] | 1.125 [0.980, 1.470] | 29.5 [15.1, 37.7] | 51.8 [29.2, 70.5] | 29.9 [25.0, 38.1] |
| Ours-v2 | 46.5 [42.2, 55.9] | 0.497 [0.447, 0.608] | 53.5 [44.1, 57.8] | 93.3 [90.5, 97.6] | 52.8 [45.7, 57.9] |
| B-paper | 60.8 [53.6, 75.4] | 0.956 [0.787, 1.253] | 39.2 [24.6, 46.4] | 92.3 [88.0, 97.1] | 40.6 [27.0, 46.2] |
| B-code | 60.5 [54.7, 72.9] | 0.855 [0.751, 1.101] | 39.5 [27.1, 45.3] | 91.4 [87.0, 96.3] | 38.7 [22.5, 47.0] |

## By true count (all sessions pooled): share of scored frames where the smoothed count equals the truth, and the mean count produced

| True count | scored frames | Ours-v1 exact % / mean count | Ours-v2 exact % / mean count | B-paper exact % / mean count | B-code exact % / mean count |
|---|---|---|---|---|---|
| 0 | 2361 | 99.8 / 0.00 | 97.3 / 0.03 | 40.5 / 1.02 | 49.0 / 0.75 |
| 1 | 4290 | 7.7 / 0.08 | 41.0 / 0.41 | 34.2 / 2.03 | 44.1 / 1.72 |
| 2 | 2775 | 7.0 / 0.42 | 30.6 / 1.14 | 44.9 / 2.76 | 50.5 / 2.37 |
| 3 | 498 | 0.0 / 0.26 | 10.6 / 1.49 | 39.2 / 3.77 | 32.5 / 3.13 |

Reading guide: LINAIGE is a ceiling-mounted sensor in other rooms, with up to 3 people and no placed heat sources; the frozen parameters were tuned on a corner-mounted sensor in one study pod. Counts of 2 or more people close together are expected to fail at 8x8. This is a transfer test, not a benchmark win.
