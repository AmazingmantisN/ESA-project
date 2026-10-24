# LINAIGE re-tune: protocol L1.0 (written 24 Oct 2026, before any tuning was run)

Companion file: linaige_retune_protocol.json (the exact search spaces and settings; its sha256 is recorded by the scripts). Commit and push both files BEFORE running `linaige_retune.py --tune`.

## 1. Why this exists

The one-shot LINAIGE run (linaige_protocol.md + amendment 1) used the frozen v1.4 parameters, which were tuned on a corner-mounted sensor in one study pod. They did not transfer to LINAIGE's ceiling-mounted AMG8833 (pooled total error: Ours-v1 71.0 %, Ours-v2 50.1 %, B-paper 61.1 %, B-code 53.5 %). That result stays in the paper unchanged.

This follow-up asks one more question: can the four methods adapt to the new geometry when each is tuned on LINAIGE data with the same budget? It is a declared analysis made AFTER the frozen run, not a replacement for it.

## 2. What has already been seen (stated so nobody has to guess)

- Frozen-parameter results on all five sessions, including Sessions 2-5, are known (linaige_results.md). Session 2 was the easiest session for every method; Session 4 the hardest.
- The file names, label counts, timing, trivial references (always-1: 43.2 % exact, always-0: 23.8 %) and the 'h' (hard) frame share are known.
- Nothing has been tuned on LINAIGE. No LINAIGE frame has been looked at beyond the above.
- The frozen results on Sessions 2-5 were seen, but they are not used to choose anything in this protocol. Tuning touches Session 1 only.

## 3. Split

- Tune on: all Session 1 stretches (10 stretches of at least 60 s, produced by linaige_run.py --convert-only under amendment 1).
- Test on: Sessions 2, 3, 4, 5 (5 stretches, 6,153 frames before warm-up and 'h' removal). One scored run.
- This follows the idea of the LINAIGE papers' own split by session (tune on one session, test on the rest). I have not checked how those papers split exactly, so the paper must say "a session-based split in the style of the LINAIGE papers", nothing stronger.
- The room of each session comes from the file names (RoomA, RoomB, ...). If Session 1 shares its room with a test session, that session is a weaker test of a new room. The results file reports sessions separately and, with --raw, names their rooms. The paper must state which test sessions are in Session 1's room.
- The test is small: 5 stretches. Intervals will be wide. The pooled number is the headline; per-session numbers are descriptive only.

## 4. Scoring (same as the frozen run, with one change in weighting)

- Truth = people_number. 30 s warm-up inside every stretch. Frames with confidence 'h' stay in the stream but are not scored.
- Error = false % + missed % of the smoothed count, pooled over all scored frames of the training stretches (frame-weighted, the same weighting as the test table; the earlier tuning weighted streams equally, which would give a 60 s stretch the same weight as a 1,000 s one here).
- Tie-break: within 0.10 points of the best total error, lower worst-single-stretch error (only stretches with at least 300 scored frames count); then lower trial index.
- Baselines get dht = frame median + 1.2 C, as in the frozen run (assumption).

## 5. Search spaces and budget

Identical to tuning protocol v1.4 for all four methods (same ranges, 300 stage-1 + 5 x 60 stage-2 = 600 trials per method, same samplers), with these declared changes:

1. dht_offset (B-paper and B-code): v1.4 allowed 0.0, 0.1, 0.2. With dht = median + 1.2 C, that places the baseline threshold only 1.2-1.4 C above the frame median, while Ours can reach 0.3-2.5 C through `contrast`. The choices are widened to {-0.9, -0.6, -0.3, 0.0, 0.1, 0.2, 0.5, 1.0, 1.3}, which gives the baselines the same reachable threshold range (0.3-2.5 C). Without this the baselines would lose because of the search space, not the method. The change was made before any tuning and is a courtesy to the baselines.
2. New random seed (20261024), so stage-1 samples are new.
3. Ours-v1/Ours-v2 `window_s` stays capped at 12 s (operational limit: detection delay).
4. B-code as published (bcode_asis) is not re-tuned.

Edge rule: a winner on a non-natural, non-operational range end is reported as "edge-limited". It does NOT trigger a second round. There is no second round: this is the only re-tune on LINAIGE.

## 6. Procedure and freeze

1. Commit + push linaige_retune_protocol.md and .json. (Dated record on GitHub.)
2. `python linaige_retune.py --tune --jobs 18` writes params_linaige_session1.json and params_linaige_session1.sha256. Commit + push both, together with linaige_retune_tuning.md.
3. `python linaige_retune.py --test --jobs 18 --raw "<linaige folder>"` is the one scored run on Sessions 2-5. It refuses to run if the params file was edited after tuning or if the lock exists. Output: linaige_retune_results.md and linaige_retune_test.lock.
4. Nothing is changed after step 3. Whatever the numbers are, they go into the paper.

## 7. What is reported

- For each method, two arms on Sessions 2-5: frozen v1.4 parameters (recomputed; must equal the corresponding rows of linaige_results.md) and Session-1-tuned parameters.
- Total error, MAE, exact-count %, occupied F1, BAS, each with a 20 s block-bootstrap interval (2,000 resamples, paired across arms); the trivial references (always 1, always 0).
- Paired change from re-tuning per method; paired differences between methods; per-session table; table by true count; in-sample Session-1 errors next to the frozen parameters' Session-1 errors.

## 8. How the outcomes will be worded (decided now)

- If a method's tuned arm clearly beats its frozen arm AND the trivial references on Sessions 2-5: "adapts to the ceiling-mounted geometry after a re-tune on one session".
- If it does not beat the trivial references (for example always answering 1): "does not count people reliably at 8x8 from a ceiling mount in this data, with or without re-tuning". This is a limitation of 8x8 counting in this data, not necessarily of one method; the other methods are read the same way.
- No claim about generalising to unseen rooms beyond what the room names in the results support.
- The paper labels this section "declared follow-up, tuned on Session 1".

## 9. Limitations to state

Small test set (5 stretches); Session 1 may share a room with some test sessions; 'h' frames assumed hard to label; baseline dht is an assumption; people close together merge at 8x8; one tuning run (no repeat seeds); stretches start mid-recording.
