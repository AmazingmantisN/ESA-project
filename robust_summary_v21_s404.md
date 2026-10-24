# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.1 | 16.6 | 86.6 | 16.6 | 19.5 | 16.7 |
| jitter_s | 48.1 | 16.3 | 83.3 | 16.3 | 20.4 | 85.1 |
| jitter_m | 87.8 | 36.9 | 68.8 | 36.9 | 47.2 | 93.0 |
| drift | 6.2 | 17.7 | 77.7 | 17.7 | 52.0 | 44.6 |
| switch | 3.2 | 14.3 | 50.5 | 14.3 | 40.2 | 26.2 |
| walker | 66.0 | 54.8 | 49.7 | 54.8 | 61.2 | 66.1 |
| **all variants** | **35.4** | **26.1** | **69.4** | **26.1** | **40.1** | **55.3** |
| all except walker | 29.3 | 20.4 | 73.4 | 20.4 | 35.9 | 53.1 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 28.4 | 0.9 |
| Ours-v2 winner | 5.5 | 14.8 |
| v2 winner, policy 4 | 70.7 | 2.7 |
| v2 winner, policy 0 | 5.5 | 14.8 |
| B-code winner | 24.2 | 11.7 |
| B-paper winner | 49.9 | 3.2 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 31.7 | 25.1 | 1.7 |
| Ours-v2 winner | 5.3 | 5.8 | 29.7 |
| v2 winner, policy 4 | 84.9 | 56.5 | 5.4 |
| v2 winner, policy 0 | 5.3 | 5.8 | 29.7 |
| B-code winner | 29.9 | 18.5 | 23.3 |
| B-paper winner | 49.4 | 50.5 | 6.4 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
