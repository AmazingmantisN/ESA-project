# tuning_protocol.md - Plan Step 7 protocol, VERSION 1.2 (23 Oct 2026)

Machine-readable twin: `tuning_protocol.json` (the tool reads it; its SHA-256 is printed and saved with every result).
Tool: `python/tune_sweep.py` (parallel, `--jobs N`). One-command runner: `python/run_all.py` (writes `summary.md`).
Supersedes v1.1 (json sha256 239ef348cfb68181..., md 662c87f6619a9ac3...), which superseded v1.0 (json sha256 6eede3d6...). Earlier results are kept for the record.

## Why v1.2 exists (changes from v1.1)
1. **Ours-v2 enabled.** Step 5c built it (persistence mode 3, verified: 35/35 unit tests, nested equivalence with Ours-v1, ESP32 parity on 13 parameter sets). Its search space is fixed below, BEFORE any v2 sweep has been run.
2. **Erratum on the edge rule.** v1.1 section 5 said a winner within 5% of a range end triggers widening. k had a winner at 0.0719 of a 0-3 range; k = 0 turns the k term off, so 0 is a *natural bound*, not an arbitrary limit. From v1.2, ends marked `natural_bounds` in the JSON (k lower end; persist_s and hyst_s lower ends, about one frame) are reported as 'natural bound, no widening'. Every other edge still triggers widening in a new version.
3. **Nothing else changes**: Ours-v1, B-paper, B-code spaces, seeds, budget (300 + 5x60), scoring, tie-break and data are identical to v1.1, so their samples and results must reproduce v1.1 exactly (a free check). Made after seeing v1.1 DEV results; test_* never touched.

## Why v1.1 exists (changes from v1.0)
v1.0 gave every method 300 random trials. Ours has six free settings and was under-sampled: only 2 of 300 trials landed near a configuration
that scores 10.61% on dev, while the best random trial scored 14.20%. B-code (fewer settings) saturated by ~100 trials. Equal trials was not
equal effort, so v1.0 numbers must not be used to compare methods. v1.1 adds a refinement stage, identical for every entry. This change was made
AFTER seeing v1.0 DEV results (test_* was never touched) and is recorded here for that reason.

## 1. Question
Which parameters does each method get, chosen the same way, before the one held-out test run (Step 8)?
Entries: **Ours-v1**, **Ours-v2** (Layer 1; enabled in v1.2), **B-paper** (their main.py/paper rule),
**B-code intended**, **B-code as published** (reference: static tracks are still counted, so it cannot compete).

## 2. Data
- Tune on `data/streams/dev_*.csv` only: 10 streams = 2 real slices (empty 0-320 s, single person 120-420 s) x 5 variants
  (clean, laptop +8 C, laptop_weak +3 C, heater +15 C, heater_weak +3 C), each stream weighted equally.
- The tool refuses any stream whose name contains `test_` or `expl_`. `test_*` is touched once, after freezing.
- `test_*` streams start 20 s after the dev slice ends (guard gap from measured decorrelation), built by `make_real_streams.py`.

## 3. Score (identical for every entry)
- Error per stream = false-alarm % + missed % (smoothed count above / below the true number of people), mean over the 10 dev streams.
- Common warm-up: the first **30 s** of each stream is not scored. The compared count is the `smooth` column of `run_pc` for every entry.

## 4. Search (equal effort, two stages)
- **Stage 1:** random search, 300 trials per entry, RNG seed 20261019, each entry sampled from its own space (see the JSON). Identical to v1.0.
- **Stage 2:** take the 5 best stage-1 trials (ties by trial index); for each, 60 perturbations (continuous values: x or / by exp(N(0,0.2)) on log
  ranges, +N(0, 8% of range) on linear ranges, clipped to the range; discrete values re-sampled with probability 0.3). RNG seed 20261020.
- 600 evaluated trials per entry. Results do not depend on the number of parallel jobs.
- Spaces: Ours: window_s 1.5-12 (log), drift 0.05-1.5 (log), contrast 0.3-2.5, k 0-3, smooth_s {0, 1.3}, maxmissed_s {0.5, 1, 2.5}.
  B-paper: time base {frames, paper, loop}, delta_static 0.05-0.8 (log), DHT offset {0, 0.1, 0.2}, smooth_s, maxmissed_s.
  B-code (both): path length {10, 20, 40, 80}, delta_static 0.05-0.8 (log), DHT offset {0, 0.1, 0.2}, smooth_s, maxmissed_s.
- Ours-v2 space: the six Ours-v1 settings (same ranges) plus persist_s 0.25-30 (log; still time before a track becomes a candidate), hyst_s 0.25-8 (log; moving time that releases a candidate), cand_policy {0 suppress all candidates, 2 count a candidate only if it was seen moving first, 4 count every candidate}, assign_mode {0 per-track greedy, 1 global one-to-one}. 10 dimensions.
- Ours-v2 FIXED, not tuned: size/warmth gate (cand_min_area = 0, cand_max_peak = 0) and merge_area = 0. Dev has no multi-person stream, and the injected laptops/heaters have simulator-chosen size and amplitude, so tuning a size/warmth gate on dev would fit the simulator. That gate belongs to Layer 2, validated on real recordings (Step 10).
- Nesting: mode 3 with 1-frame persist/hyst, policy 0, assign 0 equals Ours-v1 exactly, so Ours-v2's achievable optimum is at least Ours-v1's; if the v2 search ends worse, that is search noise from the larger space, and is reported as such (the v2 reference scores exactly the v1 reference, 10.61% on dev).
- The "as published" reference configuration of every entry is scored separately and is NOT eligible to win.
- Not tuned (fixed in presets): matching radius, connectivity, reset threshold, min blob area 1 for baselines.

## 5. Selection rule (fixed in advance)
- Best = lowest mean total error over stage 1 + stage 2. Any trial within 0.10 points of the best is a tie, broken by lower worst-single-stream error, then lower trial index.
- Edge rule: if a continuous parameter of a winner lies within 5% of a range end (log scale for log ranges), report it; widen that range in a NEW protocol
  version and rerun all entries. Never silently.
- Report with each winner: top-10 spread, untuned reference, per-stream totals (`trials_<entry>.csv`).

## 6. After tuning
- Review candidates together, then write `params_frozen.json` (protocol hash + candidates). Only then run `test_*` once (Step 8). The final method list must be fixed before freezing.
- Negative results are reported. Their logged people/object counts are never ground truth. Synthetic suite numbers are stress tests, not headline evidence.

## 7. Known limits (state them in the paper)
- Dev is two real slices from one room/day/person and the five variants reuse the same frames: small effective evidence, real overfitting risk.
- Test comes from the same session (20 s later): less independent than a new room or person.
- Equal trials is not equal dimensionality (Ours-v1 6 knobs, Ours-v2 10, B-paper 5, B-code 5). Equal budget favours the smaller spaces; this is stated, not corrected.
- Ours-v2's candidate mechanism is built for a still person absorbed by the static test; dev contains such episodes (single_* streams), so v2 is partly designed with dev in view. Test (Step 8) is the check.
- Injected laptops/heaters are perfectly steady and sit at one position (1,1): the easy side of the problem. Session labels may not equal true occupancy at every moment.
- Their logged static flags are not reproduced (step5b), so baselines are "per the paper and code description".
