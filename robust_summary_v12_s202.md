# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 6.7 | 0.4 | 99.6 | 7.6 | 6.9 | 22.2 |
| jitter_s | 65.8 | 49.6 | 99.3 | 11.5 | 35.1 | 92.4 |
| jitter_m | 91.7 | 95.7 | 95.7 | 89.2 | 93.1 | 94.5 |
| drift | 7.9 | 0.4 | 99.5 | 7.6 | 90.9 | 48.1 |
| switch | 11.1 | 0.4 | 62.7 | 7.6 | 35.7 | 29.5 |
| walker | 67.2 | 96.9 | 96.9 | 71.8 | 97.0 | 74.1 |
| **all variants** | **41.7** | **40.6** | **92.3** | **32.5** | **59.8** | **60.1** |
| all except walker | 36.6 | 29.3 | 91.4 | 24.7 | 52.3 | 57.4 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 32.2 | 4.5 |
| Ours-v2 winner | 29.1 | 0.2 |
| v2 winner, policy 4 | 91.4 | 0.0 |
| v2 winner, policy 0 | 18.6 | 6.1 |
| B-code winner | 51.6 | 0.7 |
| B-paper winner | 54.6 | 2.7 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 35.8 | 28.5 | 8.9 |
| Ours-v2 winner | 29.3 | 28.8 | 0.5 |
| v2 winner, policy 4 | 91.9 | 90.8 | 0.0 |
| v2 winner, policy 0 | 19.4 | 17.7 | 12.3 |
| B-code winner | 53.5 | 49.7 | 1.5 |
| B-paper winner | 53.8 | 55.5 | 5.4 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
