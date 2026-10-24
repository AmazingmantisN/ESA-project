# count_metrics.md - declared post-hoc, descriptive (frozen parameters, no tuning)

params_frozen.json frozen_at 2026-10-23T03:31:33+05:30; warm-up 30 s; intervals = 20 s moving-block bootstrap (2000), paired across methods, frames pooled over streams.
MAE = mean |count - truth|; F1 = occupied (count > 0) vs vacant; BAS = mean per-class recall over the true counts present (0, 1).

## A. Real held-out streams, injected sources (the 10 test_* streams)

Same frames as test_results.md (Table 5.2).

| Method | MAE (people) | Exact-count % | Occupied F1 % | BAS % |
|---|---|---|---|---|
| Ours-v1 | 0.166 [0.128, 0.208] | 83.4 [79.2, 87.2] | 81.7 [76.1, 86.8] | 81.8 [77.3, 85.8] |
| Ours-v2 | 0.034 [0.015, 0.045] | 96.6 [95.5, 98.5] | 95.9 [94.5, 98.2] | 96.1 [94.8, 98.3] |
| B-paper | 0.381 [0.326, 0.423] | 70.1 [67.0, 73.3] | 88.8 [86.2, 91.2] | 67.9 [64.8, 71.2] |
| B-code | 0.336 [0.322, 0.351] | 67.3 [65.6, 68.6] | 54.7 [47.5, 59.6] | 62.7 [60.7, 64.1] |

MAE by stream:

| Stream | Ours-v1 | Ours-v2 | B-paper | B-code |
|---|---|---|---|---|
| empty_clean | 0.000 | 0.000 | 0.006 | 0.006 |
| empty_heater | 0.000 | 0.000 | 0.006 | 0.006 |
| empty_heater_weak | 0.259 | 0.000 | 0.414 | 0.010 |
| empty_laptop | 0.000 | 0.000 | 0.006 | 0.006 |
| empty_laptop_weak | 0.000 | 0.000 | 0.319 | 0.006 |
| single_clean | 0.044 | 0.014 | 0.492 | 0.778 |
| single_heater | 0.707 | 0.237 | 0.770 | 0.740 |
| single_heater_weak | 0.441 | 0.086 | 1.024 | 0.743 |
| single_laptop | 0.200 | 0.034 | 0.511 | 0.777 |
| single_laptop_weak | 0.171 | 0.024 | 0.599 | 0.767 |

## B. Table 5.1 with intervals (clean held-out windows, ours vs their logged output)

Intervals: 20 s moving-block bootstrap of exact-count accuracy, per system. Longest error = longest run of wrong frames / fps.

| Session | System | Exact-count % [95 % CI] | MAE | Longest error (s) |
|---|---|---|---|---|
| 0 persons | Papanashi logged | 94.0 [91.7, 95.6] | 0.060 | 1.0 |
| 0 persons | Ours-v1 | 100.0 [100.0, 100.0] | 0.000 | 0.0 |
| 0 persons | Ours-v2 | 100.0 [100.0, 100.0] | 0.000 | 0.0 |
| 0 persons | B-paper | 99.4 [98.6, 100.0] | 0.006 | 0.8 |
| 0 persons | B-code | 99.4 [98.6, 100.0] | 0.006 | 0.8 |
| 1 person | Papanashi logged | 81.0 [71.5, 88.8] | 0.235 | 9.7 |
| 1 person | Ours-v1 | 95.6 [94.8, 100.0] | 0.044 | 6.8 |
| 1 person | Ours-v2 | 98.6 [97.9, 100.0] | 0.014 | 2.1 |
| 1 person | B-paper | 63.6 [55.4, 71.0] | 0.492 | 10.8 |
| 1 person | B-code | 24.8 [16.7, 31.9] | 0.778 | 18.9 |

## C. Autocorrelation of the per-frame error indicator (real held-out streams)

Lag (s) where the mean autocorrelation first drops below 0.1 (streams with at least 1 % errors):

- Ours-v1: 17.2 s
- Ours-v2: 6.2 s
- B-paper: 7.0 s
- B-code: 1.8 s

If the errors stay correlated well past 20 s, rerun the intervals with 40 s blocks and report both.

