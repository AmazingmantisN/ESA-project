# Thermal presence PoC: offline replay + real ESP32 timing

Real 8x8 AMG8833 recordings (public dataset) + injected static heat sources + the real C++ filter
running on an ESP32. No thermal sensor purchase needed.

```
firmware/thermal_poc/persistence_filter.h   the algorithm (header-only, no malloc) - used by PC *and* ESP32
firmware/thermal_poc/thermal_poc.ino        ESP32 sketch: receives frames over USB serial, replies count + microseconds
pc_test/run_pc.cpp                          same algorithm on your laptop (fast tuning)
python/load_dataset.py                      dataset CSV -> frames.npy
python/synthetic.py                         FAKE frames for testing the plumbing only
python/make_stream.py                       inject static sources, label ground truth, emulate 4x4 / 2x2
python/sweep.py                             tune window / drift / contrast
python/stream_to_esp32.py                   feed a stream to the ESP32, log results + latency
python/evaluate.py                          false-alarm %, missed %, latency
```


## REAL-DATA WORKFLOW (supersedes Steps 1-4 below; Step 0 smoke test and Step 5 still apply)
Dataset: papanashi `esp32_raw_data.csv` files (3.7-3.9 Hz, not 10 fps). Run everything from `python/`.
```bash
# 1. raw CSV -> frames.npy + _t.npy + .meta.json  (one per session; paths as on your machine)
python load_dataset.py "<papanashi>/0 persons/csv_data/esp32_raw_data.csv"      ../data/empty.npy
python load_dataset.py "<papanashi>/1 person -Trial_1/csv_data/esp32_raw_data.csv" ../data/single_t1.npy
python load_dataset.py "<papanashi>/1 person - Trial_2/csv_data/esp32_raw_data.csv" ../data/single_t2.npy
python load_dataset.py "<papanashi>/2 persons/csv_data/esp32_raw_data.csv"      ../data/two.npy
# 2. every labelled stream, with a fixed dev/test split (22 files in ../data/streams)
python make_real_streams.py
# 3. tune on DEV only (time parameters in SECONDS)
python sweep.py "../data/streams/dev_*.csv"
# 4. freeze the parameters, then evaluate on TEST exactly once
python sweep.py --evaluate "../data/streams/test_*.csv" --window_s 4 --drift 0.4 --contrast 1.0 --k 0.5
# 5. same parameters on the ESP32 (seconds converted with the stream's measured fps)
python stream_to_esp32.py --port COM7 --stream ../data/streams/test_single_laptop.csv --out ../data/res_esp32.csv --window_s 4 --drift 0.4 --contrast 1.0 --k 0.5
```
Split: empty 0-320 s dev / 320-end test; single_t1 120-420 s dev / 420-end test (first 120 s skipped,
person not clearly present); two = exploratory only; single_t2 excluded (no person signal).
Static-source variants per session: clean, laptop (+8 C), laptop_weak (+3 C), heater (+15 C), heater_weak (+3 C).
The `_weak` ones are the honest test: a person is only ~+2.3 C above the frame median in this data.
Seconds flags exist in run_pc (`--fps --window_s --maxmissed_s --smooth_s`) and stream_to_esp32.
The ESP32 sketch is unchanged (it still takes frame counts); the header only gained an unused helper,
so no reflash is needed for behaviour, but keep one copy of persistence_filter.h.

## Setup (once)
```bash
pip install numpy pandas pyserial
cd pc_test && g++ -O2 -std=c++17 -o run_pc run_pc.cpp && cd ..
```
ESP32: install Arduino IDE + "esp32 by Espressif" board package. Open `firmware/thermal_poc/thermal_poc.ino`.

## Step 0 - prove the plumbing with fake data (10 min, do this first)
```bash
cd python
python synthetic.py ../data/synth_single.npy --humans 1
python synthetic.py ../data/synth_empty.npy  --humans 0 --seed 5
python make_stream.py ../data/synth_single.npy --humans 1 --inject laptop --pos 6,1 --out ../data/t_laptop.csv
../pc_test/run_pc --stream ../data/t_laptop.csv > ../data/t_res.csv
python evaluate.py ../data/t_res.csv
```
Synthetic numbers are NOT paper results; they only show the code runs.

## Step 1 - get real frames
1. Make a free IEEE account (use your college email), go to IEEE DataPort.
2. Search "Grid-EYE Dataset for Human Occupancy Detection and Counting in a Study Pod"
   (single 8x8 AMG8833, sessions: empty / 1 person / 2 people). It is labelled "Standard Dataset":
   if download needs a subscription, ask your college library. Fallback: the open-access
   "TODOS Dataset" (8x8 logs from many rooms; pick a room with one sensor and check how its labels work).
3. Save the CSVs under `data/raw/` (e.g. `empty.csv`, `single.csv`).
I have NOT seen these files. `load_dataset.py` prints what it detected; if it cannot find the 8x8 grid
it lists the columns - send me the first 2 rows and I will adapt it.

## Step 2 - convert
```bash
python load_dataset.py ../data/raw/empty.csv  ../data/empty.npy
python load_dataset.py ../data/raw/single.csv ../data/single.npy
```
Check the printed min/max/mean are room temperatures (roughly 20-35 degC).

## Step 3 - build labelled streams with injected "laptops/heaters"
```bash
python make_stream.py ../data/empty.npy  --humans 0 --inject laptop --out ../data/s_empty_laptop.csv
python make_stream.py ../data/empty.npy  --humans 0 --inject heater --out ../data/s_empty_heater.csv
python make_stream.py ../data/single.npy --humans 1 --inject laptop --out ../data/s_single_laptop.csv
python make_stream.py ../data/single.npy --humans 1 --inject none   --out ../data/s_single_clean.csv
```
The injected source is auto-placed far from where the person usually sits (`--pos row,col` to override).
Ground truth: `humans` = people in the session, `injected` = fake static sources. Any count above `humans`
is, by construction, a static source mistaken for a person.

## Step 4 - tune on the laptop (seconds per run)
```bash
python sweep.py ../data/s_single_laptop.csv ../data/s_empty_heater.csv ../data/s_single_clean.csv
```
Pick the best row, then set those values as defaults in `FilterParams` (persistence_filter.h) and rebuild.
HONEST-SCIENCE RULE: tune on one half of each recording and report numbers on the other half (or on
a different session), otherwise you are reporting training error.

## Step 5 - run on the ESP32 (this gives the latency number)
1. Flash `thermal_poc.ino`, close the Arduino Serial Monitor (it blocks the port).
2. Find the port (Windows `COM5`, Linux `/dev/ttyUSB0`, Mac `/dev/cu.usbserial-*`).
```bash
python stream_to_esp32.py --port COM5 --stream ../data/s_single_laptop.csv --out ../data/res_esp32.csv
python evaluate.py ../data/res_esp32.csv
```
Counts should match the PC build frame-for-frame (same header file). The `us` column is time spent
inside `filt.process()` only (not serial transfer), measured with `micros()`. Report mean / p95 / max.
If the port errors out: hold BOOT while uploading, try a different USB cable (many are charge-only),
install the CP210x/CH340 driver for your board.

## Step 6 - resolution study + ablation (the "does it scale" argument)
```bash
python make_stream.py ../data/single.npy --humans 1 --inject laptop --grid 4 --out ../data/s_g4.csv
python make_stream.py ../data/single.npy --humans 1 --inject laptop --grid 2 --out ../data/s_g2.csv
../pc_test/run_pc --stream ../data/s_g4.csv > r4.csv   # re-tune per resolution with sweep.py first!
../pc_test/run_pc --stream ../data/s_single_laptop.csv --robust 0 > r_ablation.csv   # mean+std threshold
```
For latency vs resolution on hardware: change `#define GRID 4` (or 2) in the .ino, reflash, stream the matching CSV.

## What my synthetic smoke tests showed (use as hypotheses, NOT as results)
* Mean+std threshold (your original design): a hot laptop pushed the threshold above the person -> person
  missed ~100%. Median+MAD threshold fixed this. Keep both (`--robust 0/1`) - the ablation is a nice paper figure.
* A static source's centroid jitters with sensor noise; if `drift_thresh` is below that noise floor the laptop
  looks "alive". Tune it on the static-source recordings.
* A person ~3.5 px from a hot source can bridge into one blob and make the static source's centroid jump.
  Raising `min_contrast` helps; report it as a limitation.
* At 4x4 and especially 2x2, the median-background trick breaks (the person covers most pixels), so detection
  collapses even after re-tuning. If real data confirms this, the honest conclusion is a minimum useful
  resolution, not "works on 2x2 therefore on 8x8".

## Known limits to state in the paper
Offline replay + synthetic static sources (not a live deployment); a person who is truly motionless for N frames
is classified static (the missed-detection rate measures this); parameters are tuned on one dataset/one room;
the original dataset authors also publish a deterministic blob pipeline with a hot-object count - cite and compare.


## v2 (Plan Step 5): baseline modes for the head-to-head

`persistence_filter.h` now also runs the Papanashi et al. rules, selected by flags. Defaults are exactly v1
(`pc_test/check_v1_equiv.py`: 0 mismatches). Details of every baseline parameter: `baseline_spec.md`.

Rebuild after copying the files in:
    cd pc_test
    g++ -O2 -std=c++17 -o run_pc.exe run_pc.cpp
    g++ -O2 -std=c++17 -o test_modes.exe test_modes.cpp  &&  test_modes.exe        (expect: 35 tests, 0 failed)
    python check_v1_equiv.py                                                        (expect: mismatches: 0)

Rebuild the data once (the loader now also saves the DHT series, and streams get a `dht` column):
    cd ..\python
    python load_dataset.py "<raw>\0 persons\csv_data\esp32_raw_data.csv" ..\data\empty.npy      (repeat for single_t1, single_t2, two)
    python make_real_streams.py

Run a baseline on the PC (same flags go to stream_to_esp32.py):
    ..\pc_test\run_pc.exe --stream ..\data\streams\dev_single_clean.csv --fps 3.79 --preset bpaper --timebase paper > ..\data\r.csv
    --preset bpaper | bcode | bcode_asis     --timebase frames | paper | loop (bpaper)     --dht_offset 0.2
Untuned DEV-only sanity table:  python baseline_preview.py "..\data\streams\dev_*.csv"

ESP32: re-flash firmware\thermal_poc\thermal_poc.ino (protocol is a superset of v1), then
    cd ..\pc_test
    python check_firmware_protocol.py --port COM7 --stream ..\data\streams\dev_single_laptop_weak.csv --frames 600
(expect nine lines starting OK; it compares the ESP32 with run_pc frame for frame for every preset).
New output column `static` (tracks classed static) in run_pc and stream_to_esp32.py results.
