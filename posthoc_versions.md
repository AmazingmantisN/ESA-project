# posthoc_versions.md - DECLARED POST-HOC (test_* was used first for frozen v1.4; this is descriptive, the frozen choice is not revisited)

streams: 10 from C:\VIT life\Project\thermal_poc\thermal_poc\data\streams\test_*.csv; error = false% + missed%, warm-up 30 s; 95 % = 20 s block bootstrap (2000); dev columns: original-10 sub-score (comparable across versions) and robustness-16 (v1.3/v1.4 only).

| Entry | Version | Test total % [95 % CI] | False % | Missed % | Dev orig-10 | Dev rob-16 |
|---|---|---|---|---|---|---|
| ours | v1.2 | 10.44 [7.25, 14.44] | 3.96 | 6.48 | 10.09 | - |
| ours | v1.3 | 18.22 [14.14, 22.60] | 5.06 | 13.16 | 16.30 | 4.29 |
| ours | v1.4 | 18.22 [14.14, 22.60] | 5.06 | 13.16 | 16.30 | 4.29 |
| ours_v2 | v1.2 | 11.00 [9.02, 13.00] | 8.06 | 2.94 | 1.87 | - |
| ours_v2 | v1.3 | 17.98 [12.81, 21.22] | 0.00 | 17.98 | 4.26 | 0.26 |
| ours_v2 | v1.4 | 3.94 [1.67, 5.07] | 0.00 | 3.94 | 1.67 | 0.00 |
| bcode | v1.2 | 12.18 [10.20, 15.51] | 12.16 | 0.02 | 12.77 | - |
| bcode | v1.3 | 29.31 [25.06, 31.82] | 7.35 | 21.96 | 21.60 | 30.51 |
| bcode | v1.4 | 37.29 [35.85, 39.33] | 6.28 | 31.01 | 25.10 | 25.15 |
| bpaper | v1.2 | 32.07 [28.86, 35.35] | 31.37 | 0.70 | 24.63 | - |
| bpaper | v1.3 | 32.18 [29.05, 35.00] | 29.97 | 2.20 | 24.86 | 48.37 |
| bpaper | v1.4 | 32.08 [28.91, 34.97] | 29.72 | 2.35 | 24.96 | 47.54 |

Paired difference, test total % (later version minus earlier; negative = later is better), 95 % block-bootstrap:

| Entry | Comparison | Diff [95 % CI] |
|---|---|---|
| ours | v1.3 - v1.2 | +7.78 [+4.12, +11.24] |
| ours | v1.4 - v1.3 | +0.00 [+0.00, +0.00] |
| ours_v2 | v1.3 - v1.2 | +6.99 [+1.73, +10.22] |
| ours_v2 | v1.4 - v1.3 | -14.05 [-17.63, -10.07] |
| bcode | v1.3 - v1.2 | +17.13 [+11.88, +19.63] |
| bcode | v1.4 - v1.3 | +7.98 [+6.69, +11.63] |
| bpaper | v1.3 - v1.2 | +0.11 [-2.08, +2.04] |
| bpaper | v1.4 - v1.3 | -0.10 [-0.70, +0.60] |

Reading: test_* is steady injected sources like dev original-10, so robustness-tuned versions (v1.3/v1.4) are expected to give up some accuracy there (R4, 'price of robustness'); the stress benefit is in robust_summary_v1x_s101/202.md.
