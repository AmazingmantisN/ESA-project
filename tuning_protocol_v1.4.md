# tuning_protocol_v1.4.md - Plan Step 7 protocol, VERSION 1.4 (23 Oct 2026)

Machine-readable twin: `tuning_protocol_v1.4.json` (the tool reads it; its SHA-256 is printed and saved with every result).
Tools: `python/tune_sweep.py --protocol ..\tuning_protocol_v1.4.json`, one-command runner `python/run_v14.py` (writes `summary_v14.md`). Results go to `tuning_results_v14/`.
Supersedes v1.3 (json sha256 5b9e84f057b02de9..., md 8705957aec4a4c2d...), v1.2 (5b58cb8d..., 280b092c...), v1.1 (239ef348...) and v1.0 (6eede3d6...). Earlier files and results are kept.
Everything not listed in section 1 is exactly as in v1.3 (26 dev streams = 10 original + 16 robustness, scoring, budget 300 + 5x60 trials per entry, seeds 20261019/20261020, shared choices, tie-break, edge rule 5 %).

## 1. Why v1.4 exists (changes from v1.3)
The v1.3 edge rule fired on five winner parameters (reported, never silently ignored):
| Entry | Parameter | v1.3 winner | v1.3 range |
|---|---|---|---|
| Ours-v1 | window_s | 12.0 | 1.5-12 |
| Ours-v2 | window_s | 1.60 | 1.5-12 |
| Ours-v2 | persist_s | 27.97 | 0.25-30 |
| B-paper | drift | 0.80 (all top-10 identical) | 0.05-0.8 |
| B-code | drift | 0.73 | 0.05-0.8 |
Changes:
1. **Ours-v2 persist_s hi 30 -> 90 s.** (Still time before a track becomes a stationary candidate; 90 s is about 340 frames, the counters are `int`.)
2. **window_s lo 1.5 -> 0.5 s for BOTH Ours-v1 and Ours-v2** (the firmware clamps the window to at least 2 frames, about 0.5 s). Applied to both so the six shared Ours knobs stay in the same ranges and Ours-v2 still contains Ours-v1.
3. **drift hi 0.8 -> 2.0 for B-paper, B-code and B-code as published.** Without this the baselines are capped by our own range choice and "Ours beats the baselines" would not be a fair statement.
4. **Operational limit, window_s <= 12 s for Ours-v1 and Ours-v2 (declared, not widened).** A new track is not counted until its history window fills, so window_s is a detection delay, and the dev slices (minutes long) do not penalise delay. The v1.3 winner sat at exactly 12 s. Widening would reward ever longer delay; instead 12 s (about 45 of the firmware's 64 frames) is fixed as the deployable limit and an edge there is reported as 'operational limit, no widening'. This is declared after seeing the v1.3 winner and is therefore adaptive.
5. **Stop rule (fixed now):** v1.4 is the last widening iteration. A winner still on a non-natural, non-operational range end is reported as 'edge-limited' and stated as a limit of the search in the paper; it does not trigger v1.5.
6. **New report, not a score: detection delay** (`python/latency_check.py`, section 5).
7. **Fresh held-out seeds 101 and 202** (section 6). Seeds 44/55 judged v1.3 and 77 designed it; 66 and 88 were used once to smoke-test the runner with the v1.2/v1.3 winners and their output was seen, so they are burnt as well. 101 and 202 have never been run.

**Adaptive.** Made after seeing the v1.3 dev results and the v1.3 held-out results (seeds 44/55). test_* was never touched.
**Consistency check.** Because log ranges changed, the stage-1 samples differ from v1.3 for all entries, so trials cannot be compared. Instead `python/check_v14_rescore.py` re-scores the five v1.3 winners with the v1.4 tool; they lie inside the v1.4 ranges and must reproduce their v1.3 dev scores (total, original-10, robustness-16). A v1.4 winner worse than the v1.3 winner on the same 26 streams is search noise from the larger space and is reported as such.
**Comparability.** v1.4 dev totals are on the same 26 streams as v1.3, so they are comparable with v1.3 (not with v1.2 totals, 10 streams).

## 2-4. Data, score, search: as v1.3
Spaces: as v1.3 except the four changes above. Ours-v2 size/warmth gate and merge_area stay fixed. jitter_m and walker are never tuned, only reported.

## 5. Detection-delay report (not part of the score)
Splice: last 60 s of dev_empty_clean + first 150 s of dev_single_clean (labels 0 then 1). Per winner: delay until the smoothed count is >= 1 for 5 s, false-alarm % in the empty part after the 30 s warm-up, and % of frames with count == 1 in the last 60 s. The person is already seated when the single slice starts, so this is the delay of a fidgeting person who appears in view, not of someone walking in; the real entry delay is a Step 10 measurement. The ambient step at the splice is printed (the slices are different sessions).

## 6. Selection and held-out rules (fixed before the v1.4 sweep)
Selection rule unchanged. After the sweep `python/robust_check.py` runs on seeds 101 and 202 for the v1.4, v1.3 and v1.2 winners, all six variants.
- **R1:** re-tuning in v1.4 helped a method only if its held-out "all except walker" error is lower for the v1.4 winner than for the v1.3 winner on both seeds; otherwise v1.3 and v1.4 are reported as equivalent and the simpler/earlier one stays the candidate.
- **R2:** Ours-v2 may be called more robust than Ours-v1 only if it is lower on "all except walker" on both seeds by more than the seed-to-seed difference of either method; otherwise it is a steady-source specialist whatever its dev rank.
- **R3:** jitter_m and walker are never used to choose parameters (selection is dev-only). R1 and R2 use the 'all except walker' row exactly as written, which includes jitter_m; because jitter_m is volatile across seeds (a heavy tail for Ours-v2), the table also prints the mean of the four tuned-family variants (steady, jitter_s, drift, switch) as a diagnostic row. It is reported next to the R1/R2 verdict and does not replace it.
- **R4:** report the price of robustness (original-10 sub-score of each version's winner).
- **R5:** report any delay_s above the 12 s operational limit and any winner whose delay is longer than that of the B-paper winner by more than 12 s; the paper states the delay next to the accuracy.
- **R6:** if a held-out problem appears, the next version records it and uses new seeds.
The decision to freeze (`params_frozen.json`) and run test_* once is made only after reviewing the v1.4 candidates, the held-out table and the delay table together.

## 7. Known limits (state them in the paper)
All limits of v1.3 section 7 remain: adaptive design (now twice), dev is two real slices from one room/day/person, held-out seeds test the generator not real sources, jitter severity uncalibrated, injected sources at one position and size, no multi-person stream, equal trials is not equal dimensionality, robustness streams are 62 % of the total.
New: (a) the 12 s window limit and the 2.0/90 s widenings are judgement calls recorded here, not derived; (b) the delay test is a splice of two sessions, indicative only; (c) a jitter-tolerant Ours-v2 (long persist, large drift threshold) is validated only against our synthetic jitter; it could also hide a real person who sits very still for a long time, which dev contains only as one real slice.
