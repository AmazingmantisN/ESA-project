"""Declared POST-HOC, descriptive analysis (24 Oct 2026, after the literature audit). No tuning, no parameter change.
Uses only the FROZEN parameters in ../params_frozen.json. Writes count_metrics.md (and acf.png) in the project root.

What it adds to the paper (reviewers asked for these in the audit):
  A. Count-level metrics on the 10 real held-out streams (injected sources): MAE of the count, exact-count accuracy,
     occupied/vacant F1, balanced accuracy over count classes (BAS, as in the LINAIGE papers), with 95 % intervals from the
     SAME 20 s moving-block bootstrap as test_results.md (paired across methods).
  B. Block-bootstrap intervals for Table 5.1 (clean held-out windows): ours vs Papanashi's own logged output (data.csv).
  C. Autocorrelation of the per-frame error indicator, to justify the 20 s block length (acf.png).
  D. Optional (--synth FOLDER): the same count metrics on the synthetic test suite, scenarios weighted equally.

Usage (cmd, from ...\\thermal_poc\\thermal_poc\\python):
  python count_metrics.py --papanashi "..\\..\\..\\papanashi_csvs"
  python count_metrics.py --papanashi "..\\..\\..\\papanashi_csvs" --synth "<folder with syn_*.csv>" --split test --jobs 18
Truth for the real streams = the 'humans' column (session label, as in the test run). Warm-up 30 s, as everywhere else.
"""
import argparse, glob, io, json, math, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--papanashi", required=True, help="folder holding '0 persons', '1 person -Trial_1' (their csv_data/data.csv)")
ap.add_argument("--synth", default=None); ap.add_argument("--split", default="test"); ap.add_argument("--jobs", type=int, default=4)
ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--out", default=os.path.join(ROOT, "count_metrics.md"))
a = ap.parse_args()

T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.join(ROOT, "tuning_protocol_v1.4.json"))
J = json.load(open(os.path.join(ROOT, "params_frozen.json"))); F = dict(J["candidates"]); F.update(J.get("references", {}))
METHODS = ["ours", "ours_v2", "bpaper", "bcode"]; LABEL = {"ours": "Ours-v1", "ours_v2": "Ours-v2", "bpaper": "B-paper", "bcode": "B-code", "theirs": "Papanashi logged"}
WARM = 30.0; rng = np.random.default_rng(20261024)

def run(path, m, fps):
    r = subprocess.run([T.G["EXE"], "--stream", path, "--fps", str(fps)] + T.args_for(m, F[m]["params"]), capture_output=True, text=True)
    if r.returncode: sys.exit(f"run_pc failed: {m} on {os.path.basename(path)}: {r.stderr[:200]}")
    d = pd.read_csv(io.StringIO(r.stdout)); w = math.ceil(WARM * fps)
    return d.smooth.values[w:].astype(int), d.humans.values[w:].astype(int)

# ---- metrics on pooled (pred, truth) pairs ----
def mets(p, t):
    exact = (p == t).mean() * 100; mae = np.abs(p - t).mean()
    po, to = p > 0, t > 0; tp = (po & to).sum(); fp = (po & ~to).sum(); fn = (~po & to).sum()
    f1 = 2 * tp / (2 * tp + fp + fn) * 100 if (2 * tp + fp + fn) else float("nan")
    rec = [(p[t == c] == c).mean() for c in np.unique(t)]; bas = np.mean(rec) * 100
    return dict(MAE=mae, exact=exact, F1=f1, BAS=bas)
KEYS = ["MAE", "exact", "F1", "BAS"]

def block_idx(n, blk, B):
    nb = math.ceil(n / blk); s = rng.integers(0, max(1, n - blk + 1), size=(B, nb))
    return (s[:, :, None] + np.arange(blk)[None, None, :]).reshape(B, -1)[:, :n]

def boot_table(series, fps_list, title, note):
    """series: {method: [(pred, truth) per stream]} with equal-length streams across methods. Pooled frames, paired blocks."""
    ns = len(next(iter(series.values()))); idx = [block_idx(len(next(iter(series.values()))[i][0]), max(2, int(20 * fps_list[i])), a.boot) for i in range(ns)]
    L = [f"## {title}", "", note, "", "| Method | MAE (people) | Exact-count % | Occupied F1 % | BAS % |", "|---|---|---|---|---|"]
    bootv = {}
    for m, ps in series.items():
        point = mets(np.concatenate([p for p, _ in ps]), np.concatenate([t for _, t in ps]))
        bs = {k: [] for k in KEYS}
        for b in range(a.boot):
            P = np.concatenate([ps[i][0][idx[i][b]] for i in range(ns)]); Tt = np.concatenate([ps[i][1][idx[i][b]] for i in range(ns)])
            for k, v in mets(P, Tt).items(): bs[k].append(v)
        bootv[m] = bs
        cell = lambda k, f: f"{point[k]:{f}} [{np.nanpercentile(bs[k], 2.5):{f}}, {np.nanpercentile(bs[k], 97.5):{f}}]"
        L.append(f"| {LABEL.get(m, m)} | {cell('MAE', '.3f')} | {cell('exact', '.1f')} | {cell('F1', '.1f')} | {cell('BAS', '.1f')} |")
    return L + [""], bootv

out = ["# count_metrics.md - declared post-hoc, descriptive (frozen parameters, no tuning)", "",
       f"params_frozen.json frozen_at {J.get('frozen_at')}; warm-up {WARM:.0f} s; intervals = 20 s moving-block bootstrap ({a.boot}), paired across methods, frames pooled over streams.",
       "MAE = mean |count - truth|; F1 = occupied (count > 0) vs vacant; BAS = mean per-class recall over the true counts present (0, 1).", ""]

# ---- A. real held-out streams with injected sources ----
files = sorted(glob.glob(os.path.join(ROOT, "data", "streams", "test_*.csv")))
if len(files) != 10: sys.exit(f"expected 10 test_* streams, found {len(files)}")
fps = [float(json.load(open(f[:-4] + ".json")).get("fps", 3.8)) for f in files]
S = {m: [run(f, m, fps[i]) for i, f in enumerate(files)] for m in METHODS}
L, bootA = boot_table(S, fps, "A. Real held-out streams, injected sources (the 10 test_* streams)", "Same frames as test_results.md (Table 5.2).")
out += L
# per-variant MAE
out += ["MAE by stream:", "", "| Stream | " + " | ".join(LABEL[m] for m in METHODS) + " |", "|---|" + "---|" * len(METHODS)]
for i, f in enumerate(files):
    out.append(f"| {os.path.basename(f)[5:-4]} | " + " | ".join(f"{np.abs(S[m][i][0] - S[m][i][1]).mean():.3f}" for m in METHODS) + " |")
out.append("")

# ---- B. Table 5.1 with intervals: clean windows, ours vs their logged output ----
L5 = [];
for sess, folder, stream, lab in [("0 persons", "0 persons", "test_empty_clean", 0), ("1 person", "1 person -Trial_1", "test_single_clean", 1)]:
    js = json.load(open(os.path.join(ROOT, "data", "streams", stream + ".json"))); f = os.path.join(ROOT, "data", "streams", stream + ".csv"); fp = float(js["fps"])
    raw = pd.read_csv(os.path.join(a.papanashi, folder, "csv_data", "esp32_raw_data.csv")); t0 = pd.to_datetime(raw.timestamp.iloc[0])
    d = pd.read_csv(os.path.join(a.papanashi, folder, "csv_data", "data.csv")); d["t"] = (pd.to_datetime(d.timestamp) - t0).dt.total_seconds()
    w = d[d.t >= js["start_s"] + WARM]; g = w.gridEye_array.values; w = w[np.r_[True, g[1:] != g[:-1]]]     # unique frames only
    theirs = w.current_people_count.values.astype(int)
    ser = {"theirs": [(theirs, np.full(len(theirs), lab))]}
    for m in METHODS: ser[m] = [run(f, m, fp)]
    note = (f"Window from {js['start_s'] + WARM:.0f} s to the end of the session; truth = {lab}. Their rows: data.csv, repeated frames removed ({len(theirs)} frames); "
            "ours: the same window replayed. Lengths differ by a few frames, so each system is bootstrapped on its own blocks (not paired).")
    for m, ps in ser.items():           # independent blocks per system (lengths differ)
        p, t = ps[0]; ix = block_idx(len(p), max(2, int(20 * fp)), a.boot); pt = mets(p, t)
        ex = [(p[ix[b]] == t[ix[b]]).mean() * 100 for b in range(a.boot)]
        # longest consecutive error (s) - point value only
        bad = (p != t).astype(int); best = cur = 0
        for v in bad: cur = cur + 1 if v else 0; best = max(best, cur)
        L5.append(f"| {sess} | {LABEL[m]} | {pt['exact']:.1f} [{np.percentile(ex, 2.5):.1f}, {np.percentile(ex, 97.5):.1f}] | {pt['MAE']:.3f} | {best / fp:.1f} |")
out += ["## B. Table 5.1 with intervals (clean held-out windows, ours vs their logged output)", "",
        "Intervals: 20 s moving-block bootstrap of exact-count accuracy, per system. Longest error = longest run of wrong frames / fps.", "",
        "| Session | System | Exact-count % [95 % CI] | MAE | Longest error (s) |", "|---|---|---|---|---|"] + L5 + [""]

# ---- C. autocorrelation of the error indicator (block length check) ----
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 3.5)); lines = ["## C. Autocorrelation of the per-frame error indicator (real held-out streams)", "",
                                                     "Lag (s) where the mean autocorrelation first drops below 0.1 (streams with at least 1 % errors):", ""]
    for m in METHODS:
        acs = []
        for i, (p, t) in enumerate(S[m]):
            e = (p != t).astype(float)
            if e.mean() < 0.01 or e.mean() > 0.99: continue
            e = e - e.mean(); n = len(e); maxlag = int(60 * fps[i]); v = (e * e).mean()
            acs.append(np.array([(e[:n - k] * e[k:]).mean() / v for k in range(maxlag)]))
        if not acs: lines.append(f"- {LABEL[m]}: too few errors to estimate"); continue
        L0 = min(len(x) for x in acs); ac = np.mean([x[:L0] for x in acs], axis=0); lag = np.arange(L0) / np.mean(fps)
        below = np.flatnonzero(ac < 0.1); lines.append(f"- {LABEL[m]}: {lag[below[0]]:.1f} s" if len(below) else f"- {LABEL[m]}: still above 0.1 at {lag[-1]:.0f} s")
        ax.plot(lag, ac, label=LABEL[m])
    ax.axvline(20, ls="--", c="k", lw=0.8); ax.axhline(0.1, ls=":", c="gray", lw=0.8); ax.set_xlabel("lag (s)"); ax.set_ylabel("autocorrelation of error")
    ax.set_title("Per-frame error autocorrelation (dashed: 20 s block)"); ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(ROOT, "acf.png"), dpi=130)
    out += lines + ["", "If the errors stay correlated well past 20 s, rerun the intervals with 40 s blocks and report both.", ""]
except ImportError:
    out += ["## C. skipped (matplotlib not installed)", ""]

# ---- D. synthetic suite (optional) ----
if a.synth:
    man = None; mf = sorted(f for f in os.listdir(a.synth) if f.endswith("manifest.csv"))
    names = sorted(f[:-4] for f in os.listdir(a.synth) if f.endswith(".csv") and "manifest" not in f and "_labels" not in f and "_events" not in f and os.path.exists(os.path.join(a.synth, f[:-4] + ".json")))
    meta = {}
    if mf:
        man = pd.read_csv(os.path.join(a.synth, mf[0])); key = next(c for c in ("file", "name", "stream", "filename") if c in man.columns)
        man["_n"] = man[key].astype(str).str.replace(r"\.csv$", "", regex=True); man = man.set_index("_n")
    import re
    for n in names:
        sc = man.loc[n, "scenario"] if man is not None and n in man.index and "scenario" in man.columns else re.sub(r"(_s?\d+)+$", "", n)
        sp = man.loc[n, "split"] if man is not None and n in man.index and "split" in man.columns else None
        meta[n] = (str(sc), sp)
    if a.split and man is not None and "split" in man.columns: names = [n for n in names if str(meta[n][1]) == a.split]
    if not names: sys.exit("no synthetic streams found (check --synth / --split)")
    def job(x):
        n, m = x; fp = float(json.load(open(os.path.join(a.synth, n + ".json")))["fps"]); p, t = run(os.path.join(a.synth, n + ".csv"), m, fp)
        return dict(stream=n, scenario=meta[n][0], method=m, **mets(p, t))
    with ThreadPoolExecutor(a.jobs) as ex: R = pd.DataFrame(list(ex.map(job, [(n, m) for n in names for m in METHODS])))
    R.to_csv(os.path.join(ROOT, "count_metrics_synth.csv"), index=False)
    piv = R.groupby(["scenario", "method"])[KEYS].mean().reset_index()
    out += [f"## D. Synthetic suite ({len(names)} streams, split {a.split}), scenarios weighted equally", "",
            "Note: BAS here is per stream, then averaged; F1 is undefined for streams with no occupied frames (empty-room scenarios), so it is averaged over the rest.", "",
            "| Metric | " + " | ".join(LABEL[m] for m in METHODS) + " |", "|---|" + "---|" * len(METHODS)]
    for k in KEYS:
        out.append(f"| {k} | " + " | ".join(f"{piv[piv.method == m][k].mean():.3f}" if k == "MAE" else f"{piv[piv.method == m][k].mean():.1f}" for m in METHODS) + " |")
    out.append("")

open(a.out, "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out)); print("wrote", a.out)
