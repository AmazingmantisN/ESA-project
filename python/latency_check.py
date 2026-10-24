"""Detection-delay report (protocol v1.4; REPORT ONLY, not part of the tuning score).

Why: a track is not counted until its history window fills, so a long window_s means a late count; dev scoring ignores this because the dev slices are long.
Test: splice = last 60 s of dev_empty_clean followed by the first 150 s of dev_single_clean (labels 0, then 1). For every winner:
  delay_s     time from the splice until the smoothed count is >= 1 for 5 s in a row (blank = never within 150 s)
  empty_fa_%  % of frames in the empty part (after the 30 s warm-up) with smoothed count > 0
  after_ok_%  % of frames in the last 60 s of the single part with smoothed count == 1
  ambient     |median pixel step| at the splice in degC (the two slices are different sessions; a large step can confound the delay)
CAVEAT: the person is already seated when the single slice starts, so this measures the delay of a fidgeting person who suddenly appears in view,
not of a person walking in. Indicative only; the real entry delay is a Step 10 measurement.

  python latency_check.py v1.3=../tuning_results_v13/tune_candidates.json v1.4=../tuning_results_v14/tune_candidates.json [--md ../latency_report.md]
Reads dev_empty_clean / dev_single_clean only. Writes data/latency/splice.csv (outside data/streams, so no tuning glob can see it).
"""
import argparse, csv, io, json, math, os, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path.insert(0, HERE)
import tune_sweep as T
ap = argparse.ArgumentParser(); ap.add_argument("cands", nargs="+", help="label=path to tune_candidates.json"); ap.add_argument("--md", default=os.path.join(ROOT, "latency_report.md"))
ap.add_argument("--protocol", default=os.path.join(ROOT, "tuning_protocol_v1.4.json")); a = ap.parse_args()
T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.abspath(a.protocol)); EXE = T.G["EXE"]
src = os.path.join(ROOT, "data", "streams"); out = os.path.join(ROOT, "data", "latency"); os.makedirs(out, exist_ok=True)

def load(name):
    rows = list(csv.reader(open(os.path.join(src, name + ".csv")))); return rows[0], rows[1:], float(json.load(open(os.path.join(src, name + ".json"))).get("fps") or 3.8)
he, be, fps = load("dev_empty_clean"); hs, bs, fps2 = load("dev_single_clean"); assert he == hs; fps = fps2    # the slices differ slightly (3.88 vs 3.79 fps); the splice uses the single-person fps, so the 60 s empty part is ~2 % off in time, the measured delay is exact
En, Sn = int(60 * fps), int(150 * fps); E = be[-En:]; S = bs[:Sn]
with open(os.path.join(out, "splice.csv"), "w", newline="") as f:
    f.write(",".join(he) + "\n")
    for i, r in enumerate(E + S):
        r = list(r); r[0] = str(i); r[1] = "0" if i < En else "1"; f.write(",".join(r) + "\n")
json.dump({"fps": fps, "note": "splice of dev_empty_clean (last 60 s) + dev_single_clean (first 150 s)"}, open(os.path.join(out, "splice.json"), "w"))
p0 = he.index("p0"); a_e = np.array([[float(v) for v in r[p0:p0 + 64]] for r in E[-20:]]); a_s = np.array([[float(v) for v in r[p0:p0 + 64]] for r in S[:20]])
amb = abs(float(np.median(a_s) - np.median(a_e))); hold = math.ceil(5 * fps); warm = math.ceil(30 * fps)

L = [f"# latency_report.md (splice test; REPORT ONLY; fps {fps:.2f}; ambient step at the splice {amb:.2f} C)", "",
     "| Set | Entry | window_s | delay_s | empty_fa_% | after_ok_% |", "|---|---|---|---|---|---|"]
for item in a.cands:
    label, path = item.split("=", 1)
    for e, c in json.load(open(path))["candidates"].items():
        if e == "bcode_asis" or e not in T.G["P"]["entries"]: continue
        r = subprocess.run([EXE, "--stream", os.path.join(out, "splice.csv"), "--fps", str(fps)] + T.args_for(e, c["params"]), capture_output=True, text=True)
        if r.returncode: sys.exit(f"run_pc failed for {e}: {r.stderr[:200]}")
        sm = pd.read_csv(io.StringIO(r.stdout)).smooth.values; hit = None
        for i in range(En, len(sm) - hold + 1):
            if (sm[i:i + hold] >= 1).all(): hit = (i - En) / fps; break
        fa = float((sm[warm:En] > 0).mean() * 100); ok = float((sm[-int(60 * fps):] == 1).mean() * 100)
        win = c["params"].get("window_s"); L.append(f"| {label} | {e} | {'%.2f' % win if win is not None else 'n/a'} | {'%.1f' % hit if hit is not None else 'never'} | {fa:.1f} | {ok:.1f} |")
L += ["", "delay_s: seconds until the count reaches >= 1 for 5 s after a person appears; 'never' = not within 150 s. Ours window_s is the structural minimum for Ours-v1/v2."]
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", a.md)
