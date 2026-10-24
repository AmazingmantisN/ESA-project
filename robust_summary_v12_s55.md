# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 6.7 | 0.4 | 99.6 | 7.6 | 6.9 | 17.1 |
| jitter_s | 64.2 | 98.3 | 99.2 | 20.1 | 37.4 | 93.1 |
| jitter_m | 92.9 | 96.4 | 96.4 | 89.2 | 93.0 | 94.7 |
| drift | 7.8 | 0.4 | 99.5 | 7.6 | 90.3 | 47.5 |
| switch | 11.1 | 0.4 | 62.8 | 7.6 | 35.7 | 28.2 |
| walker | 62.1 | 92.1 | 92.1 | 69.3 | 85.4 | 69.5 |
| **all variants** | **40.8** | **48.0** | **91.6** | **33.6** | **58.1** | **58.3** |
| all except walker | 36.5 | 39.2 | 91.5 | 26.4 | 52.7 | 56.1 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 32.1 | 4.4 |
| Ours-v2 winner | 38.9 | 0.2 |
| v2 winner, policy 4 | 91.5 | 0.0 |
| v2 winner, policy 0 | 20.3 | 6.1 |
| B-code winner | 52.1 | 0.6 |
| B-paper winner | 53.7 | 2.4 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 35.8 | 28.5 | 8.8 |
| Ours-v2 winner | 39.3 | 38.6 | 0.5 |
| v2 winner, policy 4 | 92.3 | 90.7 | 0.0 |
| v2 winner, policy 0 | 22.5 | 18.1 | 12.3 |
| B-code winner | 49.6 | 54.6 | 1.1 |
| B-paper winner | 54.3 | 53.0 | 4.8 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
