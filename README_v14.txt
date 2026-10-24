PROTOCOL v1.4 - drop-in files for your thermal_poc folder (needs the v1.3 package already installed and your v1.3 run done)

1. Unzip over your thermal_poc folder (merge). Replaced: python\tune_sweep.py (additive: 'operational limit' edge flag; v1.2/v1.3 behaviour unchanged).
   New: tuning_protocol_v1.4.json/.md, python\run_v14.py, check_v14_rescore.py, latency_check.py.
2. In cmd from the python folder:
     python run_v14.py --quick --jobs 18      (about 1-2 min smoke test, NOT the protocol run; expect all PASS)
     python run_v14.py --jobs 18              (official run, roughly 10-15 min)
   Needs ..\tuning_results_v13\tune_candidates.json (your v1.3 run); the v1.2 columns are added if ..\tuning_results\tune_candidates.json exists.
3. Paste summary_v14.md back. A --quick run overwrites tuning_results_v14 and summary_v14.md, so run the official one last.
