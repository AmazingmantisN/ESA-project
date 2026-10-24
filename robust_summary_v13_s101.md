# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.6 | 0.3 | 99.5 | 18.7 | 19.8 | 16.3 |
| jitter_s | 8.4 | 0.3 | 98.5 | 18.8 | 19.1 | 82.8 |
| jitter_m | 77.6 | 88.1 | 88.1 | 40.9 | 41.0 | 92.0 |
| drift | 2.4 | 0.3 | 98.9 | 18.7 | 46.8 | 44.8 |
| switch | 5.9 | 0.3 | 60.3 | 25.8 | 36.8 | 27.7 |
| walker | 40.0 | 73.0 | 75.6 | 33.8 | 72.0 | 47.4 |
| **all variants** | **22.7** | **27.0** | **86.8** | **26.1** | **39.3** | **51.8** |
| all except walker | 19.2 | 17.9 | 89.1 | 24.6 | 32.7 | 52.7 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 17.7 | 1.4 |
| Ours-v2 winner | 17.6 | 0.2 |
| v2 winner, policy 4 | 89.1 | 0.0 |
| v2 winner, policy 0 | 6.2 | 18.4 |
| B-code winner | 21.0 | 11.7 |
| B-paper winner | 49.7 | 3.0 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 19.3 | 16.2 | 2.9 |
| Ours-v2 winner | 17.3 | 17.9 | 0.5 |
| v2 winner, policy 4 | 89.4 | 88.8 | 0.0 |
| v2 winner, policy 0 | 8.3 | 4.2 | 36.7 |
| B-code winner | 25.6 | 16.3 | 23.5 |
| B-paper winner | 49.3 | 50.2 | 5.9 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
