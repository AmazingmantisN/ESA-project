# LINAIGE transfer test: amendment 1 (written 24 Oct 2026, after the timing look, before any filter was run on LINAIGE)

What was seen before this amendment: file names, columns, label counts and timing only (linaige_check.py, linaige_check2.py). No method was run and nothing was scored.

Seen: 5 sessions, 31,036 rows, true 10 Hz, files in time order except Session 3 (one backward step), many gaps (up to 2,361 s).
Rows inside unbroken stretches of at least 60 s: S1 10,293 (10 stretches), S2 1,774 (1), S3 616 (1), S4 2,399 (2), S5 1,364 (1): 16,446 frames, about 1,650 s, 15 stretches.

Decisions (they complete linaige_protocol.md; nothing in it is relaxed):
1. Each file is sorted by timestamp (stable). This only affects Session 3 and does not change its stretches.
2. A stretch ends where the step between frames exceeds 3 x the median step (0.1 s). Stretches shorter than 60 s are dropped.
3. The 30 s warm-up applies inside every stretch, so about 450 s of the 1,650 s are never scored.
4. The 'confidence' column holds 'e' and 'h'. Assumption: 'h' marks frames that were hard to label (the dataset paper excludes such frames). They stay in the stream, so the filters see continuous data, but they are not scored. 'h' is 21% of Session 1 rows.
5. Truth is people_number (0-3). The filters count blobs, so counts of 2 or 3 people standing close together are expected to fail; this is reported by true count, not hidden.
6. B-paper and B-code get dht = frame median + 1.2 C per frame (Papanashi's pod offset). LINAIGE has a thermistor column (about 30 C, 4-5 C above the scene median), which is not a room-temperature reference; a thermistor-based baseline is NOT part of this run and could only be added later as a separate, declared extra.
7. Frozen parameters only (params_frozen.json, sha256 01f4fcc8...). No re-tuning, not even for the ceiling mount.
8. One scored run. linaige_run.py refuses to run if linaige_run.lock exists. A crash before results are written does not use up the run; a rerun after seeing results would be a new, declared analysis.
9. Whatever the results are, they go into the paper in a section labelled "transfer test, untuned".
10. Known limitation to state: stretches start mid-recording, so people may already be in the room when a stretch starts. Ours-v2's origin gate cannot have seen them arrive, and Ours-v1 needs its 12 s window to fill. These are properties of the methods, not corrected for.
