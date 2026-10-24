# esp32_check.md - frozen methods, link: ESP32 on COM7 @ 921600

params_frozen.json; streams dev_single_laptop_weak,dev_empty_heater,dev_single_clean; frames per stream all. Counts compared with run_pc frame by frame.

## Parity (mismatching frames, summed over streams; 0 = identical)

| Method | frames | raw | smooth | static | all OK |
|---|---|---|---|---|---|
| ours | 3442 | 0 | 0 | 0 | yes |
| ours_v2 | 3442 | 0 | 0 | 0 | yes |
| bcode | 3442 | 0 | 0 | 0 | yes |
| bpaper | 3442 | 0 | 0 | 0 | yes |
| bcode_asis | 3442 | 0 | 0 | 0 | yes |

## Time inside filt.process() per frame (microseconds; mean over frames, worst stream for p95/max)

| Method | mean | median | p95 | max | % of a 100 ms frame period (10 Hz) at p95 |
|---|---|---|---|---|---|
| ours | 4549 | 4559 | 4960 | 4990 | 4.96 |
| ours_v2 | 4679 | 4690 | 5008 | 5037 | 5.01 |
| bcode | 4643 | 4650 | 4935 | 5121 | 4.93 |
| bpaper | 5413 | 5416 | 5990 | 6314 | 5.99 |
| bcode_asis | 4707 | 4710 | 5049 | 5247 | 5.05 |

Memory (fill in from your machine): Arduino IDE 'Global variables use N bytes' = ____ ; sizeof_filter.exe table = ____ (8x8 filter object is ~41.6 KB on a 64-bit PC; 16x16 would be ~166 KB and is unlikely to fit as a static global on an ESP32).
Limits: timing covers filt.process() only (no parsing or serial); it is for the dev streams (few simultaneous blobs); worst-case frames with many blobs/tracks may take longer.
