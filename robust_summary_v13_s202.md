# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.6 | 0.3 | 99.6 | 18.7 | 19.8 | 23.4 |
| jitter_s | 5.9 | 0.2 | 98.5 | 15.9 | 18.6 | 82.0 |
| jitter_m | 73.6 | 36.1 | 85.7 | 43.6 | 39.3 | 92.0 |
| drift | 3.9 | 0.3 | 98.8 | 18.7 | 46.3 | 46.9 |
| switch | 5.9 | 0.3 | 60.4 | 25.8 | 36.9 | 30.8 |
| walker | 55.0 | 84.3 | 87.1 | 64.5 | 79.1 | 68.1 |
| **all variants** | **24.3** | **20.2** | **88.3** | **31.2** | **40.0** | **57.2** |
| all except walker | 18.2 | 7.4 | 88.6 | 24.5 | 32.2 | 55.0 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 16.6 | 1.6 |
| Ours-v2 winner | 7.0 | 0.4 |
| v2 winner, policy 4 | 88.4 | 0.2 |
| v2 winner, policy 0 | 6.5 | 18.0 |
| B-code winner | 20.8 | 11.4 |
| B-paper winner | 52.0 | 3.0 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 17.2 | 16.0 | 3.2 |
| Ours-v2 winner | 7.3 | 6.8 | 0.8 |
| v2 winner, policy 4 | 89.4 | 87.4 | 0.3 |
| v2 winner, policy 0 | 7.3 | 5.7 | 36.1 |
| B-code winner | 26.1 | 15.4 | 22.8 |
| B-paper winner | 51.5 | 52.5 | 6.1 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
