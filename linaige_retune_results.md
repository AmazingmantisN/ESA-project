# linaige_retune_results.md - declared re-tune on Session 1, one scored run on Sessions 2-5 (24 Oct 2026 23:29)

protocol sha256 6ce76d198dbed8e25cec108b40bff5aab0f057750227de4253e28812a506f6cf; params file sha256 8544166aaf210d77e353b3fce08d207948e429bd7123eb5094d106f9102df68a; frozen v1.4 file sha256 01f4fcc86280113322153be7db37ef724b6b6246b3eff129a695503fd3d30297.
Test: 5 stretches in Session2, Session3, Session4, Session5; scored frames per session: Session2 (RoomB) 1253, Session3 (RoomA) 284, Session4 (RoomA) 1470, Session5 (RoomC) 925 (total 3932); 30 s warm-up per stretch, 'h' frames not scored.
Two arms per method: 'frozen' = v1.4 parameters (the earlier LINAIGE run; recomputed here) and 'tuned' = tuned on Session 1 under protocol L1.0 (same budget for all four). Baselines get dht = frame median + 1.2 C. Intervals: 20 s moving-block bootstrap (2000), paired across arms within stretches. Only 5 stretches: intervals are wide.

## Sessions 2-5 pooled

| Arm | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |
|---|---|---|---|---|---|
| Ours-v1 (frozen) | 68.4 [61.4, 77.7] | 0.955 [0.851, 1.100] | 31.6 [22.3, 38.6] | 48.1 [36.8, 61.0] | 31.4 [27.5, 36.1] |
| Ours-v1 (tuned) | 22.4 [20.1, 26.3] | 0.248 [0.221, 0.294] | 77.6 [73.7, 79.9] | 94.9 [93.6, 96.2] | 70.6 [61.3, 74.5] |
| Ours-v2 (frozen) | 44.7 [39.6, 51.6] | 0.521 [0.466, 0.599] | 55.3 [48.4, 60.4] | 80.5 [75.2, 85.7] | 50.8 [44.4, 55.4] |
| Ours-v2 (tuned) | 21.4 [18.9, 26.2] | 0.237 [0.207, 0.290] | 78.6 [73.8, 81.1] | 95.0 [93.7, 96.2] | 71.7 [61.9, 75.5] |
| B-paper (frozen) | 61.3 [56.9, 69.7] | 0.974 [0.898, 1.149] | 38.7 [30.3, 43.1] | 91.9 [90.0, 94.2] | 39.8 [29.6, 43.3] |
| B-paper (tuned) | 49.9 [44.9, 58.2] | 0.612 [0.545, 0.720] | 50.1 [41.8, 55.1] | 90.1 [87.7, 92.5] | 45.7 [43.4, 48.8] |
| B-code (frozen) | 52.4 [49.0, 60.6] | 0.802 [0.749, 0.946] | 47.6 [39.4, 51.0] | 92.2 [90.1, 94.0] | 44.7 [34.9, 48.1] |
| B-code (tuned) | 50.1 [45.2, 58.3] | 0.613 [0.545, 0.720] | 49.9 [41.7, 54.8] | 90.1 [87.7, 92.6] | 45.6 [43.3, 48.7] |
| reference: always answer 1 person | 64.7 | 0.707 | 35.3 | 87.3 | 25.0 |
| reference: always answer 0 people | 77.5 | 1.257 | 22.5 | 0.0 | 25.0 |

## Paired change from re-tuning (tuned minus frozen; negative total error / positive exact = re-tuning helped)

| Method | total error, points | exact-count, points | occupied F1, points |
|---|---|---|---|
| Ours-v1 | -46.03 [-54.41, -38.34] | +46.03 [+38.34, +54.41] | +46.79 [+34.64, +57.50] |
| Ours-v2 | -23.37 [-28.37, -17.38] | +23.37 [+17.38, +28.37] | +14.52 [+9.90, +18.94] |
| B-paper | -11.39 [-21.23, -2.34] | +11.39 [+2.34, +21.23] | -1.83 [-5.16, +1.32] |
| B-code | -2.34 [-12.12, +6.47] | +2.34 [-6.47, +12.12] | -2.08 [-5.05, +1.19] |

## Paired differences between methods, tuned arms (negative total error = first method better)

| Comparison | total error, points | exact-count, points |
|---|---|---|
| Ours-v1 - B-paper | -27.54 [-35.68, -21.02] | +27.54 [+21.02, +35.68] |
| Ours-v1 - B-code | -27.70 [-35.93, -21.18] | +27.70 [+21.18, +35.93] |
| Ours-v2 - B-paper | -28.56 [-37.23, -21.01] | +28.56 [+21.01, +37.23] |
| Ours-v2 - B-code | -28.71 [-37.37, -21.20] | +28.71 [+21.20, +37.37] |
| Ours-v2 - Ours-v1 | -1.02 [-2.75, +1.09] | +1.02 [-1.09, +2.75] |

## Per session (descriptive: one to two stretches each; total error % and exact-count %)

| Arm | Session2 (RoomB) | Session3 (RoomA) | Session4 (RoomA) | Session5 (RoomC) |
|---|---|---|---|---|
| Ours-v1 (frozen) | 66.0 [43.5, 86.5] / 34.0 [13.5, 56.5] | 28.2 [19.7, 72.0] / 71.8 [28.0, 80.3] | 76.9 [71.5, 81.7] / 23.1 [18.3, 28.5] | 70.5 [62.8, 85.3] / 29.5 [14.7, 37.2] |
| Ours-v1 (tuned) | 12.6 [7.9, 15.4] / 87.4 [84.6, 92.1] | 11.6 [7.3, 19.4] / 88.4 [80.6, 92.7] | 30.1 [26.5, 36.6] / 69.9 [63.4, 73.5] | 26.7 [22.5, 34.5] / 73.3 [65.5, 77.5] |
| Ours-v2 (frozen) | 24.5 [9.4, 36.6] / 75.5 [63.4, 90.6] | 24.6 [19.7, 55.2] / 75.4 [44.8, 80.3] | 64.8 [60.5, 70.1] / 35.2 [29.9, 39.5] | 46.5 [42.2, 55.9] / 53.5 [44.1, 57.8] |
| Ours-v2 (tuned) | 9.3 [2.4, 16.9] / 90.7 [83.1, 97.6] | 10.2 [6.2, 17.8] / 89.8 [82.2, 93.8] | 30.6 [28.0, 36.4] / 69.4 [63.6, 72.0] | 26.5 [22.6, 33.2] / 73.5 [66.8, 77.4] |
| B-paper (frozen) | 41.0 [27.9, 57.6] / 59.0 [42.4, 72.1] | 50.4 [41.0, 68.4] / 49.6 [31.6, 59.0] | 81.1 [78.1, 87.5] / 18.9 [12.5, 21.9] | 60.8 [53.7, 75.2] / 39.2 [24.8, 46.3] |
| B-paper (tuned) | 64.0 [46.3, 80.2] / 36.0 [19.8, 53.7] | 10.9 [5.0, 17.2] / 89.1 [82.8, 95.0] | 43.9 [40.9, 50.2] / 56.1 [49.8, 59.1] | 52.3 [47.9, 64.8] / 47.7 [35.2, 52.1] |
| B-code (frozen) | 25.1 [12.8, 35.8] / 74.9 [64.2, 87.2] | 33.8 [27.3, 44.8] / 66.2 [55.2, 72.7] | 74.2 [72.2, 82.7] / 25.8 [17.3, 27.8] | 60.5 [55.1, 73.0] / 39.5 [27.0, 44.9] |
| B-code (tuned) | 64.0 [46.1, 80.3] / 36.0 [19.7, 53.9] | 10.9 [5.0, 17.2] / 89.1 [82.8, 95.0] | 44.4 [41.3, 50.4] / 55.6 [49.6, 58.7] | 52.3 [47.9, 64.8] / 47.7 [35.2, 52.1] |

## By true count, tuned arms (share of scored frames where the smoothed count equals the truth / mean count produced)

| True count | scored frames | Ours-v1 | Ours-v2 | B-paper | B-code |
|---|---|---|---|---|---|
| 0 | 884 | 92.5 / 0.08 | 86.8 / 0.15 | 96.5 / 0.04 | 96.5 / 0.04 |
| 1 | 1389 | 81.9 / 0.90 | 80.6 / 0.98 | 57.7 / 1.07 | 57.2 / 1.07 |
| 2 | 1424 | 70.9 / 1.70 | 77.7 / 1.78 | 20.9 / 1.14 | 20.9 / 1.14 |
| 3 | 235 | 37.0 / 2.14 | 41.7 / 2.20 | 7.7 / 1.60 | 7.7 / 1.60 |

Consistency check: the 'frozen' arm per-session numbers must equal the matching rows of linaige_results.md (same code, same parameters). Reading guide: this is a declared follow-up tuned on one session; it shows whether the methods can adapt to a ceiling-mounted geometry, not how they would do in a room they have never seen with parameters they have never seen. Report whatever it shows.
