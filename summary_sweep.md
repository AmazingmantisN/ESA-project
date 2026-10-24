# summary.md (22 Oct 2026 05:28)

Python 3.13.5, 20 cores, Windows. Total 423 s.

Protocol v1.1 sha256 239ef348cfb68181... md 662c87f6619a9ac3... official_run=True jobs=18

## Checks

| Check | Result | Seconds | Note |
|---|---|---|---|
| build run_pc + test_modes (g++) | PASS | 5 |  |
| test_modes (expect 24 tests, 0 failed) | PASS | 1 | 24 tests, 0 failed |
| check_v1_equiv (v2 reproduces v1 exactly) | PASS | 104 | 510 comparisons (62 parameter sets), mismatches: 0 |
| make_real_streams (guard gap; expect test_empty 1152, test_single 918 frames) | PASS | 12 | test_empty 1152, test_single 918 |
| ESP32 firmware vs run_pc (needs --port COM7) | SKIPPED | 0 | not run |
| tune_sweep (protocol v1.1, dev only) | PASS | 301 |  |

## Tuning candidates (dev only, NOT frozen)

| Entry | Best total % | False % | Missed % | Worst stream % | Stage-1 best % | Untuned ref % | Won in stage | Edge params |
|---|---|---|---|---|---|---|---|---|
| ours | 10.09 | 5.53 | 4.56 | 39.6 | 14.20 | 10.61 | 2 | k |
| bpaper | 24.63 | 20.26 | 4.37 | 58.2 | 25.25 | 81.22 | 2 | none |
| bcode | 12.77 | 10.71 | 2.06 | 53.8 | 13.04 | 30.75 | 2 | none |
| bcode_asis | 79.25 | 79.25 | 0.00 | 100.0 | 79.25 | 82.97 | 1 | none |

- ours: `{"window_s": 8.9328, "drift": 0.4814, "contrast": 1.0356, "k": 0.0719, "smooth_s": 1.3, "maxmissed_s": 2.5}`; top-10 range 10.09-11.20
- bpaper: `{"timebase": "paper", "drift": 0.2823, "dht_offset": 0.1, "smooth_s": 0.0, "maxmissed_s": 0.5}`; top-10 range 24.63-24.86
- bcode: `{"npersist": 10.0, "drift": 0.1368, "dht_offset": 0.2, "smooth_s": 1.3, "maxmissed_s": 0.5}`; top-10 range 12.68-12.96
- bcode_asis: `{"npersist": 10.0, "drift": 0.548, "dht_offset": 0.1, "smooth_s": 0.0, "maxmissed_s": 0.5}`; top-10 range 79.25-79.25

Any FAIL above: paste the Note text and the failing step's name. Nothing here is frozen or tested on test_* streams.
