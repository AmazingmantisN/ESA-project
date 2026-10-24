"""Free consistency check: protocol v1.3 must not have changed anything about the 10 original dev streams.

Stage 1 uses the same seed and spaces in v1.2 and v1.3, so every stage-1 trial must have identical parameters, and its score on the 10 ORIGINAL dev streams
(tot_dev_* columns, not dev_rob_*) must equal its v1.2 score. A mismatch means the tool, the data or the sampler changed between versions.

  python check_v13_vs_v12.py                                  # ../tuning_results (v1.2) vs ../tuning_results_v13
  python check_v13_vs_v12.py --new DIR --old DIR
Exit code 0 = all entries match. Writes nothing.
"""
import argparse, glob, os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ap = argparse.ArgumentParser(); ap.add_argument("--old", default=os.path.join(ROOT, "tuning_results")); ap.add_argument("--new", default=os.path.join(ROOT, "tuning_results_v13")); a = ap.parse_args()
bad = 0; n_entries = 0
for fn in sorted(glob.glob(os.path.join(a.new, "trials_*.csv"))):
    entry = os.path.basename(fn)[7:-4]; old_fn = os.path.join(a.old, os.path.basename(fn))
    if not os.path.exists(old_fn): print(f"{entry:11s} SKIPPED (no v1.2 file)"); continue
    new = pd.read_csv(fn); old = pd.read_csv(old_fn); n_entries += 1
    new = new[new.stage == 1].set_index("trial"); old = old[old.stage == 1].set_index("trial"); ids = sorted(set(new.index) & set(old.index))
    orig = [c for c in new.columns if c.startswith("tot_dev_") and not c.startswith("tot_dev_rob_")]
    knobs = [c for c in new.columns if c in old.columns and not c.startswith("tot_") and c not in ("stage", "false", "missed", "total", "worst", "total_orig", "total_rob")]
    p_err = 0.0
    for c in knobs:
        if not pd.api.types.is_numeric_dtype(new[c]): p_err += float((new.loc[ids, c] != old.loc[ids, c]).sum())
        else: p_err += float(np.abs(new.loc[ids, c].astype(float) - old.loc[ids, c].astype(float)).max())
    s_err = float(np.abs(new.loc[ids, orig].values - old.loc[ids, orig].values).max()) if ids else float("inf")
    t_err = float(np.abs(new.loc[ids, orig].mean(axis=1).values - old.loc[ids, "total"].values).max()) if ids else float("inf")
    ok = bool(ids) and p_err < 1e-6 and s_err < 2e-3 and t_err < 2e-3; bad += (not ok)
    print(f"{entry:11s} {'PASS' if ok else 'FAIL'}  {len(ids)} stage-1 trials, {len(orig)} original streams; max param diff {p_err:.1e}, max per-stream score diff {s_err:.1e}, max total diff {t_err:.1e}")
print("ALL MATCH: v1.3 reproduces v1.2 on the original streams" if bad == 0 and n_entries else "MISMATCH or nothing compared: do not trust the v1.3 sweep until explained")
sys.exit(0 if bad == 0 and n_entries else 1)
