# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.6 | 0.0 | 100.0 | 44.3 | 22.2 | 14.5 |
| jitter_s | 7.4 | 0.0 | 99.8 | 44.2 | 22.5 | 82.4 |
| jitter_m | 72.5 | 94.0 | 95.0 | 45.9 | 37.7 | 90.3 |
| drift | 3.9 | 0.0 | 100.0 | 43.9 | 35.0 | 44.6 |
| switch | 5.9 | 0.0 | 70.7 | 44.3 | 31.9 | 28.8 |
| walker | 67.3 | 59.8 | 60.3 | 52.8 | 63.3 | 59.9 |
| **all variants** | **26.4** | **25.6** | **87.6** | **45.9** | **35.4** | **53.4** |
| all except walker | 18.3 | 18.8 | 93.1 | 44.5 | 29.8 | 52.1 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 16.2 | 2.1 |
| Ours-v2 winner | 18.8 | 0.0 |
| v2 winner, policy 4 | 93.1 | 0.0 |
| v2 winner, policy 0 | 2.7 | 41.8 |
| B-code winner | 14.6 | 15.2 |
| B-paper winner | 48.7 | 3.4 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 17.3 | 15.0 | 4.2 |
| Ours-v2 winner | 19.2 | 18.4 | 0.0 |
| v2 winner, policy 4 | 93.4 | 92.8 | 0.0 |
| v2 winner, policy 0 | 5.0 | 0.4 | 83.6 |
| B-code winner | 18.2 | 11.0 | 30.4 |
| B-paper winner | 49.8 | 47.6 | 6.8 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
