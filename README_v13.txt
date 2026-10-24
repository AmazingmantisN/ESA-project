PROTOCOL v1.3 - drop-in files for your thermal_poc folder (the one containing python\, pc_test\, data\, tuning_results\)

1. Unzip over your thermal_poc folder (merge; nothing of v1.2 is deleted, results of v1.2 stay in tuning_results\).
   Replaced files (same behaviour for v1.2): python\tune_sweep.py, python\robust_check.py (seed-77 output verified byte-identical).
   New: tuning_protocol_v1.3.json/.md, python\robust_lib.py, make_robust_dev.py, check_v13_vs_v12.py, run_v13.py,
        data\streams\dev_rob_*.csv/.json (16 streams) + dev_rob_manifest.json.
   Do NOT run make_robust_dev.py (it is only the record of how the streams were made; tune_sweep checks their hashes).

2. In cmd, from the python folder:
     python run_v13.py --quick --jobs 18      (about 1 min, smoke test, NOT the protocol run; expect all PASS)
     python run_v13.py --jobs 18              (official run, roughly 10-15 min)
   Needs ..\tuning_results\tune_candidates.json from your v1.2 run to add the v1.2-vs-v1.3 columns (it is there if you ran run_all.py).

3. Paste summary_v13.md back (it is short). Close nothing else needed; no ESP32 involved.
