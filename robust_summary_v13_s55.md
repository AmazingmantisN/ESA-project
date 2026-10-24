# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.6 | 0.3 | 99.6 | 18.7 | 20.0 | 16.5 |
| jitter_s | 6.7 | 0.3 | 95.8 | 15.9 | 19.3 | 82.9 |
| jitter_m | 78.0 | 37.0 | 86.8 | 31.1 | 40.4 | 92.2 |
| drift | 3.8 | 0.3 | 98.8 | 18.7 | 47.1 | 45.1 |
| switch | 5.9 | 0.3 | 60.3 | 25.8 | 36.9 | 29.1 |
| walker | 53.4 | 76.6 | 80.4 | 54.4 | 72.3 | 66.8 |
| **all variants** | **24.9** | **19.1** | **87.0** | **27.4** | **39.3** | **55.4** |
| all except walker | 19.2 | 7.6 | 88.3 | 22.0 | 32.7 | 53.2 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 17.4 | 1.8 |
| Ours-v2 winner | 7.3 | 0.3 |
| v2 winner, policy 4 | 88.2 | 0.1 |
| v2 winner, policy 0 | 4.4 | 17.6 |
| B-code winner | 21.7 | 11.1 |
| B-paper winner | 50.2 | 2.9 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 18.8 | 16.0 | 3.6 |
| Ours-v2 winner | 9.0 | 5.6 | 0.7 |
| v2 winner, policy 4 | 91.0 | 85.3 | 0.2 |
| v2 winner, policy 0 | 5.0 | 3.8 | 35.3 |
| B-code winner | 24.4 | 18.9 | 22.2 |
| B-paper winner | 51.4 | 49.1 | 5.9 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
