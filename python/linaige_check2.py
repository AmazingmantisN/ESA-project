"""LINAIGE first look, part 2: timing and ordering only (no filter is run, nothing is scored).
Timestamps in LINAIGE are 'HH_MM_SS.ffffff' (time of day). This reads them properly and answers: are the files in time order,
what is the real frame rate, where are the gaps, and how much data sits in continuous stretches of at least 60 s.

  python linaige_check2.py "C:\\VIT life\\Project\\linaige"
Paste the whole printout back.
"""
import os, sys
import numpy as np, pandas as pd

root = sys.argv[1] if len(sys.argv) > 1 else "."
files = sorted(f for f in os.listdir(root) if f.lower().endswith(".csv"))

def to_sec(s):
    h, m, x = str(s).split("_"); return int(h) * 3600 + int(m) * 60 + float(x)

def stretches(t, med, min_len=60.0):
    """split where the step is > 3 x median or negative; return (n stretches >= min_len, frames in them, seconds in them, longest s)"""
    dt = np.diff(t); cut = np.flatnonzero((dt > 3 * med) | (dt <= 0)) + 1
    segs = np.split(np.arange(len(t)), cut); keep = [s for s in segs if len(s) > 1 and t[s[-1]] - t[s[0]] >= min_len]
    return len(keep), sum(len(s) for s in keep), sum(t[s[-1]] - t[s[0]] for s in keep), max([t[s[-1]] - t[s[0]] for s in keep], default=0.0)

for f in files:
    d = pd.read_csv(os.path.join(root, f)); t = np.array([to_sec(x) for x in d.timestamp], float)
    print(f"\n== {f}: {len(d)} rows")
    back = np.diff(t) < 0; print(f"   FILE ORDER: backward steps {back.sum()}; first {d.timestamp.iloc[0]}, last {d.timestamp.iloc[-1]}")
    if (np.diff(t) < -43200).any(): t = np.where(np.arange(len(t)) >= np.argmax(np.diff(t) < -43200) + 1, t + 86400, t); print("   (midnight wrap corrected)")
    for label, tt, idx in (("file order", t, np.arange(len(t))), ("sorted by time", np.sort(t), np.argsort(t, kind="stable"))):
        dt = np.diff(tt); pos = dt[dt > 0]
        if len(pos) == 0: print(f"   [{label}] no positive steps"); continue
        med = np.median(pos); n, fr, sec, lg = stretches(tt, med)
        print(f"   [{label}] step median {med:.3f} s (~{1 / med:.1f} Hz), p5 {np.percentile(pos, 5):.3f}, p95 {np.percentile(pos, 95):.3f}, max {dt.max():.2f}; "
              f"steps > 3x median: {(dt > 3 * med).sum()}; zero/negative: {(dt <= 0).sum()}")
        print(f"      continuous stretches >= 60 s: {n}, holding {fr} frames ({fr / len(d) * 100:.0f}% of rows), {sec:.0f} s, longest {lg:.0f} s")
    y = d.people_number.values; ys = y[np.argsort(t, kind="stable")]
    print(f"   label changes: file order {int((np.diff(y) != 0).sum())}, sorted order {int((np.diff(ys) != 0).sum())} (few = labels follow time, many = shuffled or noisy)")
    c = d.confidence; print(f"   confidence: dtype {c.dtype}; unique values {c.nunique()}; first values {list(c.head(5))}; most common {c.value_counts().head(5).to_dict()}")
    cn = pd.to_numeric(c, errors="coerce")
    if cn.notna().any(): print(f"      numeric part: min {cn.min():.3g}, median {cn.median():.3g}, max {cn.max():.3g}; non-numeric or empty: {int(cn.isna().sum())}")
    th = d.thermistor; print(f"   thermistor: median {th.median():.2f}, range {th.min():.2f}-{th.max():.2f}")
print("\nDone.")
