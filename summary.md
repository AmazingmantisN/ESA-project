# summary.md (23 Oct 2026 01:53)

Python 3.13.5, 20 cores, Windows. Total 502 s.

Protocol v1.2 sha256 5b58cb8defc2e5e9... md 280b092c04525b8c... official_run=True jobs=18

## Checks

| Check | Result | Seconds | Note |
|---|---|---|---|
| build run_pc + test_modes (g++) | PASS | 4 |  |
| test_modes (expect 35 tests, 0 failed) | PASS | 2 | 35 tests, 0 failed |
| check_v1_equiv (v2 reproduces v1 exactly) | PASS | 81 | 510 comparisons (62 parameter sets), mismatches: 0 |
| check_v2_nested (v2 defaults == v1; length of nested equivalence) | PASS | 35 | nested (mode 3 defaults == mode 0): 210 comparisons, mismatches: 0 |
| make_real_streams (guard gap; expect test_empty 1152, test_single 918 frames) | PASS | 11 | test_empty 1152, test_single 918 |
| ESP32 firmware vs run_pc on COM7 | PASS | 126 | OK   Ours-v2 policy 4 + global assign                   frames 600  mismatches raw/smooth/static: 0/0/0 | OK   Ours-v2 origin gate                                frames 600  mismatches raw/smooth/stat |
| tune_sweep (protocol v1.2, dev only) | PASS | 242 |  |

## Tuning candidates (dev only, NOT frozen)

| Entry | Best total % | False % | Missed % | Worst stream % | Stage-1 best % | Untuned ref % | Won in stage | Edge params |
|---|---|---|---|---|---|---|---|---|
| ours | 10.09 | 5.53 | 4.56 | 39.6 | 14.20 | 10.61 | 2 | k (natural bound, no widening) |
| bpaper | 24.63 | 20.26 | 4.37 | 58.2 | 25.25 | 81.22 | 2 | none |
| bcode | 12.77 | 10.71 | 2.06 | 53.8 | 13.04 | 30.75 | 2 | none |
| bcode_asis | 79.25 | 79.25 | 0.00 | 100.0 | 79.25 | 82.97 | 1 | none |
| ours_v2 | 1.87 | 0.27 | 1.60 | 15.2 | 9.21 | 10.61 | 2 | none |

- ours: `{"window_s": 8.9328, "drift": 0.4814, "contrast": 1.0356, "k": 0.0719, "smooth_s": 1.3, "maxmissed_s": 2.5}`; top-10 range 10.09-11.20
- bpaper: `{"timebase": "paper", "drift": 0.2823, "dht_offset": 0.1, "smooth_s": 0.0, "maxmissed_s": 0.5}`; top-10 range 24.63-24.86
- bcode: `{"npersist": 10.0, "drift": 0.1368, "dht_offset": 0.2, "smooth_s": 1.3, "maxmissed_s": 0.5}`; top-10 range 12.68-12.96
- bcode_asis: `{"npersist": 10.0, "drift": 0.548, "dht_offset": 0.1, "smooth_s": 0.0, "maxmissed_s": 0.5}`; top-10 range 79.25-79.25
- ours_v2: `{"window_s": 1.9461, "drift": 0.4552, "contrast": 1.1208, "k": 0.1754, "smooth_s": 0.0, "maxmissed_s": 2.5, "persist_s": 21.3485, "hyst_s": 2.9566, "cand_policy": 2.0, "assign_mode": 1.0}`; top-10 range 1.87-6.08

Any FAIL above: paste the Note text and the failing step's name. Nothing here is frozen or tested on test_* streams.
