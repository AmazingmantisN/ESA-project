# step5_results.md - baseline modes implemented (Plan Step 5)

Written 16 Oct 2026 (session 2). Everything below was run in the assistant's sandbox on the 4 recorded sessions rebuilt from your CSVs
(frames identical to the ones you converted). **Not yet run on your machine or your ESP32.** DEV streams only; no test_* stream was touched.

## What was built (code v2)
- `persistence_filter.h`: `persistence_mode` 0 EXTENT (ours) / 1 ENDPOINT_COUNTER (B-paper, their main.py) / 2 BIRTH_ENDPOINT (B-code, firmware);
  `threshold_mode` 0 ROBUST / 1 DHT (>= dht + offset) / 2 MEANSTD; plus plain-mean centroid, Manhattan matching, 8-connectivity,
  lock/reset logic, `count_static` (firmware as published), runtime track/blob limits. `process(raw, dht)`. No dynamic allocation.
- `run_pc.cpp`: all flags, `--preset bpaper|bcode|bcode_asis`, `--timebase frames|paper|loop`, `--npersist(_s)`, `--print_pline`, optional `dht` stream column, `static` output column.
- `thermal_poc.ino`: extended `P` line (superset of v1), `D` frame command carrying the DHT, reply gets a 6th field (static count).
- `stream_to_esp32.py`: passes any flag through run_pc, so ESP32 and PC always get identical settings.
- `load_dataset.py` saves `<out>_dht.npy` (dropouts forward-filled) and `_dhtraw.npy`; `make_stream.py` writes the `dht` column.
- Checks: `test_modes.cpp` (24 tests), `check_v1_equiv.py`, `check_firmware_protocol.py`, `baseline_preview.py`.

## Defaults you approved
Time base for B-paper: all three (frames 100/15 = 26 s/4 s, paper 10 s/1.5 s, loop 13 s/2 s). B-code: intended behaviour AND as-published (`bcode_asis`). DHT offset: +0.1 and +0.2.

## Verification (sandbox)
| Check | Result |
|---|---|
| v2 defaults vs v1, frame for frame (raw + smooth), 22 streams x 62 parameter sets | **510 comparisons, 0 mismatches** |
| Unit tests (lock timing, moving blob, oscillation, noisy blob, DHT >=, firmware as published, birth-position rule, reset, 8-conn) | **24 / 24 pass** |
| Firmware protocol (software stand-in for the ESP32) vs run_pc, 9 parameter sets, real frames with DHT | **0 mismatches** (real ESP32 not yet run) |

## Findings (synthetic tests + untuned DEV preview; hypotheses, not results)
1. **Their endpoint+counter rule vs sensor noise.** For a strong static blob the endpoint distance of the centroid is roughly half the pixel noise (degC) in pixels.
   Synthetic white noise 0.10 degC: 54% of frames under 0.05 px, longest unbroken run 9 frames; 0.15 degC: run 6. A counter needing 20 to 100 in a row cannot fill.
2. **On the real stream the same happens.** B-paper with the spec value (0.05 px) never locked an injected, perfectly static laptop (0 frames). At 0.1 px it locked at 116 s; at 0.2 px and above at 29 s.
   So B-paper is not broken, it is threshold-versus-noise. This supports the Step 6/8 hypothesis, **but only for this injected source and these assumptions.**
3. **B-code (firmware rule) locks static sources within 5 to 10 s** (it compares with the birth position once the path is 20 long) and also locks the seated person in 3.9% of clean dev frames (missed 3.7% under "intended").
4. **Oscillation fools the endpoint rule, not extent** (unit test T3), and **B-code flags a moving blob that returns to its start** (T7). Both are by construction; whether they occur in real data is a Step 8 question.
5. Untuned B-paper false alarms with a static source present: 100% at the spec threshold (never masks); B-code intended 0.7 to 19%; B-code as published 100% (it counts static tracks).

## FIDELITY GAP (open, must be resolved or disclosed)
Our B-paper on the empty room (dev slice 0-320 s): **0 to 1.5% false alarms** (min blob area 1 to 40). **Their logged output on the same slice: 10.0%.** Not explained by the assumed minimum blob area.
Candidates: their blob filtering/min area, DHT handling (D7), a different code version (D8), or logging artefacts. Until closed, say "reimplementation per the paper and code description", not "reproduction".

## Assumptions made (not in baseline_spec.md)
A1 minimum blob area for baselines = ours (40 cells). A2 max_missed 1 (B-paper: 3 loop passes ~ 1.5 frames) and 2 (B-code). A3 B-paper judges every live track every frame (as their loop does). A4 B-paper N_window uses the oldest of the last N_window positions.
A5 B-code birth-position reset at row 3.5 crossing does not reset the path length. A6 B-paper smoothing off (smooth 1). A7 DHT used as recorded with dropouts forward-filled; `--dht-raw` reproduces their start-up artefact.

## What to do on your machine
Copy the zip over the project (xcopy /E /Y), rebuild `run_pc.exe` and `test_modes.exe`, rebuild streams (commands in README, v2 section), run `check_v1_equiv.py`, re-flash the ESP32, run `check_firmware_protocol.py --port COM7 ...`. Send back: test_modes summary line, check_v1 line, the 9 OK lines.
