# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.6 | 0.0 | 100.0 | 44.3 | 22.1 | 16.7 |
| jitter_s | 8.4 | 0.0 | 99.9 | 44.0 | 20.3 | 81.8 |
| jitter_m | 77.6 | 95.1 | 96.2 | 51.9 | 38.3 | 90.6 |
| drift | 2.4 | 0.0 | 100.0 | 43.7 | 34.1 | 45.1 |
| switch | 5.9 | 0.0 | 70.7 | 44.3 | 26.7 | 26.3 |
| walker | 40.0 | 81.5 | 83.0 | 39.1 | 71.4 | 46.3 |
| **all variants** | **22.7** | **29.4** | **91.6** | **44.6** | **35.5** | **51.1** |
| all except walker | 19.2 | 19.0 | 93.4 | 45.7 | 28.3 | 52.1 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 17.7 | 1.4 |
| Ours-v2 winner | 19.0 | 0.0 |
| v2 winner, policy 4 | 93.4 | 0.0 |
| v2 winner, policy 0 | 3.6 | 42.1 |
| B-code winner | 13.9 | 14.4 |
| B-paper winner | 48.6 | 3.5 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 19.3 | 16.2 | 2.9 |
| Ours-v2 winner | 19.0 | 19.1 | 0.0 |
| v2 winner, policy 4 | 93.4 | 93.4 | 0.0 |
| v2 winner, policy 0 | 6.5 | 0.7 | 84.2 |
| B-code winner | 16.2 | 11.6 | 28.8 |
| B-paper winner | 48.7 | 48.5 | 7.0 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
