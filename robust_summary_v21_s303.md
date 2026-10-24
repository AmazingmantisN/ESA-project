# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.1 | 16.9 | 86.4 | 16.9 | 19.4 | 16.5 |
| jitter_s | 49.8 | 15.8 | 70.4 | 15.8 | 18.7 | 83.1 |
| jitter_m | 90.9 | 41.7 | 68.3 | 41.7 | 42.7 | 92.7 |
| drift | 7.3 | 17.5 | 80.3 | 17.5 | 51.4 | 45.0 |
| switch | 3.2 | 14.2 | 50.5 | 14.2 | 40.3 | 24.9 |
| walker | 63.7 | 57.4 | 64.2 | 57.4 | 75.0 | 73.7 |
| **all variants** | **36.0** | **27.3** | **70.0** | **27.3** | **41.3** | **56.0** |
| all except walker | 30.5 | 21.2 | 71.2 | 21.2 | 34.5 | 52.5 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 29.5 | 0.9 |
| Ours-v2 winner | 6.8 | 14.5 |
| v2 winner, policy 4 | 69.1 | 2.1 |
| v2 winner, policy 0 | 6.8 | 14.5 |
| B-code winner | 23.4 | 11.2 |
| B-paper winner | 49.1 | 3.3 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 31.2 | 27.8 | 1.8 |
| Ours-v2 winner | 7.1 | 6.4 | 28.9 |
| v2 winner, policy 4 | 83.3 | 54.9 | 4.2 |
| v2 winner, policy 0 | 7.1 | 6.4 | 28.9 |
| B-code winner | 27.9 | 18.8 | 22.3 |
| B-paper winner | 49.5 | 48.8 | 6.7 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
