# tradeoff.md - DECLARED POST-HOC, descriptive (existing results only)

Test = held-out test_* total % (steady injected sources). Stress = held-out synthetic robustness, seeds 101/202 mean: 'all except walker' and 'steady' rows. Lower is better on every column.

| Entry | Version | Test steady % [95 % CI] | Stress steady % | Stress all-except-walker % | Good on both (test<15 and stress<20)? |
|---|---|---|---|---|---|
| ours | v1.2 | 10.44 [7.25, 14.44] | 6.7 | 36.9 | no |
| ours | v1.3 | 18.22 [14.14, 22.60] | 1.6 | 18.7 | no |
| ours | v1.4 | 18.22 [14.14, 22.60] | 1.6 | 18.7 | no |
| ours_v2 | v1.2 | 11.00 [9.02, 13.00] | 0.4 | 31.9 | no |
| ours_v2 | v1.3 | 17.98 [12.81, 21.22] | 0.3 | 12.6 | no |
| ours_v2 | v1.4 | 3.94 [1.67, 5.07] | 0.0 | 18.9 | yes |
| bcode | v1.2 | 12.18 [10.20, 15.51] | 7.0 | 52.0 | no |
| bcode | v1.3 | 29.31 [25.06, 31.82] | 19.8 | 32.5 | no |
| bcode | v1.4 | 37.29 [35.85, 39.33] | 22.1 | 27.7 | no |
| bpaper | v1.2 | 32.07 [28.86, 35.35] | 19.4 | 56.5 | no |
| bpaper | v1.3 | 32.18 [29.05, 35.00] | 19.9 | 53.9 | no |
| bpaper | v1.4 | 32.08 [28.91, 34.97] | 20.2 | 53.2 | no |

Reading: a method that needs a different tuning round to be good on each axis (low on one, high on the other) has a real trade-off; one that is low on both in a single round does not.
Thresholds 15 / 20 are descriptive cut-offs chosen for the table, not pre-registered tests.
