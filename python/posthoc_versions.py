"""DECLARED POST-HOC table: 'price of robustness' - the winners of protocol v1.2, v1.3 and v1.4 side by side on the held-out test_* streams.

Status: test_* was already used once for the frozen v1.4 winners (test_results.md). This script scores the OTHER versions' winners on the same streams AFTER that, so it is
descriptive only: it cannot change the frozen choice (v1.4) and must be labelled post-hoc in the paper. Nothing is tuned. Writes only the md/csv given (no lock touched).
Dev columns come from the candidate files (v1.2 scored 10 dev streams, v1.3/v1.4 26; only 'original-10' is comparable across versions).

  python posthoc_versions.py v1.2=../tuning_results/tune_candidates.json v1.3=../tuning_results_v13/tune_candidates.json v1.4=../tuning_results_v14/tune_candidates.json
         [--glob ../data/streams/test_*.csv] [--md ../posthoc_versions.md]
"""
import argparse, glob, io, json, math, os, subprocess, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T
ap = argparse.ArgumentParser(); ap.add_argument("cands", nargs="+"); ap.add_argument("--glob", default=os.path.join(ROOT, "data", "streams", "test_*.csv")); ap.add_argument("--md", default=os.path.join(ROOT, "posthoc_versions.md")); a = ap.parse_args()
T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.join(ROOT, "tuning_protocol_v1.4.json"))
files = sorted(glob.glob(a.glob)); names = [os.path.basename(f)[:-4] for f in files]; assert files, "no streams"
fps = {f: float(json.load(open(f[:-4] + ".json")).get("fps", 3.8)) for f in files}; warm_s = T.G["P"]["scoring"]["warmup_s"]
def raw(e, prm, f):
    r = subprocess.run([T.G["EXE"], "--stream", f, "--fps", str(fps[f])] + T.args_for(e, prm), capture_output=True, text=True)
    if r.returncode: sys.exit(f"run_pc failed: {r.stderr[:200]}")
    d = pd.read_csv(io.StringIO(r.stdout)).iloc[math.ceil(warm_s * fps[f]):]; return (d.smooth.values > d.humans.values).astype(float), (d.smooth.values < d.humans.values).astype(float)
rng = np.random.default_rng(20261025); B = 2000; idx = {}
for i, f in enumerate(files):
    n = len(raw("ours", {"window_s": 4, "drift": .6, "contrast": 1.2, "k": .2, "smooth_s": 1.3, "maxmissed_s": 1.0}, f)[0]); blk = max(2, int(20 * fps[f])); nb = math.ceil(n / blk)
    idx[i] = (rng.integers(0, max(1, n - blk + 1), size=(B, nb))[:, :, None] + np.arange(blk)[None, None, :]).reshape(B, -1)[:, :n]
rows = []; boots = {}
for item in a.cands:
    ver, path = item.split("=", 1); C = json.load(open(path))["candidates"]
    for e in ("ours", "ours_v2", "bcode", "bpaper"):
        if e not in C: continue
        R = [raw(e, C[e]["params"], f) for f in files]; tot = np.array([(x.mean() + y.mean()) * 100 for x, y in R])
        bt = np.mean([(R[i][0][idx[i]].mean(1) + R[i][1][idx[i]].mean(1)) * 100 for i in range(len(files))], axis=0); lo, hi = np.percentile(bt, [2.5, 97.5]); boots[(ver, e)] = bt
        rows.append(dict(ver=ver, entry=e, total=tot.mean(), lo=lo, hi=hi, false=np.mean([x.mean() for x, _ in R]) * 100, missed=np.mean([y.mean() for _, y in R]) * 100,
                         dev_orig=C[e].get("dev_orig_total", C[e].get("dev_total")), dev_rob=C[e].get("dev_rob_total")))
L = [f"# posthoc_versions.md - DECLARED POST-HOC (test_* was used first for frozen v1.4; this is descriptive, the frozen choice is not revisited)", "",
     f"streams: {len(files)} from {a.glob}; error = false% + missed%, warm-up {warm_s} s; 95 % = 20 s block bootstrap ({B}); dev columns: original-10 sub-score (comparable across versions) and robustness-16 (v1.3/v1.4 only).", "",
     "| Entry | Version | Test total % [95 % CI] | False % | Missed % | Dev orig-10 | Dev rob-16 |", "|---|---|---|---|---|---|---|"]
for e in ("ours", "ours_v2", "bcode", "bpaper"):
    for r in [r for r in rows if r["entry"] == e]:
        L.append(f"| {e} | {r['ver']} | {r['total']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}] | {r['false']:.2f} | {r['missed']:.2f} | {r['dev_orig']:.2f} | " + (f"{r['dev_rob']:.2f}" if r['dev_rob'] is not None and r['dev_rob'] == r['dev_rob'] else "-") + " |")
vs = [x.split("=")[0] for x in a.cands]
if len(vs) > 1:
    L += ["", "Paired difference, test total % (later version minus earlier; negative = later is better), 95 % block-bootstrap:", "", "| Entry | Comparison | Diff [95 % CI] |", "|---|---|---|"]
    for e in ("ours", "ours_v2", "bcode", "bpaper"):
        for v0, v1 in zip(vs, vs[1:]):
            if (v0, e) in boots and (v1, e) in boots:
                d = boots[(v1, e)] - boots[(v0, e)]; m = [r for r in rows if r["entry"] == e]; t0 = [r["total"] for r in m if r["ver"] == v0][0]; t1 = [r["total"] for r in m if r["ver"] == v1][0]
                L.append(f"| {e} | {v1} - {v0} | {t1 - t0:+.2f} [{np.percentile(d, 2.5):+.2f}, {np.percentile(d, 97.5):+.2f}] |")
L += ["", "Reading: test_* is steady injected sources like dev original-10, so robustness-tuned versions (v1.3/v1.4) are expected to give up some accuracy there (R4, 'price of robustness'); the stress benefit is in robust_summary_v1x_s101/202.md."]
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
