# latency_report.md (splice test; REPORT ONLY; fps 3.79; ambient step at the splice 0.25 C)

| Set | Entry | window_s | delay_s | empty_fa_% | after_ok_% |
|---|---|---|---|---|---|
| v2.1 | ours | 5.08 | 5.3 | 0.0 | 65.2 |
| v2.1 | bpaper | n/a | 0.5 | 2.7 | 52.0 |
| v2.1 | bcode | n/a | 0.5 | 2.7 | 97.8 |
| v2.1 | ours_v2 | 2.07 | 14.5 | 0.0 | 53.3 |
| v1.4 | ours | 12.00 | 12.4 | 0.0 | 65.2 |
| v1.4 | bpaper | n/a | 0.0 | 2.7 | 71.4 |
| v1.4 | bcode | n/a | 0.5 | 2.7 | 96.9 |
| v1.4 | ours_v2 | 1.21 | 4.2 | 0.0 | 100.0 |

delay_s: seconds until the count reaches >= 1 for 5 s after a person appears; 'never' = not within 150 s. Ours window_s is the structural minimum for Ours-v1/v2.
