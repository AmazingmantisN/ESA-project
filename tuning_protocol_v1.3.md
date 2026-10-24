# tuning_protocol_v1.3.md - Plan Step 7 protocol, VERSION 1.3 (23 Oct 2026)

Machine-readable twin: `tuning_protocol_v1.3.json` (the tool reads it; its SHA-256 is printed and saved with every result).
Tools: `python/tune_sweep.py --protocol ..\tuning_protocol_v1.3.json` (parallel, `--jobs N`), one-command runner `python/run_v13.py` (writes `summary_v13.md`).
Supersedes v1.2 (json sha256 5b58cb8defc2e5e9..., md 280b092c04525b8c...), v1.1 (239ef348...) and v1.0 (6eede3d6...). Earlier files and results are kept for the record; v1.3 writes to `tuning_results_v13/`.

## 1. Why v1.3 exists (changes from v1.2)
**Evidence.** v1.2 scored every method on perfectly steady injected sources only. The Step 5e stress test (rebuilt dev slices with non-ideal sources, seed 77, reproduced on the laptop on 23 Oct) showed the v1.2 winners are steady-source specialists:
Ours-v2 scored 0.4 % on steady/drift/switch sources but 74.7 % on jitter_s, 96.5 % on jitter_m and 95.1 % on a walker; Ours-v1 scored 66.7 % on jitter_s. Over all variants except the walker: Ours-v1 37.4 %, Ours-v2 34.5 %, B-code 55.5 %, B-paper 55.7 %.
Ours-v2's whole advantage was fewer misses (0.3 % vs 4.6 %); its false alarms were not lower (34.2 % vs 32.7 %). Dev tuning therefore selected what is best on easy sources.

**The one change.** Dev scoring now uses 26 streams: the 10 original ones plus 16 robustness streams with non-ideal injected sources (section 2). Nothing else changes: search spaces, trial budget, seeds, shared choices, tie-break, edge rule and the 10 original streams are identical to v1.2.
Consequence (free check, `python/check_v13_vs_v12.py`): every stage-1 trial has the same parameters as in v1.2 and must score identically on the original 10 streams. Stage 2 differs because the top-5 differ.

**This change is adaptive.** It was designed after seeing the v1.2 DEV results and the seed-77 stress results, i.e. after learning where the methods fail. It is recorded here for that reason. test_* was never touched.

**What v1.3 does not claim.** v1.3 totals are scores on a different, harder set. They are not comparable with v1.2 totals and a drop is not a regression. Comparisons between versions are made only (a) on the original-10 sub-score, or (b) on the held-out stress seeds of section 6.

## 2. Data
- **Original 10** (unchanged): `dev_*` = 2 real slices (empty 0-320 s, single person 120-420 s) x 5 variants (clean, laptop +8 C, laptop_weak +3 C, heater +15 C, heater_weak +3 C).
- **Robustness 16** (new): `dev_rob_<empty|single>_<variant>_<w|s>` built from `dev_empty_clean` / `dev_single_clean` by `python/make_robust_dev.py` (seed 20261023, one generator per stream). Source: size sigma 0.7 px at (1,1), +3 C (w) or +8 C (s), as in dev.
  | variant | behaviour |
  |---|---|
  | jitter_xs | position wanders 0.05 px/frame, amplitude flicker 0.15 C (AR 0.8): a very quiet laptop |
  | jitter_s | 0.10 px/frame, flicker 0.30 C: a laptop with a fan |
  | drift | slides 1.5 px along the row over the stream |
  | switch | off for the first 35 %, ramps on over 5 s (opened), jumps 1 px at 70 % (moved) |
  The generated files are shipped; `tune_sweep.py` checks their sha256 against `data/streams/dev_rob_manifest.json` and refuses to run on any difference. Do not regenerate them on another machine.
- **Not tuned, reported only:** `jitter_m` (0.25 px, 0.6 C) collapsed every method to 89-97 % at seed 77, so it carries no tuning signal; `walker` (random walk 0.35 px/frame) behaves like a person and is an adversary that no motion-based rule can separate without Layer 2.
- The jitter severities are not calibrated to a real laptop. The xs/s ladder shows how fast a method degrades; the real fan/heater behaviour is Step 10.
- The tool refuses any stream whose name contains `test_` or `expl_`. `test_*` is touched once, after freezing.

## 3. Score
Unchanged from v1.2: error per stream = false-alarm % + missed %, warm-up 30 s, compared count = `smooth`; each dev stream weighted equally. With 26 streams the robustness streams are 16/26 = 62 % of the total. For that reason the tool also reports, for every winner, the original-10 sub-score, the robustness-16 sub-score and the error per variant.

## 4. Search (equal effort, two stages): unchanged
Stage 1: 300 random trials per entry, seed 20261019. Stage 2: top 5, 60 perturbations each, seed 20261020. 600 trials per entry. Spaces exactly as in v1.2 (Ours-v1 6 settings, Ours-v2 10, B-paper 5, B-code 5; Ours-v2 size/warmth gate and merge_area fixed, not tuned).
Spaces are NOT widened in this version even where a v1.2 winner sat near an end (Ours-v2 persist_s 21.3 of 30). The edge rule applies as before; a v1.3 winner within 5 % of a non-natural range end is reported and triggers widening in a new version.

## 5. Selection rule: unchanged
Lowest mean total error over stage 1 + stage 2; trials within 0.10 points are tied and broken by lower worst-single-stream error (now over 26 streams), then lower trial index. "As published" references are scored but not eligible.

## 6. Held-out evaluation and interpretation rules (fixed before the v1.3 sweep)
After the sweep, `python/robust_check.py` is run on **seeds 44 and 55** (never used in tuning) for the v1.3 winners and, for comparison, the v1.2 winners, over all six variants including jitter_m and walker. Seed 77 was seen before v1.3 and is not held out.
Rules for reading the result:
- **R1 (re-tuning helped a method):** only if its held-out "all except walker" error is lower for the v1.3 winner than for the v1.2 winner on both seeds. Otherwise report that re-tuning gave no robust gain.
- **R2 (Ours-v2 vs Ours-v1):** Ours-v2 may be called more robust than Ours-v1 only if it is lower on "all except walker" on both seeds by more than the seed-to-seed difference of either method. Otherwise it is reported as a steady-source specialist, whatever its dev rank.
- **R3:** the jitter_m and walker rows are reported as ceilings and are never used to pick a winner.
- **R4:** the price of robustness is reported: the v1.3 winners' original-10 sub-score versus the v1.2 winners' (v1.3 will be worse there by construction).
- **R5:** if held-out results show a problem, the next version records it and uses new seeds; seeds 44/55 are then no longer held out.
The decision to freeze (`params_frozen.json`) and run test_* once is made only after reviewing the v1.3 candidates and this table together.

## 7. Known limits (state them in the paper)
- Adaptive design (section 1): the variants were chosen after seeing where methods failed. Held-out seeds only test new noise draws of the same generator, not new kinds of source; they check the tuning, not the simulator.
- Dev is still two real slices from one room/day/person; the 26 streams reuse the same frames, so effective evidence is small and overfitting risk remains. All injected sources sit at (1,1) with one size; no multi-person stream.
- Jitter severity is arbitrary (not calibrated to a real laptop); only real recordings (Step 10) can validate any of this.
- Equal trials is not equal dimensionality (Ours-v1 6, Ours-v2 10, B-paper 5, B-code 5).
- The robustness streams are 62 % of the total: a method that handles them well but costs a little on steady sources wins. This is a stated choice, not a neutral one.
- Their logged static flags are not reproduced (step5b), so baselines are "per the paper and code description".
