"""DHT-reference-error curve for the baselines (FROZEN params, dev slices + steady +8 C laptop; synthetic sanity check, NOT a result, not used for tuning).

Why: B-paper/B-code threshold pixels against the DHT (ambient) reading. If the DHT lags a drifting room, it reads e degC too LOW (room warming) or too HIGH (cooling).
For a room drifting at r degC/min and a DHT with first-order lag tau min, the steady error is e = r * tau. We sweep e directly (both signs) and read the physical meaning off the axis.
Ours-v1/v2 do not use the DHT, so their line is flat by construction (shown once as the control, using e = 0).
  python dht_lag.py [--frozen ../params_frozen.json] [--md ../dht_lag.md] [--csv ../dht_lag.csv]
"""
import argparse, io, json, math, os, subprocess, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T, robust_lib as R
ap = argparse.ArgumentParser(); ap.add_argument("--frozen", default=os.path.join(ROOT, "params_frozen.json")); ap.add_argument("--md", default=os.path.join(ROOT, "dht_lag.md")); ap.add_argument("--csv", default=os.path.join(ROOT, "dht_lag.csv")); a = ap.parse_args()
T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.join(ROOT, "tuning_protocol_v1.4.json"))
F = json.load(open(a.frozen))["candidates"]; out = os.path.join(ROOT, "data", "ambient"); os.makedirs(out, exist_ok=True)
E = [-3.0, -2.0, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0, 3.0]; M = [m for m in ("ours", "ours_v2", "bcode", "bpaper", "bcode_asis") if m in F]; rows = []
for b in R.BASES:
    head, body, lab, side, fps, frames = R.read_base(os.path.join(ROOT, "data", "streams"), b)
    src = R.inject(frames, fps, "steady", 8.0, np.random.default_rng(5)).reshape(len(frames), 64)
    for e in E:
        bd = [list(r) for r in body]
        for r in bd: r[3] = f"{float(r[3]) + e:.2f}"            # DHT reads e degC off the true value
        name = f"dht_{b.split('_')[1]}_{e:+.2f}"; R.write_stream(out, name, head, bd, lab, src, side, "steady", 8.0)
        for m in M:
            r = subprocess.run([T.G["EXE"], "--stream", os.path.join(out, name + ".csv"), "--fps", str(fps)] + T.args_for(m, F[m]["params"]), capture_output=True, text=True)
            d = pd.read_csv(io.StringIO(r.stdout)).iloc[math.ceil(30 * fps):]
            rows.append(dict(base=b, e=e, method=m, false=(d.smooth > d.humans).mean() * 100, missed=(d.smooth < d.humans).mean() * 100))
df = pd.DataFrame(rows); df["err"] = df["false"] + df["missed"]; df.to_csv(a.csv, index=False)
p = df.pivot_table(index="e", columns="method", values="err", aggfunc="mean")[M]
L = ["# dht_lag.md (frozen methods; DHT reads e degC off the true room value; steady +8 C laptop on dev slices; synthetic; NOT a result)", "",
     "e = r x tau: e.g. room warming 0.1 C/min with a 5-min-lag DHT -> e = -0.5 (DHT reads low). Error % = false + missed, mean of empty and single stream.", "",
     "| e (C) | " + " | ".join(M) + " |", "|---|" + "---|" * len(M)] + [f"| {e:+.2f} | " + " | ".join("%.1f" % v for v in p.loc[e]) + " |" for e in p.index]
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("wrote", a.md, a.csv)
