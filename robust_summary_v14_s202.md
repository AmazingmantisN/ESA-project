# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.6 | 0.0 | 100.0 | 44.3 | 22.1 | 23.8 |
| jitter_s | 5.9 | 0.0 | 99.9 | 44.1 | 19.9 | 81.2 |
| jitter_m | 73.6 | 93.4 | 95.2 | 50.3 | 34.4 | 90.1 |
| drift | 3.9 | 0.0 | 100.0 | 43.7 | 34.2 | 45.7 |
| switch | 5.9 | 0.0 | 70.7 | 44.3 | 25.2 | 31.1 |
| walker | 55.0 | 95.1 | 95.1 | 55.4 | 74.5 | 69.3 |
| **all variants** | **24.3** | **31.4** | **93.5** | **47.0** | **35.0** | **56.9** |
| all except walker | 18.2 | 18.7 | 93.2 | 45.3 | 27.1 | 54.4 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 16.6 | 1.6 |
| Ours-v2 winner | 18.7 | 0.0 |
| v2 winner, policy 4 | 93.2 | 0.0 |
| v2 winner, policy 0 | 3.5 | 41.8 |
| B-code winner | 12.6 | 14.5 |
| B-paper winner | 50.9 | 3.5 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 17.2 | 16.0 | 3.2 |
| Ours-v2 winner | 19.1 | 18.2 | 0.0 |
| v2 winner, policy 4 | 93.3 | 93.1 | 0.0 |
| v2 winner, policy 0 | 6.4 | 0.6 | 83.7 |
| B-code winner | 15.3 | 10.0 | 29.0 |
| B-paper winner | 51.2 | 50.6 | 6.9 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
