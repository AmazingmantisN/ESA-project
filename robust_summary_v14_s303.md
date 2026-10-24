# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)

24 streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.

| Variant | Ours-v1 winner | Ours-v2 winner | v2 winner, policy 4 | v2 winner, policy 0 | B-code winner | B-paper winner |
|---|---|---|---|---|---|---|
| steady | 1.6 | 0.0 | 100.0 | 44.3 | 22.3 | 13.7 |
| jitter_s | 5.8 | 0.0 | 99.9 | 44.4 | 20.6 | 82.3 |
| jitter_m | 73.5 | 95.2 | 95.8 | 48.5 | 35.9 | 90.3 |
| drift | 3.0 | 0.0 | 100.0 | 43.7 | 35.0 | 46.2 |
| switch | 5.9 | 0.0 | 70.7 | 44.3 | 27.6 | 28.0 |
| walker | 62.7 | 78.3 | 78.6 | 50.4 | 74.3 | 69.2 |
| **all variants** | **25.4** | **28.9** | **90.8** | **45.9** | **36.0** | **55.0** |
| all except walker | 18.0 | 19.0 | 93.3 | 45.1 | 28.3 | 52.1 |

False-alarm % / missed % split (all except walker):

| Method | false % | missed % |
|---|---|---|
| Ours-v1 winner | 16.4 | 1.6 |
| Ours-v2 winner | 19.0 | 0.0 |
| v2 winner, policy 4 | 93.3 | 0.0 |
| v2 winner, policy 0 | 2.9 | 42.1 |
| B-code winner | 13.7 | 14.6 |
| B-paper winner | 48.5 | 3.7 |

By base (all except walker): empty room (every count is false) vs single person (false + missed):

| Method | empty: false % | single: false % | single: missed % |
|---|---|---|---|
| Ours-v1 winner | 17.3 | 15.5 | 3.2 |
| Ours-v2 winner | 19.1 | 19.0 | 0.0 |
| v2 winner, policy 4 | 93.3 | 93.3 | 0.0 |
| v2 winner, policy 0 | 5.2 | 0.7 | 84.2 |
| B-code winner | 16.7 | 10.7 | 29.2 |
| B-paper winner | 49.6 | 47.4 | 7.3 |

Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.
If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule.
