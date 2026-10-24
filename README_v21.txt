PROTOCOL v2.1 (re-tune only, no Ours-v3) - drop-in files for your thermal_poc folder. Needs your v1.4 run done (..\tuning_results_v14\tune_candidates.json).

Question it answers: Ours-v2 looked great on real streams but weak on synthetic ones. Was that just because it was tuned on the 26 real streams only?
It re-tunes Ours-v1, Ours-v2, B-paper, B-code and B-code-as-published with equal effort (600 trials each) on 10 real + 16 robustness + 80 synthetic dev streams. Nothing is frozen.

1. Unzip over your thermal_poc folder (the one with python\, firmware\, pc_test\, data\), choose Replace/merge.
   Replaced: python\tune_sweep.py, python\robust_check.py, firmware\thermal_poc\persistence_filter.h + thermal_poc.ino, pc_test\run_pc.cpp + test_modes.cpp.
   New: tuning_protocol_v2.1.json/.md, python\tune_sweep_v2.py, run_v21.py, check_v21_rescore.py, data\synth\dev\ (80 streams, 35 MB), data\synth\dev_manifest.json.
   (The zip also holds the unused v2.0/Ours-v3 files; ignore them.)
2. In cmd from the python folder:
     python run_v21.py --quick --jobs 18      (about 3-5 min smoke test, NOT the protocol run; expect all PASS)
     python run_v21.py --jobs 18              (official run, roughly 35-60 min; leave the laptop alone and plugged in)
3. Paste summary_v21.md back. Do not edit tuning_protocol_v2.1.json/.md before the official run (hashes are recorded).
4. The ESP32 sketch changed (extra fields, inert by default). Reflash thermal_poc.ino before any later ESP32 check.
