# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 6.7 | 0.4 | 99.6 | 7.6 | 7.1 | 16.5 |
| jitter_s | 65.9 | 75.0 | 99.3 | 37.2 | 30.7 | 92.9 |
| jitter_m | 91.1 | 96.3 | 96.3 | 89.8 | 91.7 | 94.7 |
| drift | 10.5 | 0.4 | 99.5 | 7.6 | 90.1 | 45.0 |
| switch | 11.3 | 0.4 | 62.7 | 7.6 | 39.7 | 29.0 |
| walker | 47.4 | 84.1 | 84.1 | 52.6 | 79.6 | 49.3 |
| **all variants** | **38.8** | **42.8** | **90.2** | **33.8** | **56.5** | **54.6** |
| all except walker | 37.1 | 34.5 | 91.5 | 30.0 | 51.8 | 55.6 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 32.1 | 5.0 |
| Ours-v2 winner | 34.2 | 0.3 |
| v2 winner, policy 4 | 91.5 | 0.0 |
| v2 winner, policy 0 | 23.8 | 6.2 |
| B-code winner | 51.2 | 0.6 |
| B-paper winner | 53.0 | 2.6 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 35.3 | 28.9 | 9.9 |
| Ours-v2 winner | 39.2 | 29.1 | 0.6 |
| v2 winner, policy 4 | 91.9 | 91.1 | 0.0 |
| v2 winner, policy 0 | 29.3 | 18.3 | 12.3 |
| B-code winner | 50.5 | 51.9 | 1.2 |
| B-paper winner | 52.4 | 53.6 | 5.3 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
