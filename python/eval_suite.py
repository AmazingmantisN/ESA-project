"""Evaluate the FROZEN methods on a synthetic suite (no tuning, no parameter change). Pre-registered metrics:

 PRIMARY   strict: all frames after a 30 s warm-up; error = false% (smooth > humans) + missed% (smooth < humans)   [same as the tuning score]
 SECONDARY grace : same, but frames within 15 s after any change of `humans` are excluded (judges steady-state, not the transition)
 DELAY     for each change of `humans` in the stream (found from the humans column itself, no events.csv needed):
             entry delay = seconds until smooth >= new count for 3 s in a row;  exit delay = seconds until smooth <= new count for 3 s in a row
             censored ("never") if not reached before the next change / stream end (reported as the cap, counted separately)

Input: a folder with <name>.csv (frame,humans,injected,dht,p0..p63), <name>.json ({"fps":..}) and optionally manifest.csv (column 'file' or 'name' or 'stream', plus 'scenario','seed','split').
Scenario = manifest 'scenario' if available, else the file name up to the first '_s<digits>' / trailing '_<digits>' seed tag.
Use --split to keep only some manifest splits (e.g. test). Streams whose name ends with _labels or is manifest/events are skipped.

  python eval_suite.py <folder> [--frozen ../params_frozen.json] [--split test] [--md out.md] [--csv out.csv] [--jobs N]
Writes only the md/csv given. Exits if params_frozen.json is missing (this tool never tunes).
"""
import argparse, io, json, math, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T

ap = argparse.ArgumentParser(); ap.add_argument("folder"); ap.add_argument("--frozen", default=os.path.join(ROOT, "params_frozen.json"))
ap.add_argument("--split", default=None); ap.add_argument("--md", default="eval_suite.md"); ap.add_argument("--csv", default="eval_suite.csv"); ap.add_argument("--jobs", type=int, default=4)
ap.add_argument("--methods", default="ours,ours_v2,bcode,bpaper,bcode_asis"); a = ap.parse_args()
if not os.path.exists(a.frozen): sys.exit("params_frozen.json not found - this tool only evaluates frozen parameters")
T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.join(ROOT, "tuning_protocol_v1.4.json"))
_J = json.load(open(a.frozen)); F = dict(_J["candidates"]); F.update(_J.get("references", {})); METHODS = [m for m in a.methods.split(",") if m in F]
WARM, GRACE, HOLD, CAP = 30.0, 15.0, 3.0, 60.0

man = None; _mf = sorted(f for f in os.listdir(a.folder) if f.endswith("manifest.csv")); mp = os.path.join(a.folder, _mf[0]) if _mf else ""
if mp:
    man = pd.read_csv(mp); key = next((c for c in ("file", "name", "stream", "filename") if c in man.columns), None)
    if key: man["_n"] = man[key].astype(str).str.replace(r"\.csv$", "", regex=True)
    else: man = None
names = sorted(f[:-4] for f in os.listdir(a.folder) if f.endswith(".csv") and not re.search(r"(_labels|_events|manifest)", f[:-4]) and os.path.exists(os.path.join(a.folder, f[:-4] + ".json")))
meta = {}
for n in names:
    sc = None; sp = None
    if man is not None and (man["_n"] == n).any():
        r = man[man["_n"] == n].iloc[0]; sc = r.get("scenario"); sp = r.get("split")
    if sc is None or (isinstance(sc, float) and math.isnan(sc)): sc = re.sub(r"(_s?\d+)+$", "", n)
    meta[n] = (str(sc), None if sp is None or (isinstance(sp, float) and math.isnan(sp)) else str(sp))
if a.split: names = [n for n in names if meta[n][1] == a.split]
if not names: sys.exit("no streams found (check folder / --split)")

def hold_hit(ok, i0, i1, hold):
    for i in range(i0, i1 - hold + 1):
        if ok[i:i + hold].all(): return i
    return None

def run(n, m):
    fps = float(json.load(open(os.path.join(a.folder, n + ".json")))["fps"]); csvp = os.path.join(a.folder, n + ".csv")
    r = subprocess.run([T.G["EXE"], "--stream", csvp, "--fps", str(fps)] + T.args_for(m, F[m]["params"]), capture_output=True, text=True)
    if r.returncode: raise RuntimeError(f"{m} on {n}: {r.stderr[:200]}")
    d = pd.read_csv(io.StringIO(r.stdout)); sm = d.smooth.values.astype(int); h = d.humans.values.astype(int); w = math.ceil(WARM * fps)
    ch = np.flatnonzero(np.diff(h) != 0) + 1                      # frames where humans changes
    keep = np.ones(len(h), bool); keep[:w] = False
    strict = ((sm > h)[keep].mean() + (sm < h)[keep].mean()) * 100
    kg = keep.copy()
    for c in ch: kg[c:c + math.ceil(GRACE * fps)] = False
    grace = ((sm > h)[kg].mean() + (sm < h)[kg].mean()) * 100 if kg.any() else float("nan")
    ev = []; hh = math.ceil(HOLD * fps)
    for k, c in enumerate(ch):
        if c < w: continue
        end = min(ch[k + 1] if k + 1 < len(ch) else len(h), c + math.ceil(CAP * fps)); up = h[c] > h[c - 1]
        ok = (sm >= h[c]) if up else (sm <= h[c]); i = hold_hit(ok, c, end, hh)
        ev.append(("entry" if up else "exit", None if i is None else (i - c) / fps))
    return dict(stream=n, scenario=meta[n][0], method=m, strict=strict, grace=grace, events=ev, injected=bool(d.injected.max()) if "injected" in d else False)

jobs = [(n, m) for n in names for m in METHODS]
with ThreadPoolExecutor(a.jobs) as ex: R = list(ex.map(lambda x: run(*x), jobs))
rows = [{k: v for k, v in r.items() if k != "events"} for r in R]; pd.DataFrame(rows).to_csv(a.csv, index=False)
df = pd.DataFrame(rows)

def table(col, title):
    p = df.pivot_table(index="scenario", columns="method", values=col, aggfunc="mean")[METHODS]; p.loc["MEAN (equal weight per scenario)"] = p.mean()
    return [f"## {title}", "", "| Scenario | " + " | ".join(METHODS) + " |", "|---|" + "---|" * len(METHODS)] + \
           [f"| {s} | " + " | ".join("%.1f" % v if v == v else "n/a" for v in p.loc[s]) + " |" for s in p.index] + [""]
L = [f"# eval_suite.md ({len(names)} streams from {a.folder}; frozen params sha in params_frozen.json; no tuning)", ""]
L += table("strict", "PRIMARY: strict error % (false + missed, all frames after 30 s)") + table("grace", "SECONDARY: error % excluding 15 s after each change in count")
dl = []
for r in R:
    for kind, d in r["events"]: dl.append(dict(scenario=r["scenario"], method=r["method"], kind=kind, delay=d))
if dl:
    D = pd.DataFrame(dl); L += ["## DELAY: median seconds to reach the new count for 3 s (cap 60 s); n = events; never = not reached", "",
        "| Scenario | kind | n | " + " | ".join(METHODS) + " |", "|---|---|---|" + "---|" * len(METHODS)]
    for (s, k), g in D.groupby(["scenario", "kind"]):
        cells = []
        for m in METHODS:
            x = g[g.method == m].delay; nv = x.isna().sum(); med = x.dropna().median()
            cells.append(("%.1f" % med if med == med else "-") + (f" ({nv} never)" if nv else ""))
        L.append(f"| {s} | {k} | {g[g.method == METHODS[0]].shape[0]} | " + " | ".join(cells) + " |")
    L.append("")
L += ["Notes: scenario means weight every scenario equally; grace/strict use `humans` as truth; delay events come from changes of the `humans` column (cross-check with events.csv by hand).",
      "Frozen methods = params_frozen.json (v1.4 winners). Reference rows: bcode_asis = the published baseline code with its published settings (tuned only for DHT offset/drift in our protocol)."]
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", a.md, a.csv)
