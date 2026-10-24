"""Tune on DEV streams, then evaluate ONCE on TEST streams. All time parameters in SECONDS.

Mode 1 - sweep (dev only):
  python sweep.py "../data/streams/dev_*.csv"
  Ranks (window_s, drift, contrast) by mean error over the dev streams (each stream weighted equally).

Mode 2 - final evaluation (run once, after you froze the parameters):
  python sweep.py --evaluate "../data/streams/test_*.csv" --window_s 3 --drift 0.25 --contrast 1.75
  Prints a per-stream table. Do not tune on these numbers (that would be reporting training error).

Frame rate for the seconds->frames conversion is read from each stream's .json sidecar
(written by make_stream.py); fallback 3.8 Hz. Quote patterns so cmd does not expand them.

  window_s     history length for the persistence test (seconds)
  drift        centroid extent (source px) below which a blob is called static
  contrast     min degC above the frame median for a pixel to count as hot
  k            threshold = median + k * (1.4826 * MAD) but never below median + contrast.
               Matters a lot on this data: a seated person plus a hot source cover so many of the
               64 pixels that MAD inflates, and with k=3 the threshold rises above the person.
"""
import argparse, glob, io, itertools, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = next((p for p in (os.path.join(HERE, "..", "pc_test", n) for n in ("run_pc.exe", "run_pc")) if os.path.exists(p)), None)
if EXE is None: sys.exit("run_pc not found in ../pc_test: build it first (g++ -O2 -std=c++17 -o run_pc run_pc.cpp)")

def fps_of(stream):
    try: return float(json.load(open(stream[:-4] + ".json"))["fps"])
    except Exception: return 3.8

def run(stream, window_s, drift, contrast, smooth_s, maxmissed_s, k=3.0):
    fps = fps_of(stream)
    out = subprocess.run([EXE, "--stream", stream, "--fps", str(fps), "--window_s", str(window_s),
                          "--maxmissed_s", str(maxmissed_s), "--smooth_s", str(smooth_s),
                          "--drift", str(drift), "--contrast", str(contrast), "--k", str(k)],
                         capture_output=True, text=True, check=True).stdout
    d = pd.read_csv(io.StringIO(out))
    warm = int(window_s * fps + smooth_s * fps) + 2            # filter needs a full window first
    d = d.iloc[warm:]
    return (d.smooth > d.humans).mean() * 100, (d.smooth < d.humans).mean() * 100, len(d)

ap = argparse.ArgumentParser()
ap.add_argument("dev", nargs="?", help='glob of DEV streams, e.g. "../data/streams/dev_*.csv"')
ap.add_argument("--evaluate", help="glob of TEST streams (needs fixed parameters below)")
ap.add_argument("--k", type=float, default=3.0); ap.add_argument("--window_s", type=float); ap.add_argument("--drift", type=float); ap.add_argument("--contrast", type=float)
ap.add_argument("--smooth_s", type=float, default=1.3); ap.add_argument("--maxmissed_s", type=float, default=2.5)
ap.add_argument("--top", type=int, default=12)
a = ap.parse_args()

if a.evaluate:
    if None in (a.window_s, a.drift, a.contrast): sys.exit("--evaluate needs --window_s --drift --contrast")
    files = sorted(glob.glob(a.evaluate)) or sys.exit("no streams match " + a.evaluate)
    print(f"FINAL EVALUATION  window_s={a.window_s} drift={a.drift} contrast={a.contrast} k={a.k} smooth_s={a.smooth_s} maxmissed_s={a.maxmissed_s}")
    tot_f = tot_m = 0
    for f in files:
        fa, ms, n = run(f, a.window_s, a.drift, a.contrast, a.smooth_s, a.maxmissed_s, a.k)
        print(f"  {os.path.basename(f)[:-4]:28s} frames {n:5d}  false {fa:6.2f}%  missed {ms:6.2f}%")
        tot_f += fa / len(files); tot_m += ms / len(files)
    print(f"  {'MEAN over streams':28s}              false {tot_f:6.2f}%  missed {tot_m:6.2f}%  total {tot_f + tot_m:6.2f}%")
    sys.exit(0)

if not a.dev: sys.exit(__doc__)
files = sorted(glob.glob(a.dev)) or sys.exit("no streams match " + a.dev)
if any("test_" in os.path.basename(f) for f in files): sys.exit("refusing to tune on test_* streams (use --evaluate once, after freezing parameters)")
def one(args):
    w, dr, ct, k = args
    fa = ms = 0.0
    for s in files:
        f_, m_, _ = run(s, w, dr, ct, a.smooth_s, a.maxmissed_s, k)
        fa += f_ / len(files); ms += m_ / len(files)
    return (w, dr, ct, k, fa, ms, fa + ms)

grid = list(itertools.product([2, 4, 6], [0.1, 0.16, 0.25, 0.4, 0.6, 0.8, 1.0], [1.0, 1.25, 1.5, 1.75, 2.0], [0.5, 1.0, 2.0, 3.0]))
print(f"{len(grid)} parameter combinations x {len(files)} streams (parallel) ...")
with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
    rows = list(ex.map(one, grid))
df = pd.DataFrame(rows, columns=["window_s", "drift", "contrast", "k", "false%", "missed%", "total_err%"])
best = df.sort_values("total_err%").head(a.top)
print(best.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
edges = []
if best.iloc[0].drift in (0.1, 1.0): edges.append("drift")
if best.iloc[0].contrast in (1.0, 2.0): edges.append("contrast")
if best.iloc[0].k in (0.5, 3.0): edges.append("k")
if best.iloc[0].window_s in (2, 6): edges.append("window_s")
if edges: print("NOTE: best row is on the edge of the grid for: " + ", ".join(edges) + " -> widen that range in sweep.py and rerun.")
