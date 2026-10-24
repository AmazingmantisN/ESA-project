v26 package (24 Oct 2026): LINAIGE declared re-tune (tune on Session 1, test on Sessions 2-5).

Unzip into C:\VIT life\Project\thermal_poc\thermal_poc so that:
  python\linaige_retune.py          sits next to python\tune_sweep.py
  linaige_retune_protocol.json      in the project root
  linaige_retune_protocol.md        in the project root

Needs: linaige_streams\ (already there from the last run), pc_test\run_pc.exe, params_frozen.json. Use FULL paths in PowerShell (no "...").

STEP 0 - written plan first (this is what makes it a dated record):
  cd "C:\VIT life\Project\thermal_poc\thermal_poc"
  git add linaige_retune_protocol.md linaige_retune_protocol.json
  git commit -m "LINAIGE re-tune protocol L1.0 (before tuning)"
  git push
  (Look at the git output: it must say it pushed. Do not run step 1 before this.)

STEP 1 - tune on Session 1 only (expect 10-30 min on your laptop):
  cd "C:\VIT life\Project\thermal_poc\thermal_poc\python"
  python linaige_retune.py --tune --jobs 18
  Paste back the printed lines starting with "==" (four lines) and the sha256.
  Optional smoke test first, 10 seconds: add --quick (writes *_QUICK files, uses nothing up).

STEP 2 - record the tuned parameters BEFORE testing:
  cd "C:\VIT life\Project\thermal_poc\thermal_poc"
  git add params_linaige_session1.json params_linaige_session1.sha256 linaige_retune_tuning.md
  git commit -m "LINAIGE re-tune: Session-1 parameters (before testing on Sessions 2-5)"
  git push

STEP 3 - the one scored run on Sessions 2-5 (a few minutes):
  cd "C:\VIT life\Project\thermal_poc\thermal_poc\python"
  python linaige_retune.py --test --jobs 18 --raw "C:\VIT life\Project\linaige"
  (--raw is the folder with the original LINAIGE csv files; it is only used to print each session's room.)
  Paste back linaige_retune_results.md.
  Sanity check: the "(frozen)" rows per session must equal the matching rows of linaige_results.md.

The script refuses to tune after the test, refuses to test twice, and refuses if params_linaige_session1.json was edited. If the test crashes before it prints results, it did not use up the run.
