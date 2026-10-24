# summary_v14.md (23 Oct 2026 03:18)

Python 3.13.5, 20 cores, Windows. Total 512 s.

Protocol v1.4 json sha256 4d4b84b144950381e1c190e9919846e5f05ac1e9fb3a8efd02feb3cf45735153
md sha256 a5af0883a0c03c7812a3f01b2bf203e75753ce6852d6dcd2fc20de66cc944f70
official_run=True jobs=18 dev streams=26

## Checks

| Check | Result | Seconds | Note |
|---|---|---|---|
| build run_pc + test_modes (g++) | PASS | 2 |  |
| test_modes (expect 35 tests, 0 failed) | PASS | 1 | 35 tests, 0 failed |
| tune_sweep protocol v1.4 (dev only) | PASS | 453 |  |
| check_v14_rescore (v1.3 winners reproduce their v1.3 dev scores) | PASS | 6 | ALL MATCH: v1.4 tool reproduces the v1.3 winners' dev scores |
| latency_check (report only) | PASS | 1 |  |
| robust_check held-out seed 101, v1.4 winners | PASS | 8 |  |
| robust_check held-out seed 202, v1.4 winners | PASS | 8 |  |
| robust_check held-out seed 101, v1.3 winners | PASS | 8 |  |
| robust_check held-out seed 202, v1.3 winners | PASS | 8 |  |
| robust_check held-out seed 101, v1.2 winners | PASS | 8 |  |
| robust_check held-out seed 202, v1.2 winners | PASS | 8 |  |

## v1.4 dev winners (NOT frozen). Error = false% + missed%, lower is better

| Entry | Total % (26) | False | Missed | Worst stream | Original 10 | Robustness 16 | v1.3 winner: total / original 10 | Stage-1 best | Edge params |
|---|---|---|---|---|---|---|---|---|---|
| ours | 8.91 | 3.90 | 5.01 | 72.7 | 16.30 | 4.29 | 8.91 / 16.30 | 12.69 | window_s (operational limit, no widening) |
| bpaper | 38.85 | 34.47 | 4.38 | 93.7 | 24.96 | 47.54 | 39.33 / 24.86 | 39.36 | none |
| bcode | 25.13 | 7.83 | 17.30 | 70.3 | 25.10 | 25.15 | 27.08 / 21.60 | 27.35 | none |
| bcode_asis | 87.74 | 87.74 | 0.00 | 100.0 | 79.25 | 93.05 | 87.74 / 79.25 | 87.74 | none |
| ours_v2 | 0.64 | 0.00 | 0.64 | 16.1 | 1.67 | 0.00 | 1.80 / 4.26 | 5.03 | none |

Robustness-16 error by variant (v1.4 winner, dev):

| Entry | jitter_xs | jitter_s | drift | switch |
|---|---|---|---|---|
| ours | 1.6 | 6.3 | 3.3 | 5.9 |
| bpaper | 38.5 | 84.1 | 44.3 | 23.2 |
| bcode | 22.0 | 20.8 | 33.9 | 23.9 |
| bcode_asis | 100.0 | 100.0 | 100.0 | 72.2 |
| ours_v2 | 0.0 | 0.0 | 0.0 | 0.0 |

- ours: `{"window_s": 12.0, "drift": 0.6484, "contrast": 1.4182, "k": 0.1825, "smooth_s": 1.3, "maxmissed_s": 1.0}`; top-10 range 8.91-10.84
- bpaper: `{"timebase": "paper", "drift": 1.0077, "dht_offset": 0.1, "smooth_s": 0.0, "maxmissed_s": 0.5}`; top-10 range 38.80-39.30
- bcode: `{"npersist": 20.0, "drift": 0.9579, "dht_offset": 0.2, "smooth_s": 1.3, "maxmissed_s": 0.5}`; top-10 range 25.13-25.92
- bcode_asis: `{"npersist": 10.0, "drift": 1.2089, "dht_offset": 0.1, "smooth_s": 0.0, "maxmissed_s": 0.5}`; top-10 range 87.74-87.74
- ours_v2: `{"window_s": 1.213, "drift": 0.6421, "contrast": 1.2147, "k": 0.5686, "smooth_s": 1.3, "maxmissed_s": 1.0, "persist_s": 0.3971, "hyst_s": 1.899, "cand_policy": 2.0, "assign_mode": 0.0}`; top-10 range 0.64-3.94

## Held-out synthetic stress test (seeds 101 and 202, never used in tuning; mean of both seeds; false%+missed%)

| Variant | v1 v1.2 | v1 v1.3 | v1 v1.4 | v2 v1.2 | v2 v1.3 | v2 v1.4 | B-code v1.2 | B-code v1.3 | B-code v1.4 | B-paper v1.2 | B-paper v1.3 | B-paper v1.4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| steady | 6.7 | 1.6 | 1.6 | 0.4 | 0.3 | 0.0 | 7.0 | 19.8 | 22.1 | 19.4 | 19.9 | 20.2 |
| jitter_s | 65.8 | 7.2 | 7.2 | 62.3 | 0.2 | 0.0 | 32.9 | 18.9 | 20.1 | 92.7 | 82.4 | 81.5 |
| jitter_m | 91.4 | 75.6 | 75.6 | 96.0 | 62.1 | 94.2 | 92.4 | 40.1 | 36.3 | 94.6 | 92.0 | 90.3 |
| drift | 9.2 | 3.1 | 3.1 | 0.4 | 0.3 | 0.0 | 90.5 | 46.5 | 34.2 | 46.5 | 45.8 | 45.4 |
| switch | 11.2 | 5.9 | 5.9 | 0.4 | 0.3 | 0.0 | 37.7 | 36.8 | 25.9 | 29.2 | 29.2 | 28.7 |
| walker | 57.3 | 47.5 | 47.5 | 90.5 | 78.7 | 88.3 | 88.3 | 75.5 | 73.0 | 61.7 | 57.8 | 57.8 |
| all variants | 40.2 | 23.5 | 23.5 | 41.7 | 23.6 | 30.4 | 58.1 | 39.6 | 35.2 | 57.4 | 54.5 | 54.0 |
| all except walker | 36.9 | 18.7 | 18.7 | 31.9 | 12.6 | 18.9 | 52.0 | 32.5 | 27.7 | 56.5 | 53.9 | 53.2 |
| tuned-family mean (steady, jitter_s, drift, switch) | 23.2 | 4.5 | 4.5 | 15.9 | 0.3 | 0.0 | 42.0 | 30.5 | 25.6 | 47.0 | 44.3 | 44.0 |

'all except walker' per seed: v1.2 seed 101: v1 37.1, v2 34.5, B-code 51.8, B-paper 55.6; v1.2 seed 202: v1 36.6, v2 29.3, B-code 52.3, B-paper 57.4; v1.3 seed 101: v1 19.2, v2 17.9, B-code 32.7, B-paper 52.7; v1.3 seed 202: v1 18.2, v2 7.4, B-code 32.2, B-paper 55.0; v1.4 seed 101: v1 19.2, v2 19.0, B-code 28.3, B-paper 52.1; v1.4 seed 202: v1 18.2, v2 18.7, B-code 27.1, B-paper 54.4

## Detection delay (splice test, report only)

| Set | Entry | window_s | delay_s | empty_fa_% | after_ok_% |
|---|---|---|---|---|---|
| v1.2 | ours | 8.93 | 9.2 | 0.0 | 34.8 |
| v1.2 | bpaper | n/a | 0.0 | 2.7 | 52.4 |
| v1.2 | bcode | n/a | 4.7 | 2.7 | 98.7 |
| v1.2 | ours_v2 | 1.95 | 2.1 | 0.0 | 100.0 |
| v1.3 | ours | 12.00 | 12.4 | 0.0 | 65.2 |
| v1.3 | bpaper | n/a | 0.0 | 2.7 | 71.4 |
| v1.3 | bcode | n/a | 14.0 | 2.7 | 97.8 |
| v1.3 | ours_v2 | 1.60 | 14.0 | 0.0 | 100.0 |
| v1.4 | ours | 12.00 | 12.4 | 0.0 | 65.2 |
| v1.4 | bpaper | n/a | 0.0 | 2.7 | 71.4 |
| v1.4 | bcode | n/a | 0.5 | 2.7 | 96.9 |
| v1.4 | ours_v2 | 1.21 | 4.2 | 0.0 | 100.0 |
delay_s: seconds until the count reaches >= 1 for 5 s after a person appears; 'never' = not within 150 s. Ours window_s is the structural minimum for Ours-v1/v2.

Any FAIL above: paste its Note and the step name. jitter_m and walker are reported only. Nothing here is frozen or tested on test_* streams.
