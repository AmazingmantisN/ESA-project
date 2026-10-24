# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 6.7 | 0.4 | 99.6 | 7.6 | 7.1 | 16.6 |
| jitter_s | 69.2 | 90.1 | 99.3 | 17.6 | 44.7 | 92.3 |
| jitter_m | 91.2 | 94.8 | 94.8 | 88.1 | 90.4 | 94.7 |
| drift | 8.5 | 0.4 | 99.6 | 7.6 | 90.7 | 45.5 |
| switch | 11.1 | 0.4 | 62.7 | 7.6 | 35.6 | 28.1 |
| walker | 62.4 | 80.5 | 80.5 | 64.7 | 80.6 | 70.5 |
| **all variants** | **41.5** | **44.4** | **89.4** | **32.2** | **58.2** | **58.0** |
| all except walker | 37.4 | 37.2 | 91.2 | 25.7 | 53.7 | 55.5 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 32.4 | 4.9 |
| Ours-v2 winner | 37.0 | 0.2 |
| v2 winner, policy 4 | 91.2 | 0.0 |
| v2 winner, policy 0 | 20.8 | 4.9 |
| B-code winner | 53.1 | 0.6 |
| B-paper winner | 53.0 | 2.5 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 35.7 | 29.1 | 9.8 |
| Ours-v2 winner | 39.7 | 34.3 | 0.5 |
| v2 winner, policy 4 | 92.3 | 90.1 | 0.0 |
| v2 winner, policy 0 | 24.0 | 17.5 | 9.8 |
| B-code winner | 49.8 | 56.4 | 1.2 |
| B-paper winner | 53.9 | 52.1 | 5.0 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
