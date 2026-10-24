# dataset_notes.md — Papanashi et al. study-pod recordings (Plan Step 2 output)

Written 16 Oct 2026. Every number below was recomputed directly from the CSVs
(`papanashi_csvs/<session>/csv_data/`) and cross-checked against the `*.meta.json` files
produced by `load_dataset.py` on the project machine. They agree.

Source: github.com/kernelops/thermal-occupancy-monitor, commit `5d7fe8a2432659845f41b1bbb0b5ebd2a7c29d2c`
(15 Jun 2026). IEEE DataPort copy (DOI 10.21227/0pwe-g126) not checked for extra sessions.
**No LICENSE in the repo: do not copy their code or redistribute their CSVs. Reimplement from the paper, cite, link the DOI.**

## 1. Layout

    dataset/{0 persons, 1 person -Trial_1, 1 person - Trial_2, 2 persons}/csv_data/{data.csv, esp32_raw_data.csv}

Folder names have inconsistent spacing (`1 person -Trial_1` vs `1 person - Trial_2`). Quote the paths.
All recordings are from 27 May 2025 (2-person session: 19:15 to 19:34).

## 2. Schemas

| File | Columns | Use |
|---|---|---|
| `esp32_raw_data.csv` | `timestamp, gridEye, dht_temperature` | **Our frame source.** Raw, unlabelled. |
| `data.csv` | `record_id, timestamp, dht_temperature, gridEye_array, current_people_count, net_crossing_count, current_objects_count` | Their logged algorithm output only. |

- `gridEye` / `gridEye_array`: text list of 64 floats, row-major 8x8, parse with `ast.literal_eval`. Timestamps are ISO.
- `current_people_count`, `net_crossing_count`, `current_objects_count` are **their algorithm's output, never ground truth.**
  Ground truth for people = the session label (0 / 1 / 2), with the caveats in section 6.

## 3. Sessions (esp32_raw_data.csv)

| Session | Raw frames | Duration | Unique fps | Gaps >3x median dt | Temp min / max / median (C) | DHT values |
|---|---|---|---|---|---|---|
| 0 persons | 2,445 | 639.6 s | 3.88 | 1 (2.3 s at 29 s) | 26.00 / 29.00 / 27.50 | 28.7 |
| 1 person Trial_1 | 2,553 | 692.1 s | 3.80 | 5 (0.85 to 1.4 s, all near 675 to 680 s) | 25.25 / 31.25 / 27.75 | 28.7, 29.1, and 0.1 (32 rows) |
| 1 person Trial_2 | 273 | 71.4 s | 3.89 | 0 | 25.75 / 29.25 / 27.00 | 28.4 |
| 2 persons | 3,579 | 1,087.5 s | 3.73 | **86** (up to ~3 s, mostly mid-session) | 25.25 / 32.00 / 28.25 | 28.4 to 29.2, and -0.2 (32 rows) |

All timestamps strictly increase. No exact repeated frames in the raw files. All temperatures are room-plausible (25 to 32 C).

## 4. Quirks that affect the pipeline

1. **Real frame rate is ~3.8 Hz (3.73 to 3.89), not 10 fps.** The Master Plan assumed 10 fps; every frame-count parameter in it is wrong by ~2.6x.
   Window 30 frames = ~8 s, not 3 s. Their N_persist = 100 = ~26 s of raw frames. **All time parameters are defined in seconds and converted using the measured fps.**
2. **`data.csv` logs ~2x the raw rows and about half are exact repeats of the previous frame**
   (0 persons: 2,209 of 4,648; Trial_1: 2,685 of 5,237; Trial_2: 288 of 560; 2 persons: 4,747 of 8,325).
   After removing repeats, `data.csv` has exactly as many unique frames as the raw file (e.g. 3,579 for 2 persons). Cause unknown (their ESP32 loop or the processing loop; check in Step 3).
3. **All-zero grids exist only in `data.csv`** (0 persons: 2, Trial_1: 60, Trial_2: 5, 2 persons: 0). The raw files have none. (An earlier log said the raw files had them. That was wrong.)
4. **Bad DHT readings** in the raw files: 32 consecutive rows at 0.1 C (Trial_1) and 32 at -0.2 C (2 persons). Their grids are valid. The loader keeps them by default (our filter does not use DHT); `--drop-dht-dropouts` removes them. **The DHT-based baseline (Step 5) must handle this.**
5. **DHT is nearly constant within a session** (1 to 5 distinct values in 28.4 to 29.2 C).
6. **Timing gaps matter.** Persistence windows span real time, so the 2-person session (86 gaps) is only exploratory. Trial_1's gaps are all in the last ~20 s.

## 5. Signal strength (frame max minus frame median)

| Session | median | p95 | max |
|---|---|---|---|
| 0 persons | 0.75 C | 1.00 C | 1.50 C |
| 1 person Trial_1 | 2.25 C | 2.75 C | 3.25 C |
| 1 person Trial_2 | 1.00 C | 1.67 C | 2.00 C |
| 2 persons | 2.25 C | 3.00 C | 3.75 C |

- A person is only ~+2.3 C above the frame median. The old default `min_contrast` of 2.5 C sits above this, which is why it missed the real person 100% of the time.
- Trial_1: the person sits lower right (rows 4 to 7, cols 3 to 7) and is mostly seated and still. The person signal ramps up over the first ~120 s (hot pixels in 14% then 45% of frames).
- Empty-room DHT (28.7) sits ~1.2 C above the frame median (27.5). **Hypothesis, untested:** this may explain some of their empty-room false positives with a DHT+0.1 C threshold.

## 6. Label reliability

- **Trial_2 is excluded.** It is 71 s, its heat signal looks like the empty room, and their own log says 1 person in only 25% of rows (0 in 63%). Its "1 person" label is not trustworthy and it is too short to be a test split. This deviates from Plan 7.2.
- Trial_1: the first ~120 s are skipped (person not clearly present).
- Session labels may not equal true occupancy at every moment (people may enter or leave). **Not verified; no video available.**

## 7. Their logged counts vs the paper (rough check, not a reproduction)

| Session | Their count equals session label | Paper | Notes |
|---|---|---|---|
| 0 persons | 92.2% | 92.02% | matches |
| Trial_1 | 77.4% (77.2% excluding zero-grid rows) | 77.12% | matches; counts 2 to 4 in 17.4% of rows (over-counting); static object flagged in 906 rows |
| 2 persons | **60.1%** | **68.99%** | **unexplained mismatch** |

Things tried for the 2-person gap, none of which explain it: de-duplicating repeated rows gives 57.1%; first/middle/last third give 62.7 / 57.4 / 60.1%. Their occupancy detection (count >= 1) is 98.2% in the log, against 100% in the paper. Possible causes: a different code version, a different scoring window, or a different subset. Ask in Step 3.
Trial_1 has `current_objects_count` > 0 in 906 rows; no other session has any. Relevant to Step 4.

## 8. Decisions that follow (see the handoff log for the full plan)

- Frame source: `esp32_raw_data.csv` only. `data.csv` only for their logged outputs.
- Loader outputs `<out>.npy` (N,8,8), `<out>_t.npy` (seconds), `<out>.meta.json`; it rejects `data.csv`.
- Split (proposed, **not yet approved**): empty 0 to 320 s dev, 320 s to end test; Trial_1 120 to 420 s dev, 420 s to end test; 2 persons from 180 s exploratory only; Trial_2 excluded.
  Weakness: dev and test come from the same room, person and day, so test is less independent than Plan 7.2's split.
- Honest-science rule: tune on `dev_*` only, run `test_*` once after parameters are frozen.

## 9. Still open

- Their code/README parameters and units (N_window, 0.5 vs 0.8 px) and the cause of the repeated rows: Step 3.
- The 2-person accuracy mismatch.
- Whether any session label is wrong at specific moments.
