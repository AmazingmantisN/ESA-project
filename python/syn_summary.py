"""Group means and paired differences from an eval_suite.py CSV (synthetic suite). Descriptive grouping (declared, not pre-registered): core = A1-A15,G1; fps = *_1Hz/*_10Hz; unseen = U1-U6.
Paired difference = mean over scenarios of (method A - method B), 95 % bootstrap over seeds within each scenario (resampling streams of the same scenario); negative = A better.
  python syn_summary.py eval_test_v11.csv [--md syn_summary_test.md]
"""
import argparse, numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--md", default="syn_summary.md"); a = ap.parse_args()
d = pd.read_csv(a.csv); p = d.pivot_table(index=["scenario", "stream"], columns="method", values="strict").reset_index()
p["g"] = p.scenario.map(lambda s: "unseen" if s.startswith("U") else ("fps" if "Hz" in s else "core")); M = [m for m in ("ours", "ours_v2", "bcode", "bpaper", "bcode_asis") if m in p.columns]
L = [f"# syn_summary ({a.csv}); strict error %, scenarios weighted equally", "", "| Group | scenarios | " + " | ".join(M) + " |", "|---|---|" + "---|" * len(M)]
for g, df in list(p.groupby("g")) + [("ALL", p)]:
    m = df.groupby("scenario")[M].mean().mean(); L.append(f"| {g} | {df.scenario.nunique()} | " + " | ".join(f"{m[k]:.1f}" for k in M) + " |")
rng = np.random.default_rng(11); B = 3000
L += ["", "Paired differences (negative = first is better), 95 % bootstrap over seeds within scenario:", "", "| Group | Comparison | Diff [95 % CI] | first better in |", "|---|---|---|---|"]
for gn, df in [("ALL", p), ("core", p[p.g == "core"]), ("unseen", p[p.g == "unseen"]), ("fps", p[p.g == "fps"])]:
    for x, y in [("ours", "bpaper"), ("ours", "bcode"), ("ours_v2", "bpaper"), ("ours_v2", "bcode"), ("ours", "ours_v2")]:
        parts = [(df[df.scenario == s][x].values - df[df.scenario == s][y].values) for s in sorted(df.scenario.unique())]
        obs = np.mean([q.mean() for q in parts]); bs = np.mean([q[rng.integers(0, len(q), (B, len(q)))].mean(1) for q in parts], axis=0); w = sum((q < 0).mean() > 0.5 for q in parts)
        L.append(f"| {gn} | {x} - {y} | {obs:+.2f} [{np.percentile(bs, 2.5):+.2f}, {np.percentile(bs, 97.5):+.2f}] | {w}/{len(parts)} scenarios |")
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
