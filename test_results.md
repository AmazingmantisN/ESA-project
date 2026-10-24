# test_results.md - HELD-OUT TEST RUN (one shot) (23 Oct 2026 03:32)

params_frozen.json sha256 01f4fcc86280113322153be7db37ef724b6b6246b3eff129a695503fd3d30297; protocol v1.4 json 4d4b84b144950381...; 10 streams; warm-up 30 s; error = false% + missed%; 95 % interval = 20 s moving-block bootstrap (2000).

| Method | Total % [95 % CI] | False % | Missed % | Dev total (26 streams) | Dev original-10 |
|---|---|---|---|---|---|
| ours | 18.22 [14.16, 22.65] | 5.06 | 13.16 | 8.91 | 16.30 |
| ours_v2 | 3.94 [1.73, 5.19] | 0.00 | 3.94 | 0.64 | 1.67 |
| bcode | 37.29 [35.87, 39.29] | 6.28 | 31.01 | 25.13 | 25.10 |
| bpaper | 32.08 [28.79, 35.16] | 29.72 | 2.35 | 38.85 | 24.96 |
| bcode_asis (as published, tuned) | 83.30 [82.41, 84.27] | 83.30 | 0.00 | 87.74 | 79.25 |
| ours (untuned reference) | 9.66 [6.70, 12.95] | 5.55 | 4.11 | - | - |
| ours_v2 (untuned reference) | 9.66 [6.70, 12.95] | 5.55 | 4.11 | - | - |
| bcode (untuned reference) | 23.53 [21.52, 27.13] | 23.21 | 0.32 | - | - |
| bpaper (untuned reference) | 82.36 [81.56, 83.37] | 82.36 | 0.00 | - | - |

Error % by source variant (mean of the empty-room and single-person stream):

| Method | clean | laptop_weak | laptop | heater_weak | heater | empty room | single person |
|---|---|---|---|---|---|---|---|
| ours | 2.2 | 8.5 | 10.0 | 35.0 | 35.4 | 5.2 | 31.3 |
| ours_v2 | 0.7 | 1.2 | 1.7 | 4.3 | 11.8 | 0.0 | 7.9 |
| bcode | 37.9 | 37.6 | 38.0 | 36.2 | 36.8 | 0.7 | 73.9 |
| bpaper | 18.5 | 38.2 | 19.0 | 56.7 | 28.0 | 15.0 | 49.1 |
| bcode_asis (as published, tuned) | 16.5 | 100.0 | 100.0 | 100.0 | 100.0 | 80.1 | 86.5 |
| ours (untuned reference) | 4.4 | 3.3 | 4.4 | 27.9 | 8.3 | 4.0 | 15.3 |
| ours_v2 (untuned reference) | 4.4 | 3.3 | 4.4 | 27.9 | 8.3 | 4.0 | 15.3 |
| bcode (untuned reference) | 16.4 | 18.1 | 16.4 | 45.7 | 21.0 | 14.8 | 32.2 |
| bpaper (untuned reference) | 12.2 | 100.0 | 100.0 | 100.0 | 99.6 | 81.1 | 83.6 |

Paired differences, total % (negative = first is better), 95 % block-bootstrap interval:

| Comparison | Difference [95 % CI] |
|---|---|
| ours_v2 - ours | -14.28 [-19.05, -11.02] |
| ours_v2 - bcode | -33.35 [-37.10, -31.37] |
| ours_v2 - bpaper | -28.14 [-31.89, -25.50] |
| ours - bpaper | -13.86 [-17.84, -9.24] |
| ours - bcode | -19.07 [-24.29, -14.34] |

Error % per stream (total):

| Method | empty_clean | empty_heater | empty_heater_weak | empty_laptop | empty_laptop_weak | single_clean | single_heater | single_heater_weak | single_laptop | single_laptop_weak |
|---|---|---|---|---|---|---|---|---|---|---|
| ours | 0.0 | 0.0 | 25.9 | 0.0 | 0.0 | 4.4 | 70.7 | 44.1 | 20.0 | 17.1 |
| ours_v2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.4 | 23.7 | 8.6 | 3.4 | 2.4 |
| bcode | 0.6 | 0.6 | 1.0 | 0.6 | 0.6 | 75.2 | 73.0 | 71.5 | 75.3 | 74.6 |
| bpaper | 0.6 | 0.6 | 41.4 | 0.6 | 31.9 | 36.4 | 55.4 | 72.0 | 37.5 | 44.5 |
| bcode_asis (as published, tuned) | 0.6 | 100.0 | 100.0 | 100.0 | 100.0 | 32.4 | 100.0 | 100.0 | 100.0 | 100.0 |
| ours (untuned reference) | 0.0 | 0.0 | 20.1 | 0.0 | 0.0 | 8.7 | 16.7 | 35.6 | 8.8 | 6.6 |
| ours_v2 (untuned reference) | 0.0 | 0.0 | 20.1 | 0.0 | 0.0 | 8.7 | 16.7 | 35.6 | 8.8 | 6.6 |
| bcode (untuned reference) | 8.4 | 8.4 | 38.9 | 8.4 | 10.0 | 24.4 | 33.6 | 52.6 | 24.4 | 26.2 |
| bpaper (untuned reference) | 5.7 | 100.0 | 100.0 | 100.0 | 100.0 | 18.7 | 99.3 | 100.0 | 100.0 | 100.0 |

Reading: test_* starts 20 s after the dev slices end, same session and room, so this is a held-out time window, not a new room or person. Sources are the same steady injected laptops/heaters as dev.
Uncertainty is from temporal blocks of two real slices only; it does not include room-to-room or person-to-person variation.
