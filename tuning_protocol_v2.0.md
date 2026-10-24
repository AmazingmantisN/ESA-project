# Tuning protocol v2.0 (written 23 Oct 2026, before the v2.0 sweep is run; twin of tuning_protocol_v2.0.json, whose rules win if the two ever differ)

## Why a new version
v1.4 froze Ours-v1 and Ours-v2. On the real held-out streams Ours-v2 won clearly, but on the synthetic Stage-1.1 suite it is weak where a person sits still
(short 1.2 s window: a still, seated person looks like a warm object). v2.0 is a NEW design round, not a widening of v1.4:
- adds **Ours-v3** = Ours-v2 + a *liveness* signal (a slowly wandering centroid marks a living person; `cand_policy` bit 8, parameters `live_s`, `live_thresh`; O(1) memory per track);
- re-tunes EVERY entry (Ours-v1, Ours-v2, Ours-v3, B-paper, B-code, B-code as published) on a larger dev set, with identical effort.
The v1.4 winners stay frozen as the pre-v2.0 reference (`params_frozen.json`). Nothing is changed in them.

## Dev set (the only data the sweep may see)
Three pools, weight 1/3 each in the dev total:
1. real_orig: the 10 original real-slice dev streams;
2. real_rob: the 16 v1.3 robustness dev streams (hash-checked);
3. synth_dev: 80 synthetic Stage-1.1 DEV streams (16 scenarios A1-A15 and G1, 5 seeds each; every scenario equal weight inside the pool; hash-checked against `data/synth/dev_manifest.json`).
Forbidden in tuning: test_*, expl_*, syn_test*, quiet*. The real test_* streams and the old synthetic test seeds (44,55,88,99,111,122) are burnt: descriptive only.

## Score and selection (unchanged from v1.4)
Error = false% + missed% of the smoothed count against the true count, 30 s warm-up. Dev total = mean of the three pool means.
Two stages per entry: 300 random trials, then the best 5 x 60 perturbations (600 trials per entry, same seed for every entry, equal effort).
Winner = lowest total; any trial within 0.10 pt of the best competes on lower worst-single-stream error, then lower trial index.
Edge rule: a winner parameter within 5 % of a range end is reported as edge-limited unless the end is a natural bound (k=0, persist_s/hyst_s ~1 frame) or an operational bound (window_s <= 12 s, live_s <= 20 s).
Ours-v3 searches `cand_policy` in {0,2,8,10} plus `live_s` (1-20 s, log) and `live_thresh` (0.05-0.8 source px). Its untuned reference is the nested v1 setting.
Note for the paper: Ours-v3 has more tuned dimensions than the baselines; equal trials is not equal dimensionality. Ours-v1 and Ours-v2 are re-tuned too so the ablation is fair.

## After the sweep (nothing is frozen by the sweep itself)
1. Consistency check: the v1.4 winners re-scored by the v2.0 tool must reproduce their real dev scores (original-10 and robustness-16) exactly.
2. Detection delay (splice test, report only).
3. Held-out synthetic stress, FRESH seeds 303 and 404 (never used), v2.0 winners vs v1.4 frozen winners, variants steady/jitter_s/jitter_m/drift/switch/walker. jitter_m and walker are reported only.
4. At freeze time (a separate later step): freeze the winners, generate the FRESH synthetic test (seeds 133,144,155,166,177,188; all 28 test scenarios) plus a quiet-person stress (A6/A7/A8 with much weaker wander, config declared at freeze time), score once.

## Decision rules
- R7: Ours-v3 may be called STRONGER than Ours-v1 and than Ours-v2 (v1.4 frozen) only if, on the fresh synthetic test (equal weight per scenario, strict error), the paired difference v3 minus each has a 95 % bootstrap interval (over seeds within scenarios) entirely below 0.
- R8: if R7 fails against a method, the paper says v3 is not shown to be stronger than that method and keeps the better-tested one as the main method; the v2.0 results are then a negative result.
- R9: report whatever the outcome: real dev pools of each winner (in-sample), held-out stress, delay, quiet-person stress, ESP32 parity/timing of the v3 winner.
- R10: baselines get the same effort and dev set; edge-limited baseline winners are reported, not re-widened. No later version may reuse the fresh synthetic test seeds.
- Stop rule: v2.0 is a single pass. No widening round follows it.
