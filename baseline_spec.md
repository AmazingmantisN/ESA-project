# baseline_spec.md — Papanashi et al. persistence baseline (Plan Step 3 output)

Written 16 Oct 2026. Source: github.com/kernelops/thermal-occupancy-monitor at commit
`5d7fe8a2432659845f41b1bbb0b5ebd2a7c29d2c` (no LICENSE file). Files read in full: `main.py` (PC server),
`ESP32_Script.ino` (firmware), `README.md`. **Nothing here copies their code: values and behaviour are
described so we can reimplement from the equations and cite.**

Paper values (Eq. 12/13, Table 4, N_persist = 100, Δ_static = 0.5, Δ_reset = 2.0) are taken from Master Plan
section 3.4; the paper itself was not re-read in this step.

## 1. Headline findings

1. **The repo contains two different persistence rules.** `main.py` (PC) matches the paper (window + counter + reset).
   The ESP32 firmware and README use another rule with other numbers (20 frames, 0.8).
2. **N_window is 15** (`DRIFT_WINDOW_FRAMES` in `main.py`). The paper's Table 4 omits it.
3. **All distances are in cells of the 71x71 upsampled grid, not source pixels.** 10 cells = 1 sensor pixel.
   Their 0.5 = **0.05 source pixel**; 0.8 = 0.08; reset 2.0 = 0.2; match radius 25 (Manhattan) = 2.5 source pixels.
4. **The firmware as published does not suppress static objects.** It counts every track as a person, then builds
   a static mask and throws it away. Only `main.py` excludes static tracks from the people count.
5. **The dataset was not produced by this repo's `main.py`.** The repo logger writes 6 columns and no
   `esp32_raw_data.csv`; the dataset has `net_crossing_count` and a raw file. The code version behind the
   logged counts is unknown.
6. **The repeated rows in `data.csv` are explained** (section 4).
7. **DHT offset may be applied twice** (section 5, D7). Unverified.

## 2. Parameter table (value, unit, source)

"cells" = 71x71 grid cells. "iter" = one pass of the `main.py` main loop (not one new sensor frame).

| Parameter | Paper | `main.py` (PC) | ESP32 firmware | README | Unit / note |
|---|---|---|---|---|---|
| Interpolation | linear then linear (bilinear), 71x71 | same, factor 10 | same | "bilinear" | no real difference |
| Threshold | DHT11 + 0.1 C | `>=` (DHT + 0.1 sent by firmware) + 0.1 again in the server | `>=` DHT + 0.1 | DHT + 0.1 | see D7 |
| DHT update | not checked | every frame, as received | every 10 s (`DHT_INTERVAL`) | 10 s | firmware |
| Blobs | connected components | OpenCV `connectedComponents` (default 8-connectivity) | flood fill, 4-connected | | |
| Centroid | | unweighted mean of blob cell coordinates | same | | **not intensity-weighted**; ours is |
| Match radius | | Manhattan < 25 cells, nearest blob | Manhattan < 25 cells, first fit | 25 | firmware takes the first track within range |
| Fallback match | central-point Jaccard | Jaccard of central points; distance 7, index 0.25 | none | 7 / 0.25 | module-level defaults 5 / 0.3 are overridden in `__main__` |
| Stale track pruning | 3 frames | removed when age >= 3 iter | age >= 3 iter | | |
| Max tracks | 10 | no cap found | `MAX_TRACKED` = 10, `MAX_BLOBS` = 20 | | |
| **N_window** | **not given** | **15 iter** | none | none | |
| **N_persist** | 100 frames (10 s) | 100 consecutive iter | 20 (compared with path length) | 20 | |
| **Δ_static** | 0.5 "px" | 0.5 cells | 0.8 cells | 0.8 px | |
| **Δ_reset** | 2.0 "px" | 2.0 cells from locked centroid | 2.0 cells | | |
| Mask radius | | `int(sqrt(size/pi)) + 2` cells | `sqrt(size/pi) + 2` | dilation 2 | |
| People count | | tracks **not** static | **all tracks** (static ones included) | | see headline 4 |
| Object count | | static tracks | static tracks | | |

## 3. The two rules, precisely

**Rule A: `main.py` / paper (our B-paper).** For each track not already static:
if the track has at least 15 positions, compute the distance between the current centroid and the centroid 15
updates earlier. If it is below 0.5 cells, a per-track counter increases by one; otherwise the counter is reset to 0.
When the counter reaches 100 the track becomes static: its centroid is locked and a circular mask is stored.
A static track returns to normal when its centroid is more than 2.0 cells from the locked centroid.
The counter also resets to 0 if the track has fewer than 15 positions.

**Rule B: firmware / README (our B-code).** Each track keeps a path of at most 20 positions (it stops growing at
20, it never slides). Once the path is full, **every frame** the track is compared with its *first position*
(its birth position, or the position at the last crossing of row 35). If that distance is below 0.8 cells, the track
becomes static. There is **no counter and no window**. The reset rule is the same as in Rule A.
Consequence: a blob that happened to start within 0.8 cells of where it is 20 updates later is flagged
immediately, and a person who drifts away and returns to the starting point is flagged too.
The published firmware computes the mask but never applies it, so there is no suppression (headline 4).

## 4. Why `data.csv` has repeated rows (resolved from the code, consistent with the data)

`main.py` receives frames in a separate server thread and runs its own loop (about 50 ms wait plus processing)
that copies "the latest frame" every pass and **writes one row per pass whether or not a new frame arrived**.
The firmware delivers a new frame about every 0.26 s, while the loop writes about every 0.13 s.
Measured from `data.csv` timestamps: 7.27 / 7.49 / 7.79 / 7.66 rows per second, against 3.73 to 3.89 unique
frames per second in the raw files. So about every second row repeats. The all-zero rows and DHT = 0 at the start of
`data.csv` are the loop's initial values before the first frame arrived.
**Consequence: every frame-count parameter in `main.py` counts loop passes, not sensor frames.** 100 passes is
about 13 s of wall time (about 50 unique frames), not 10 s; 15 passes is about 2 s.
Inference, not verified: the sensor-side rate of about 3.8 Hz probably reflects the firmware loop time (HTTP post, full
pipeline and a 50 ms delay).

## 5. Discrepancy log

| ID | Discrepancy | Status |
|---|---|---|
| D1 | N_persist: paper 100 (10 s) vs `main.py` 100 passes (about 13 s) vs firmware/README 20 | both variants kept |
| D2 | Δ_static: 0.5 vs 0.8 | both variants kept |
| D3 | N_window absent from the paper; code 15 | resolved: 15 |
| D4 | Different rules in PC and firmware (section 3) | both variants kept |
| D5 | Units: cells of the 71x71 grid, not source pixels | resolved; our drift threshold is in source pixels = cells / 10 |
| D6 | Firmware counts static tracks as people and discards the mask | resolved from code |
| D7 | DHT offset: firmware sends DHT + 0.1, server adds another 0.1, so the effective threshold may be DHT + 0.2, not +0.1 as in paper and README. The raw CSV value 28.700000000000003 hints at a float addition but does not show where. | **unverified**; ask authors |
| D8 | Dataset columns (`net_crossing_count`, `esp32_raw_data.csv`) are not produced by the repo's logger | **unknown code version**; ask authors |
| D9 | `data.csv` repeats rows because the loop outruns the sensor | resolved |
| D10 | Jaccard constants differ between module defaults (5, 0.3) and `__main__` (7, 0.25) | resolved: use 7 / 0.25 (README agrees) |

DHT11 accuracy, from vendor listings of the module (not the original Aosong datasheet): temperature resolution 1 C,
accuracy +/- 2 C, range 0 to 50 C. A 0.1 C threshold offset is therefore 20 times smaller than the sensor's stated
accuracy, which matches the paper's own admission that detection weakens when DHT approaches blob temperature.
Our data shows the DHT sitting about 1.2 C above the empty-room frame median (hypothesis in `dataset_notes.md`, untested).

## 6. Baseline variants to implement in Step 5

| Variant | Rule | N_window | N_persist | Δ_static | Δ_reset | Threshold |
|---|---|---|---|---|---|---|
| **B-paper** (= `main.py`) | A | 15 | 100 | 0.5 cells (0.05 px) | 2.0 cells (0.2 px) | DHT + 0.1 C |
| **B-code** (firmware/README) | B | 20 (path length) | none | 0.8 cells (0.08 px) | 2.0 cells (0.2 px) | DHT + 0.1 C |

Open decisions for the plan (not made here):
- **Time base for B-paper.** Our replay has about 3.8 unique frames per second. Options: 100 and 15 unique frames
  (about 26 s and 4 s), 10 s and 1.5 s (the paper's claim), or 13 s and 2 s (the logged loop rate). I suggest running
  all three as a sensitivity check and reporting them.
- **B-code suppression.** The published firmware never applies its mask. I suggest implementing the *intended*
  behaviour (static tracks excluded from the people count), labelling it clearly as an assumption, and also
  reporting the as-published count.
- **DHT offset** (D7): run +0.1 and +0.2 as a sensitivity check.
- **Hypothesis for Step 5/8, untested:** their thresholds of 0.05 to 0.08 source pixels sit at the same scale where our
  synthetic test showed centroid jitter looking like motion (about 38% false alarms at 0.08). Our dev sweep prefers 0.4.
  This may mean their static rule rarely triggers on a jittery blob. Test it; do not assume it.

## 7. Still open

- Which code version produced `data.csv` and `esp32_raw_data.csv` (D8). Worth an email to the authors, together
  with the DHT offset (D7) and the unit of Δ_static.
- The paper's own text was not re-read here; confirm Table 4 and Eq. 12/13 against the PDF before citing.
- Why their 2-person accuracy in the logs (60.1%) does not match the paper (68.99%). Unexplained.
