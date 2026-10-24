# latency_report.md (splice test; REPORT ONLY; fps 3.79; ambient step at the splice 0.25 C)

| Set | Entry | window_s | delay_s | empty_fa_% | after_ok_% |
|---|---|---|---|---|---|
| v1.2 | ours | 8.93 | 9.2 | 0.0 | 34.8 |
| v1.2 | bpaper | n/a | 0.0 | 2.7 | 52.4 |
| v1.2 | bcode | n/a | 4.7 | 2.7 | 98.7 |
| v1.2 | ours_v2 | 1.95 | 2.1 | 0.0 | 100.0 |
| v1.3 | ours | 12.00 | 12.4 | 0.0 | 65.2 |
| v1.3 | bpaper | n/a | 0.0 | 2.7 | 71.4 |
| v1.3 | bcode | n/a | 14.0 | 2.7 | 97.8 |
| v1.3 | ours_v2 | 1.60 | 14.0 | 0.0 | 100.0 |
| v1.4 | ours | 12.00 | 12.4 | 0.0 | 65.2 |
| v1.4 | bpaper | n/a | 0.0 | 2.7 | 71.4 |
| v1.4 | bcode | n/a | 0.5 | 2.7 | 96.9 |
| v1.4 | ours_v2 | 1.21 | 4.2 | 0.0 | 100.0 |

delay_s: seconds until the count reaches >= 1 for 5 s after a person appears; 'never' = not within 150 s. Ours window_s is the structural minimum for Ours-v1/v2.
