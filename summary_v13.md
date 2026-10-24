# summary_v13.md (23 Oct 2026 02:39)

Python 3.13.5, 20 cores, Windows. Total 501 s.

Protocol v1.3 json sha256 5b9e84f057b02de97bd4689330e32eda444452e4b3a8fc3360bae5f2bf23f913
md sha256 8705957aec4a4c2dd8ff41a54494f1bc7adc3c51f82e5a788ac8653acd98d59f
official_run=True jobs=18 dev streams=26

## Checks

| Check | Result | Seconds | Note |
|---|---|---|---|
| build run_pc + test_modes (g++) | PASS | 2 |  |
| test_modes (expect 35 tests, 0 failed) | PASS | 1 | 35 tests, 0 failed |
| tune_sweep protocol v1.3 (dev only) | PASS | 463 |  |
| check_v13_vs_v12 (original streams identical to v1.2) | PASS | 1 | ALL MATCH: v1.3 reproduces v1.2 on the original streams |
| robust_check held-out seed 44, v13 winners | PASS | 8 |  |
| robust_check held-out seed 55, v13 winners | PASS | 9 |  |
| robust_check held-out seed 44, v12 winners | PASS | 9 |  |
| robust_check held-out seed 55, v12 winners | PASS | 9 |  |

## v1.3 dev winners (NOT frozen). Error = false% + missed%, lower is better

| Entry | Total % (26 streams) | False | Missed | Worst stream | Original 10 | Robustness 16 | v1.2 winner on original 10 | Stage-1 best | Untuned ref | Edge params |
|---|---|---|---|---|---|---|---|---|---|---|
| ours | 8.91 | 3.90 | 5.01 | 72.7 | 16.30 | 4.29 | 10.09 | 10.23 | 20.97 | window_s |
| bpaper | 39.33 | 35.32 | 4.01 | 93.7 | 24.86 | 48.37 | 24.63 | 39.50 | 88.94 | drift |
| bcode | 27.08 | 13.22 | 13.86 | 54.7 | 21.60 | 30.51 | 12.77 | 27.77 | 56.24 | drift |
| bcode_asis | 87.74 | 87.74 | 0.00 | 100.0 | 79.25 | 93.05 | 79.25 | 87.74 | 89.92 | none |
| ours_v2 | 1.80 | 0.00 | 1.80 | 39.1 | 4.26 | 0.26 | 1.87 | 4.88 | 20.97 | window_s, persist_s |

Robustness-16 error by variant (v1.3 winner, dev):

| Entry | jitter_xs | jitter_s | drift | switch |
|---|---|---|---|---|
| ours | 1.6 | 6.3 | 3.3 | 5.9 |
| bpaper | 38.2 | 83.6 | 45.3 | 26.4 |
| bcode | 19.7 | 18.7 | 46.8 | 36.9 |
| bcode_asis | 100.0 | 100.0 | 100.0 | 72.2 |
| ours_v2 | 0.3 | 0.2 | 0.3 | 0.3 |

- ours: `{"window_s": 12.0, "drift": 0.6484, "contrast": 1.4182, "k": 0.1825, "smooth_s": 1.3, "maxmissed_s": 1.0}`; top-10 range 8.83-10.23
- bpaper: `{"timebase": "paper", "drift": 0.8, "dht_offset": 0.1, "smooth_s": 0.0, "maxmissed_s": 0.5}`; top-10 range 39.33-39.33
- bcode: `{"npersist": 10.0, "drift": 0.7286, "dht_offset": 0.2, "smooth_s": 1.3, "maxmissed_s": 0.5}`; top-10 range 27.08-27.60
- bcode_asis: `{"npersist": 10.0, "drift": 0.548, "dht_offset": 0.1, "smooth_s": 0.0, "maxmissed_s": 0.5}`; top-10 range 87.74-87.74
- ours_v2: `{"window_s": 1.6034, "drift": 1.2081, "contrast": 1.2682, "k": 0.9378, "smooth_s": 0.0, "maxmissed_s": 1.0, "persist_s": 27.9716, "hyst_s": 1.7963, "cand_policy": 2.0, "assign_mode": 0.0}`; top-10 range 1.72-3.55

## Held-out synthetic stress test (seeds 44 and 55, never used in tuning; mean of both seeds; false%+missed%)

| Variant | v1 v1.2 | v1 v1.3 | v2 v1.2 | v2 v1.3 | B-code v1.2 | B-code v1.3 | B-paper v1.2 | B-paper v1.3 |
|---|---|---|---|---|---|---|---|---|
| steady | 6.7 | 1.6 | 0.4 | 0.3 | 7.0 | 19.9 | 16.9 | 17.2 |
| jitter_s | 66.7 | 7.2 | 94.2 | 0.3 | 41.0 | 19.2 | 92.7 | 84.0 |
| jitter_m | 92.1 | 75.8 | 95.6 | 47.8 | 91.7 | 37.1 | 94.7 | 92.1 |
| drift | 8.2 | 3.9 | 0.4 | 0.3 | 90.5 | 46.7 | 46.5 | 45.0 |
| switch | 11.1 | 5.9 | 0.4 | 0.3 | 35.7 | 36.9 | 28.1 | 28.8 |
| walker | 62.2 | 55.8 | 86.3 | 76.2 | 83.0 | 66.3 | 70.0 | 66.2 |
| all variants | 41.1 | 25.0 | 46.2 | 20.9 | 58.2 | 37.7 | 58.1 | 55.5 |
| all except walker | 37.0 | 18.9 | 38.2 | 9.8 | 53.2 | 32.0 | 55.8 | 53.5 |

'all except walker' per seed (to see the seed-to-seed spread): v1.2 seed 44: v1 37.4, v2 37.2, B-code 53.7, B-paper 55.5; v1.2 seed 55: v1 36.5, v2 39.2, B-code 52.7, B-paper 56.1; v1.3 seed 44: v1 18.6, v2 11.9, B-code 31.2, B-paper 53.7; v1.3 seed 55: v1 19.2, v2 7.6, B-code 32.7, B-paper 53.2

Any FAIL above: paste its Note and the step name. jitter_m and walker are reported only (not tuned). Nothing here is frozen or tested on test_* streams.
