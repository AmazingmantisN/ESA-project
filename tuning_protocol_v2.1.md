# Tuning protocol v2.1 (23 Oct 2026, written before the sweep is run; twin of tuning_protocol_v2.1.json, whose rules win if the two differ)

## What and why
v2.1 = v2.0 WITHOUT Ours-v3. It re-tunes Ours-v1, Ours-v2, B-paper, B-code and B-code as published, with equal effort, on a bigger dev set. Question it answers: is the gap between
real data (Ours-v2 very good) and synthetic data (Ours-v2 weak) just a tuning artifact of tuning on the 26 real streams only? The v1.4 winners stay frozen in params_frozen.json and remain the reference.
(The liveness code of Ours-v3 is still in the firmware but is inert unless cand_policy has bit 8; the nested tests prove it changes nothing.)

## Dev set (only data the sweep may see), weight 1/3 per pool
real_orig (10 real-slice streams), real_rob (16 robustness streams), synth_dev (80 synthetic Stage-1.1 dev streams, 16 scenarios, scenarios equal weight inside the pool; hash-checked).
Forbidden: test_*, expl_*, syn_test*, quiet*. Real test_* and the old synthetic test seeds are used up (descriptive only).

## Score and selection (unchanged from v1.4)
Error = false% + missed% of the smoothed count vs the true count, 30 s warm-up. Dev total = mean of the three pool means.
Per entry: 300 random trials, then best 5 x 60 perturbations (600 trials, same seed for every entry). Winner = lowest total; within 0.10 pt the lower worst-single-stream error, then lower trial index.
Edge rule: a winner parameter within 5 % of a range end is reported as edge-limited unless the end is natural (k=0, persist_s/hyst_s ~1 frame) or operational (window_s <= 12 s).
Equal trials is not equal dimensionality (Ours-v2 has 10 tuned settings, B-code 5): state this in the paper.

## After the sweep (nothing is frozen by the sweep)
1. Consistency: v1.4 winners re-scored by the v2.1 tool reproduce their real dev scores exactly.
2. Detection delay (report only). 3. Held-out synthetic-source stress on FRESH seeds 303 and 404, v2.1 winners vs v1.4 frozen winners.
4. Freezing and a FRESH synthetic test (seeds 133,144,155,166,177,188) are a separate later step.

## Decision rules
- R7: a re-tuned method replaces its v1.4 frozen version only if on the fresh synthetic test (equal weight per scenario, strict error) the paired difference new minus v1.4-frozen has a 95 % bootstrap interval entirely below 0. Otherwise v1.4 frozen stays the reported version and the re-tune is a robustness check.
- R8: report whatever the outcome (dev pools, stress, delay, v1.4 winners on the same pools). R9: same effort and dev set for every method; edge-limited winners are reported, not re-widened; fresh test seeds are never reused. Single pass: no widening round follows.
