# LINAIGE transfer test: protocol (written 24 Oct 2026, before any LINAIGE file was opened)

Purpose: check whether the frozen filters work in other rooms, with other people, a ceiling mount and 10 Hz, without re-tuning.
This is a transfer test, not a benchmark win: LINAIGE has no placed heat sources, and its people mostly stand and walk.

1. Parameters: exactly params_frozen.json (sha256 01f4fcc8...). No re-tuning, no per-session settings, no change after seeing results.
2. Methods: Ours-v1, Ours-v2, B-paper, B-code. B-paper and B-code need a DHT reading that LINAIGE does not have; they get
   DHT = frame median + 1.2 deg C (the offset measured in Papanashi's pod) and this is stated as an assumption.
3. Frame rate: the measured rate of each file (expected 10 Hz). All time parameters are already in seconds.
4. Sequences: only stretches that are continuous in time are used. A gap longer than 3 x the median frame step starts a new stretch.
   Stretches shorter than 60 s are dropped. The 30 s warm-up applies to each stretch.
5. Truth: the LINAIGE per-frame count. Frames marked hard-to-label (if marked) are dropped from scoring but kept in the stream.
6. Metrics: total error (false% + missed%), exact-count accuracy, MAE, occupied F1, balanced accuracy; per session and by true count
   (0, 1, 2, 3+). 95 % intervals by 20 s moving-block bootstrap within stretches.
7. Reporting: every result is reported, whatever it shows, in a separate section of the paper labelled "transfer test, untuned".
   Known expected failure: counts of 2 or more people close together under an 8x8 ceiling sensor, where blobs merge.
8. The run is done once. Any later change (for example a re-tuned variant) is a new, declared analysis and does not replace this one.
