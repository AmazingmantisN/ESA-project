# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.6 | 0.3 | 99.6 | 18.7 | 19.9 | 18.0 |
| jitter_s | 7.6 | 0.3 | 98.4 | 18.7 | 19.1 | 85.0 |
| jitter_m | 73.7 | 58.5 | 83.5 | 36.5 | 33.9 | 92.0 |
| drift | 4.0 | 0.3 | 98.8 | 18.7 | 46.3 | 44.9 |
| switch | 5.9 | 0.3 | 60.3 | 25.8 | 36.9 | 28.5 |
| walker | 58.1 | 75.7 | 75.7 | 64.3 | 60.4 | 65.6 |
| **all variants** | **25.2** | **22.6** | **86.1** | **30.5** | **36.1** | **55.7** |
| all except walker | 18.6 | 11.9 | 88.1 | 23.7 | 31.2 | 53.7 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 17.0 | 1.5 |
| Ours-v2 winner | 11.7 | 0.2 |
| v2 winner, policy 4 | 88.1 | 0.0 |
| v2 winner, policy 0 | 4.8 | 18.9 |
| B-code winner | 19.6 | 11.6 |
| B-paper winner | 50.8 | 2.9 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 18.5 | 15.5 | 3.1 |
| Ours-v2 winner | 9.0 | 14.5 | 0.4 |
| v2 winner, policy 4 | 91.0 | 85.2 | 0.0 |
| v2 winner, policy 0 | 5.3 | 4.3 | 37.8 |
| B-code winner | 23.6 | 15.6 | 23.1 |
| B-paper winner | 52.6 | 49.1 | 5.7 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
