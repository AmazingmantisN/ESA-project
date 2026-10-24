# eval_suite.md (168 streams from C:\VIT life\Project\syn_stage1\syn_data; frozen params sha in params_frozen.json; no tuning)

## PRIMARY: strict error % (false + missed, all frames after 30 s)

| Scenario | ours | ours_v2 | bcode | bpaper | bcode_asis |
|---|---|---|---|---|---|
| A1 | 0.0 | 0.0 | 0.8 | 1.0 | 1.0 |
| A10 | 10.0 | 28.6 | 40.7 | 19.4 | 73.8 |
| A10_10Hz | 18.8 | 37.6 | 50.7 | 38.1 | 75.1 |
| A10_1Hz | 29.4 | 40.0 | 26.2 | 32.6 | 72.9 |
| A11 | 16.4 | 32.8 | 21.3 | 21.0 | 74.9 |
| A12 | 28.1 | 19.5 | 77.2 | 49.1 | 56.8 |
| A13 | 0.3 | 0.0 | 3.3 | 18.6 | 83.6 |
| A14 | 28.1 | 46.6 | 61.3 | 44.4 | 57.0 |
| A15 | 10.4 | 26.8 | 42.2 | 18.9 | 77.8 |
| A2 | 3.3 | 0.0 | 1.5 | 27.0 | 99.9 |
| A3 | 0.0 | 0.0 | 0.2 | 0.3 | 100.0 |
| A4 | 1.1 | 0.0 | 5.7 | 39.7 | 100.0 |
| A5 | 0.0 | 0.0 | 2.9 | 30.3 | 99.9 |
| A6 | 6.3 | 4.5 | 81.0 | 15.8 | 5.5 |
| A6_10Hz | 11.8 | 11.9 | 84.0 | 9.0 | 2.8 |
| A6_1Hz | 17.9 | 8.1 | 65.4 | 25.5 | 1.6 |
| A7 | 12.4 | 11.4 | 70.1 | 39.8 | 61.3 |
| A8 | 46.5 | 42.1 | 77.2 | 32.5 | 64.9 |
| A8_10Hz | 30.4 | 40.6 | 81.0 | 27.9 | 66.7 |
| A8_1Hz | 35.7 | 42.3 | 70.9 | 28.8 | 66.3 |
| A9 | 65.4 | 56.7 | 82.6 | 50.2 | 34.2 |
| G1 | 11.0 | 23.9 | 78.6 | 41.9 | 65.8 |
| U1 | 46.6 | 60.6 | 77.5 | 84.0 | 88.1 |
| U2 | 3.5 | 1.5 | 49.4 | 21.9 | 31.5 |
| U3 | 30.2 | 19.3 | 66.1 | 56.9 | 61.5 |
| U4 | 12.8 | 21.9 | 38.3 | 27.2 | 69.6 |
| U5 | 2.0 | 11.9 | 35.9 | 6.7 | 2.6 |
| U6 | 21.1 | 24.8 | 74.9 | 89.6 | 94.5 |
| MEAN (equal weight per scenario) | 17.8 | 21.9 | 48.8 | 32.1 | 60.3 |

## SECONDARY: error % excluding 15 s after each change in count

| Scenario | ours | ours_v2 | bcode | bpaper | bcode_asis |
|---|---|---|---|---|---|
| A1 | 0.0 | 0.0 | 0.8 | 1.0 | 1.0 |
| A10 | 4.8 | 25.8 | 41.9 | 17.7 | 72.3 |
| A10_10Hz | 17.9 | 35.2 | 51.9 | 36.9 | 75.2 |
| A10_1Hz | 27.4 | 38.0 | 27.6 | 31.3 | 72.6 |
| A11 | 13.5 | 31.5 | 17.6 | 18.5 | 77.5 |
| A12 | 28.1 | 19.5 | 77.2 | 49.1 | 56.8 |
| A13 | 0.3 | 0.0 | 3.3 | 18.6 | 83.6 |
| A14 | 23.3 | 44.0 | 59.8 | 42.6 | 57.3 |
| A15 | 5.2 | 27.3 | 43.2 | 17.0 | 81.3 |
| A2 | 3.3 | 0.0 | 1.5 | 27.0 | 99.9 |
| A3 | 0.0 | 0.0 | 0.2 | 0.3 | 100.0 |
| A4 | 1.1 | 0.0 | 5.7 | 39.7 | 100.0 |
| A5 | 0.0 | 0.0 | 2.9 | 30.3 | 99.9 |
| A6 | 6.3 | 4.5 | 81.0 | 15.8 | 5.5 |
| A6_10Hz | 11.8 | 11.9 | 84.0 | 9.0 | 2.8 |
| A6_1Hz | 17.9 | 8.1 | 65.4 | 25.5 | 1.6 |
| A7 | 12.4 | 11.4 | 70.1 | 39.8 | 61.3 |
| A8 | 46.5 | 42.1 | 77.2 | 32.5 | 64.9 |
| A8_10Hz | 30.4 | 40.6 | 81.0 | 27.9 | 66.7 |
| A8_1Hz | 35.7 | 42.3 | 70.9 | 28.8 | 66.3 |
| A9 | 65.4 | 56.7 | 82.6 | 50.2 | 34.2 |
| G1 | 11.0 | 23.9 | 78.6 | 41.9 | 65.8 |
| U1 | 46.6 | 60.6 | 77.5 | 84.0 | 88.1 |
| U2 | 3.5 | 1.5 | 49.4 | 21.9 | 31.5 |
| U3 | 30.2 | 19.3 | 66.1 | 56.9 | 61.5 |
| U4 | 12.8 | 21.9 | 38.3 | 27.2 | 69.6 |
| U5 | 2.0 | 11.9 | 35.9 | 6.7 | 2.6 |
| U6 | 21.1 | 24.8 | 74.9 | 89.6 | 94.5 |
| MEAN (equal weight per scenario) | 17.1 | 21.5 | 48.8 | 31.7 | 60.5 |

## DELAY: median seconds to reach the new count for 3 s (cap 60 s); n = events; never = not reached

| Scenario | kind | n | ours | ours_v2 | bcode | bpaper | bcode_asis |
|---|---|---|---|---|---|---|---|
| A10 | entry | 6 | 11.4 | 1.8 (2 never) | 0.0 | 0.0 | 0.0 |
| A10 | exit | 6 | 2.1 | 1.6 (3 never) | 2.4 (1 never) | 7.4 | - (6 never) |
| A10_10Hz | entry | 6 | 3.3 | 7.6 | 1.5 | 0.0 | 0.0 |
| A10_10Hz | exit | 6 | 2.5 | 2.3 (3 never) | 2.7 (1 never) | 9.5 | - (6 never) |
| A10_1Hz | entry | 6 | 18.5 | 14.0 (2 never) | 0.0 | 0.0 | 0.0 |
| A10_1Hz | exit | 6 | 1.5 | 1.5 (2 never) | 3.0 | 5.5 | 4.0 (5 never) |
| A11 | entry | 6 | 1.6 (1 never) | 0.8 (4 never) | 24.5 (4 never) | 0.0 | 0.0 |
| A11 | exit | 6 | 7.0 | 0.0 (1 never) | 3.7 | 9.9 | 22.6 (5 never) |
| A14 | entry | 6 | - (6 never) | 0.0 (5 never) | 21.7 (4 never) | 9.5 (3 never) | 0.0 (2 never) |
| A14 | exit | 6 | 0.0 | 0.0 | 0.9 | 2.0 | 2.0 (2 never) |
| A15 | entry | 6 | 11.6 | 0.8 | 0.0 | 0.0 | 0.0 |
| A15 | exit | 6 | 0.8 | 0.9 (2 never) | 4.5 (3 never) | 10.1 | - (6 never) |

Notes: scenario means weight every scenario equally; grace/strict use `humans` as truth; delay events come from changes of the `humans` column (cross-check with events.csv by hand).
Frozen methods = params_frozen.json (v1.4 winners). Reference rows: bcode_asis = the published baseline code with its published settings (tuned only for DHT offset/drift in our protocol).
