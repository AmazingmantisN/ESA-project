"""Ambient-drift sanity check of the FROZEN methods (dev slices only; synthetic; NOT a result and NOT used for tuning).

Why: real empty rooms (TODOS dataset) show the whole-frame level moving 3 C (median) to 7 C (p90) over a day; our stress suite only moved the SOURCE, never the room.
Median-subtracted detection should absorb a whole-frame shift, but the DHT-threshold baselines and anything that compares frames over time may not.

Builds, from dev_empty_clean and dev_single_clean, a steady laptop (+8 C, sigma 0.7, as in dev) plus a whole-frame ambient change:
  none     no change (control)
  ramp_1   linear +1.0 C over the stream      ramp_3  linear +3.0 C over the stream      step_15  +1.5 C step at 50 %
For the DHT baselines the DHT reading either follows the room ("dht follows") or stays constant ("dht frozen", a sluggish sensor).
Scores false% + missed% with the protocol metric (30 s warm-up). Writes only to ../data/ambient/ (not a stream folder) and the md given by --md.

  python ambient_check.py [--frozen ../params_frozen.json] [--md ../ambient_check.md]
"""
import argparse, io, json, math, os, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T, robust_lib as R

ap = argparse.ArgumentParser(); ap.add_argument("--frozen", default=os.path.join(ROOT, "params_frozen.json")); ap.add_argument("--md", default=os.path.join(ROOT, "ambient_check.md"))
a = ap.parse_args()
T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.join(ROOT, "tuning_protocol_v1.4.json"))
F = json.load(open(a.frozen))["candidates"]; out = os.path.join(ROOT, "data", "ambient"); os.makedirs(out, exist_ok=True)
CASES = {"none": lambda n: np.zeros(n), "ramp_1": lambda n: np.linspace(0, 1.0, n), "ramp_3": lambda n: np.linspace(0, 3.0, n), "step_15": lambda n: 1.5 * (np.arange(n) >= n // 2)}
res = {}                                     # (method, case, dht) -> list of totals per base
for b in R.BASES:
    head, body, lab, side, fps, frames = R.read_base(os.path.join(ROOT, "data", "streams"), b)
    src = R.inject(frames, fps, "steady", 8.0, np.random.default_rng(5))
    for case, f in CASES.items():
        dT = f(len(frames))
        for dht_mode in ("follows", "frozen"):
            fr = (src + dT[:, None, None]).reshape(len(frames), 64); bd = [list(r) for r in body]
            if dht_mode == "follows":
                for i, r in enumerate(bd): r[3] = f"{float(r[3]) + dT[i]:.2f}"
            name = f"amb_{b.split('_')[1]}_{case}_{dht_mode}"; R.write_stream(out, name, head, bd, lab, fr, side, "steady", 8.0)
            for e in ("ours", "ours_v2", "bcode", "bpaper"):
                r = subprocess.run([T.G["EXE"], "--stream", os.path.join(out, name + ".csv"), "--fps", str(fps)] + T.args_for(e, F[e]["params"]), capture_output=True, text=True)
                d = pd.read_csv(io.StringIO(r.stdout)).iloc[math.ceil(30 * fps):]
                res.setdefault((e, case, dht_mode), []).append(((d.smooth > d.humans).mean() + (d.smooth < d.humans).mean()) * 100)
L = ["# ambient_check.md (frozen methods, dev slices + steady +8 C laptop + whole-frame ambient change; synthetic; NOT a result)", "",
     "Error % = false% + missed%, mean of the empty-room and single-person stream. For ours/ours_v2 the DHT column is unused, so only the 'follows' value is shown.", "",
     "| Method | none | ramp +1 C | ramp +3 C | step +1.5 C | ramp +3 C, DHT frozen | step +1.5 C, DHT frozen |", "|---|---|---|---|---|---|---|"]
for e in ("ours", "ours_v2", "bcode", "bpaper"):
    g = lambda c, m: np.mean(res[(e, c, m)])
    cells = [g("none", "follows"), g("ramp_1", "follows"), g("ramp_3", "follows"), g("step_15", "follows")]
    fz = [g("ramp_3", "frozen"), g("step_15", "frozen")] if e in ("bcode", "bpaper") else [float("nan")] * 2
    L.append(f"| {e} | " + " | ".join("%.1f" % c if c == c else "n/a" for c in cells + fz) + " |")
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", a.md)
