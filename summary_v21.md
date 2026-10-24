# summary_v21.md (23 Oct 2026 10:49)

Python 3.13.5, 20 cores, Windows. Total 213 s.

Protocol v2.1 json sha256 6ec75fe0a66e127a34bc6fa1aac792b5d0041fc42f7550609c9a85325ea816cf
md sha256 69507fd23b7b70bf01668fd5428d232deb150450ea1d154644d5aad80963c60c
official_run=False jobs=18 dev streams=106

## Checks

| Check | Result | Seconds | Note |
|---|---|---|---|
| build run_pc + test_modes (g++) | PASS | 4 |  |
| test_modes (expect 38 tests, 0 failed) | PASS | 2 | 38 tests, 0 failed |
| check_v1_equiv (v2 code with v1 flags == v1 reference) | PASS | 22 | 173 comparisons (22 parameter sets), mismatches: 0 |
| check_v2_nested (v2 nested == v1; liveness off changes nothing) | PASS | 12 | nested (mode 3 defaults == mode 0): 132 comparisons, mismatches: 0 |
| tune_sweep_v2 protocol v2.1 (dev only) QUICK TEST | PASS | 118 |  |
| check_v21_rescore (v1.4 winners reproduce their real dev scores) | PASS | 22 | ALL MATCH: v2.1 tool reproduces the v1.4 winners' real dev scores |
| latency_check (report only) | PASS | 1 |  |
| robust_check FRESH seed 303, v21 winners | PASS | 8 |  |
| robust_check FRESH seed 404, v21 winners | PASS | 8 |  |
| robust_check FRESH seed 303, v14 winners | PASS | 8 |  |
| robust_check FRESH seed 404, v14 winners | PASS | 8 |  |

## v2.1 dev winners (NOT frozen; in-sample). Error = false% + missed%, lower is better

| Entry | Dev total | Real orig-10 | Real rob-16 | Synth dev-80 | False | Missed | Worst stream | Untuned ref | Stage-1 best | Edge params |
|---|---|---|---|---|---|---|---|---|---|---|
| ours | 14.42 | 15.25 | 13.40 | 14.63 | 8.65 | 5.78 | 95.6 | 17.69 | 19.64 | none |
| bpaper | 33.82 | 26.32 | 48.74 | 26.41 | 29.18 | 4.64 | 91.4 | 80.67 | 33.82 | none |
| bcode | 28.21 | 21.87 | 32.22 | 30.53 | 13.07 | 15.14 | 97.7 | 43.88 | 28.21 | none |
| bcode_asis | 80.31 | 79.33 | 93.00 | 68.61 | 80.20 | 0.11 | 100.0 | 81.73 | 80.31 | none |
| ours_v2 | 19.66 | 22.24 | 16.17 | 20.55 | 0.22 | 19.44 | 100.0 | 17.69 | 24.66 | drift |

Same dev pools, the v1.4 frozen winners (for comparison; they were tuned only on the 26 real streams):

| Entry | Dev total (equal pool weights) | Real orig-10 | Real rob-16 | Synth dev-80 |
|---|---|---|---|---|
| ours (v1.4) | 11.45 | 16.30 | 4.29 | 13.76 |
| bpaper (v1.4) | 33.37 | 24.96 | 47.54 | 27.62 |
| bcode (v1.4) | 28.61 | 25.10 | 25.15 | 35.59 |
| bcode_asis (v1.4) | 80.24 | 79.25 | 93.05 | 68.41 |
| ours_v2 (v1.4) | 8.12 | 1.67 | 0.00 | 22.70 |

Synthetic dev error by scenario (winner of each entry; mean over 5 seeds; in-sample):

| Scenario | ours | bpaper | bcode | bcode_asis | ours_v2 | ours v1.4 | ours_v2 v1.4 |
|---|---|---|---|---|---|---|---|
| A1 | 0.0 | 1.5 | 1.5 | 1.8 | 0.0 | 0.0 | 0.0 |
| A10 | 4.7 | 20.1 | 18.9 | 77.1 | 20.2 | 9.8 | 19.1 |
| A11 | 20.9 | 27.3 | 24.0 | 73.3 | 21.3 | 14.2 | 33.3 |
| A12 | 24.3 | 40.3 | 54.7 | 73.9 | 49.3 | 19.0 | 23.5 |
| A13 | 1.3 | 12.2 | 18.4 | 81.5 | 0.0 | 1.1 | 12.7 |
| A14 | 19.2 | 28.7 | 49.9 | 67.8 | 24.9 | 19.3 | 15.1 |
| A15 | 10.4 | 17.8 | 38.8 | 73.8 | 3.0 | 11.2 | 46.7 |
| A2 | 1.6 | 38.3 | 3.1 | 99.5 | 0.0 | 0.0 | 0.0 |
| A3 | 0.0 | 0.9 | 0.1 | 100.0 | 0.0 | 0.0 | 0.0 |
| A4 | 11.2 | 27.6 | 0.2 | 100.0 | 0.0 | 6.5 | 0.0 |
| A5 | 7.7 | 29.7 | 11.0 | 98.7 | 0.0 | 4.0 | 22.3 |
| A6 | 8.8 | 12.1 | 63.5 | 4.1 | 26.7 | 9.6 | 5.1 |
| A7 | 15.3 | 49.1 | 37.8 | 76.9 | 25.2 | 10.9 | 26.0 |
| A8 | 19.1 | 24.7 | 56.1 | 73.4 | 42.8 | 26.1 | 55.6 |
| A9 | 75.0 | 51.6 | 68.7 | 37.1 | 77.7 | 76.0 | 77.8 |
| G1 | 14.4 | 40.6 | 41.7 | 59.0 | 37.8 | 12.4 | 26.1 |

- ours: `{"window_s": 5.0808, "drift": 0.4312, "contrast": 1.294, "k": 0.4449, "smooth_s": 1.3, "maxmissed_s": 1.0}`; top-10 range 14.42-41.09
- bpaper: `{"timebase": "paper", "drift": 0.6413, "dht_offset": 0.2, "smooth_s": 1.3, "maxmissed_s": 0.5}`; top-10 range 33.82-42.87
- bcode: `{"npersist": 40.0, "drift": 0.6413, "dht_offset": 0.2, "smooth_s": 1.3, "maxmissed_s": 0.5}`; top-10 range 28.21-34.55
- bcode_asis: `{"npersist": 20.0, "drift": 0.8581, "dht_offset": 0.1, "smooth_s": 1.3, "maxmissed_s": 0.5}`; top-10 range 80.24-81.73
- ours_v2: `{"window_s": 2.0668, "drift": 1.3269, "contrast": 1.5835, "k": 0.9837, "smooth_s": 1.3, "maxmissed_s": 2.5, "persist_s": 30.0235, "hyst_s": 0.4711, "cand_policy": 0.0, "assign_mode": 1.0}`; top-10 range 19.66-49.51

## Held-out synthetic-source stress test (FRESH seeds 303 and 404; mean of both; false%+missed%; real-slice bases with injected sources)

| Variant | v1 (v2.1) | v2 (v2.1) | v1 (v1.4) | v2 (v1.4) | B-code (v2.1) | B-paper (v2.1) |
|---|---|---|---|---|---|---|
| steady | 1.1 | 16.8 | 1.6 | 0.0 | 19.4 | 16.6 |
| jitter_s | 49.0 | 16.1 | 6.6 | 0.0 | 19.5 | 84.1 |
| jitter_m | 89.3 | 39.3 | 73.0 | 94.6 | 45.0 | 92.8 |
| drift | 6.8 | 17.6 | 3.5 | 0.0 | 51.7 | 44.8 |
| switch | 3.2 | 14.2 | 5.9 | 0.0 | 40.2 | 25.5 |
| walker | 64.8 | 56.1 | 65.0 | 69.0 | 68.1 | 69.9 |
| all variants | 35.7 | 26.7 | 25.9 | 27.2 | 40.7 | 55.6 |
| all except walker | 29.9 | 20.8 | 18.1 | 18.9 | 35.2 | 52.8 |
| tuned-family mean (steady, jitter_s, drift, switch) | 15.0 | 16.2 | 4.4 | 0.0 | 32.7 | 42.8 |

## Detection delay (splice test, report only)

| Set | Entry | window_s | delay_s | empty_fa_% | after_ok_% |
|---|---|---|---|---|---|
| v2.1 | ours | 5.08 | 5.3 | 0.0 | 65.2 |
| v2.1 | bpaper | n/a | 0.5 | 2.7 | 52.0 |
| v2.1 | bcode | n/a | 0.5 | 2.7 | 97.8 |
| v2.1 | ours_v2 | 2.07 | 14.5 | 0.0 | 53.3 |
| v1.4 | ours | 12.00 | 12.4 | 0.0 | 65.2 |
| v1.4 | bpaper | n/a | 0.0 | 2.7 | 71.4 |
| v1.4 | bcode | n/a | 0.5 | 2.7 | 96.9 |
| v1.4 | ours_v2 | 1.21 | 4.2 | 0.0 | 100.0 |
delay_s: seconds until the count reaches >= 1 for 5 s after a person appears; 'never' = not within 150 s. Ours window_s is the structural minimum for Ours-v1/v2.

Any FAIL above: paste its Note and the step name. Nothing here is frozen; test_* and the fresh synthetic test are untouched. Dev numbers are in-sample, the stress table is the first out-of-sample look.
