"""Step 1 of the LINAIGE transfer test: LOOK at the data only. No method is run, nothing is scored.

Download LINAIGE from Kaggle (kaggle.com/datasets/francescodaghero/linaige, free account), unzip it anywhere, then:
  python linaige_check.py "C:\\path\\to\\linaige"
Paste the printed summary back. It tells us whether the files are continuous time sequences (needed for persistence filters),
which column holds the people count, the pixel units, and the frame rate, so the converter can be written correctly.
"""
import os, sys, re
import numpy as np, pandas as pd

root = sys.argv[1] if len(sys.argv) > 1 else "."
files = [os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs]
print(f"{len(files)} files under {root}")
for f in sorted(files)[:40]: print(f"  {os.path.relpath(f, root)}  ({os.path.getsize(f) / 1e6:.2f} MB)")
csvs = [f for f in files if f.lower().endswith((".csv", ".txt"))]
for f in sorted(csvs):
    try: d = pd.read_csv(f)
    except Exception as e: print(f"\n== {os.path.relpath(f, root)}: cannot read as CSV ({e})"); continue
    print(f"\n== {os.path.relpath(f, root)}: {len(d)} rows x {d.shape[1]} columns")
    print("   first columns:", list(d.columns[:12]), "..." if d.shape[1] > 12 else "")
    print("   last columns:", list(d.columns[-6:]))
    num = d.select_dtypes("number")
    pix = [c for c in num.columns if re.fullmatch(r"(p|pix|pixel)?_?\d+", str(c).lower())]
    if len(pix) >= 64:
        v = num[pix[:64]].values; print(f"   64 pixel-like columns found; values min {v.min():.2f} median {np.median(v):.2f} max {v.max():.2f} (deg C if ~15-40)")
        fmax = v.max(1) - np.median(v, 1); print(f"   frame max - median: median {np.median(fmax):.2f}, p95 {np.percentile(fmax, 95):.2f}")
    for c in d.columns:
        lc = str(c).lower()
        if any(k in lc for k in ("label", "count", "people", "person", "target", "class", "y")) and d[c].nunique() < 20:
            print(f"   candidate label column '{c}': counts {d[c].value_counts().sort_index().to_dict()}")
        if any(k in lc for k in ("time", "stamp", "date", "frame", "idx", "index", "session")):
            s = d[c]; print(f"   time/index column '{c}': first {s.iloc[0]}, last {s.iloc[-1]}, unique {s.nunique()}")
            try:
                if pd.api.types.is_numeric_dtype(s): dt = np.diff(s.values.astype(float)); unit = "(column units)"
                else: dt = np.diff(pd.to_datetime(s).values).astype("timedelta64[ms]").astype(float) / 1000; unit = "s"
                dt = np.asarray(dt, float); print(f"      step unit {unit}"); print(f"      step: median {np.median(dt):.4g}, max {dt.max():.4g}, steps > 3x median: {(dt > 3 * np.median(dt)).sum()}")
            except Exception as e: print(f"      (could not compute steps: {e})")
print("\nDone. Paste everything above into the chat.")
