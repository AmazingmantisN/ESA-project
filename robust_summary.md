# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 6.9 | 0.4 | 99.6 | 7.6 | 7.2 | 15.6 |
| jitter_s | 66.7 | 74.7 | 99.1 | 31.2 | 49.4 | 92.6 |
| jitter_m | 92.6 | 96.5 | 96.5 | 89.4 | 94.3 | 94.8 |
| drift | 9.4 | 0.4 | 99.5 | 7.6 | 90.8 | 50.3 |
| switch | 11.1 | 0.4 | 62.7 | 7.6 | 35.8 | 25.4 |
| walker | 43.2 | 95.1 | 95.1 | 52.3 | 95.3 | 50.2 |
| **all variants** | **38.3** | **44.6** | **92.1** | **32.6** | **62.1** | **54.8** |
| all except walker | 37.4 | 34.5 | 91.5 | 28.7 | 55.5 | 55.7 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 32.7 | 4.6 |
| Ours-v2 winner | 34.2 | 0.3 |
| v2 winner, policy 4 | 91.5 | 0.0 |
| v2 winner, policy 0 | 22.5 | 6.1 |
| B-code winner | 54.8 | 0.7 |
| B-paper winner | 53.1 | 2.7 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 36.3 | 29.2 | 9.3 |
| Ours-v2 winner | 39.4 | 29.0 | 0.5 |
| v2 winner, policy 4 | 92.1 | 90.9 | 0.0 |
| v2 winner, policy 0 | 28.5 | 16.6 | 12.3 |
| B-code winner | 57.4 | 52.1 | 1.5 |
| B-paper winner | 52.9 | 53.3 | 5.3 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
