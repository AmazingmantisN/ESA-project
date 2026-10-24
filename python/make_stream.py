"""Turn frames.npy into a labelled stream CSV: optionally cut a time slice, inject static heat
sources, optionally emulate a smaller sensor (4x4 / 2x2) by block-averaging.

Usage examples
  python make_stream.py ../data/single_t1.npy --humans 1 --start-s 120 --end-s 420 --inject laptop --out ../data/streams/dev_single_laptop.csv
  python make_stream.py ../data/empty.npy --humans 0 --inject heater --amp 3 --out ../data/streams/e_heater_weak.csv
  python make_stream.py ../data/single_t1.npy --humans 1 --inject laptop --grid 4 --out ../data/s_g4.csv

If <frames>_t.npy (written by load_dataset.py) sits next to the frames file, --start-s/--end-s
work and the frame rate of the slice is measured. A sidecar <out>.json records fps, slice, gaps
and the injected source, so later scripts can convert seconds -> frames.

DHT: if <frames>_dht.npy (written by load_dataset.py v2) sits next to the frames file, the stream gets a
`dht` column (ambient reading, dropouts forward-filled) right after `injected`. Only the DHT-threshold
baseline reads it; run_pc / the firmware ignore it otherwise. --dht-raw uses the readings as recorded
(with the 0.1 / -0.2 dropouts), --no-dht omits the column. Injected sources do not change the DHT.

Ground truth columns in the CSV:  humans = real people (from the session label)
                                  injected = number of fake static sources added
Injected strength: preset amplitudes are in degC ABOVE ambient at the source centre. A person in
the papanashi data peaks at only ~+2.3 degC above the frame median, so a +8 degC laptop is far
brighter than a person. Use --amp to set a source of comparable strength (the harder case).
"""
import argparse, json, os
import numpy as np

PRESETS = {  # amplitude (degC above ambient), sigma (pixels), slow thermal wobble (degC)
    "laptop": dict(amp=8.0,  sigma=0.7, wobble=0.3),
    "heater": dict(amp=15.0, sigma=1.2, wobble=0.5),
    "sun":    dict(amp=4.0,  sigma=1.5, wobble=0.4),
}

def gauss(cx, cy, sigma):
    ys, xs = np.mgrid[0:8, 0:8]
    return np.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / (2 * sigma ** 2))

def farthest_from_person(frames):
    """Pick an interior pixel as far as possible from where the person usually is."""
    mean = frames.mean(axis=0) - np.median(frames)
    py, px = np.unravel_index(np.argmax(mean), mean.shape)
    best, bd = (3, 3), -1
    for r in range(1, 7):
        for c in range(1, 7):
            d = (r - py) ** 2 + (c - px) ** 2
            if d > bd: bd, best = d, (r, c)
    return best  # (row, col)

ap = argparse.ArgumentParser()
ap.add_argument("frames"); ap.add_argument("--humans", type=int, required=True)
ap.add_argument("--inject", choices=["none", "laptop", "heater", "sun"], default="none")
ap.add_argument("--n_static", type=int, default=1)
ap.add_argument("--pos", help="row,col override for the first injected source")
ap.add_argument("--amp", type=float, help="override preset amplitude (degC above ambient)")
ap.add_argument("--start-s", type=float, help="keep frames from this time (needs <frames>_t.npy)")
ap.add_argument("--end-s", type=float, help="keep frames before this time (needs <frames>_t.npy)")
ap.add_argument("--grid", type=int, choices=[8, 4, 2], default=8)
ap.add_argument("--noise", type=float, default=0.1, help="extra sensor noise on injected source (degC)")
ap.add_argument("--dht-raw", action="store_true", help="use DHT readings as recorded (default: dropouts forward-filled)")
ap.add_argument("--no-dht", action="store_true", help="do not write a dht column")
ap.add_argument("--seed", type=int, default=1); ap.add_argument("--out", required=True)
a = ap.parse_args()

rng = np.random.default_rng(a.seed)
frames = np.load(a.frames).astype(np.float32)
tpath = a.frames[:-4] + "_t.npy" if a.frames.endswith(".npy") else None
t_s = np.load(tpath) if tpath and os.path.exists(tpath) else None
dpath = a.frames[:-4] + ("_dhtraw.npy" if a.dht_raw else "_dht.npy") if a.frames.endswith(".npy") else None
dht = np.load(dpath).astype(np.float32) if (dpath and os.path.exists(dpath) and not a.no_dht) else None
if dht is not None and len(dht) != len(frames): raise SystemExit(f"{dpath} has {len(dht)} rows but frames has {len(frames)}: rerun load_dataset.py")

if (a.start_s is not None or a.end_s is not None):
    if t_s is None: raise SystemExit(f"--start-s/--end-s need {tpath} (run load_dataset.py first)")
    m = np.ones(len(frames), bool)
    if a.start_s is not None: m &= t_s >= a.start_s
    if a.end_s is not None:   m &= t_s < a.end_s
    frames, t_s = frames[m], t_s[m]
    if dht is not None: dht = dht[m]
    if len(frames) < 50: raise SystemExit(f"slice has only {len(frames)} frames")

n = len(frames)
fps = gaps = None
if t_s is not None and n > 2:
    dt = np.diff(t_s); med = float(np.median(dt)); fps = round(1.0 / med, 3)
    gaps = int((dt > 3 * med).sum())

injected, inj_info = 0, None
if a.inject != "none":
    pr = dict(PRESETS[a.inject])
    if a.amp is not None: pr["amp"] = a.amp
    base = tuple(int(v) for v in a.pos.split(",")) if a.pos else farthest_from_person(frames)
    spots = [base, (7 - base[0], 7 - base[1]), (base[0], 7 - base[1])][: a.n_static]
    print(f"injecting {a.n_static} x {a.inject} (amp {pr['amp']} degC, sigma {pr['sigma']}) at (row,col) = {spots}")
    # wobble period ~94 s whatever the frame rate
    tt = (t_s - t_s[0]) / 15.0 if t_s is not None else np.arange(n) / 150.0
    for k, (r, c) in enumerate(spots):
        g = gauss(c, r, pr["sigma"])
        amp_t = pr["amp"] + pr["wobble"] * np.sin(tt + k)                   # slow fan/thermostat wobble
        frames += (amp_t[:, None, None] * g[None]) + rng.normal(0, a.noise, frames.shape) * g[None]
    injected = len(spots)
    inj_info = dict(kind=a.inject, amp=pr["amp"], sigma=pr["sigma"], spots=[list(s) for s in spots])

if a.grid != 8:
    b = 8 // a.grid
    frames = frames.reshape(n, a.grid, b, a.grid, b).mean(axis=(2, 4))      # block-average
flat = frames.reshape(n, -1)
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
with open(a.out, "w") as f:
    f.write("frame,humans,injected," + ("dht," if dht is not None else "") + ",".join(f"p{i}" for i in range(flat.shape[1])) + "\n")
    for i in range(n):
        f.write(f"{i},{a.humans},{injected}," + (f"{dht[i]:.2f}," if dht is not None else "") + ",".join(f"{v:.2f}" for v in flat[i]) + "\n")
side = dict(source=os.path.basename(a.frames), dht_column=bool(dht is not None), dht_raw=bool(a.dht_raw), frames=n, grid=a.grid, humans=a.humans, injected=injected,
            injected_info=inj_info, fps=fps, start_s=a.start_s, end_s=a.end_s,
            slice_duration_s=round(float(t_s[-1] - t_s[0]), 1) if t_s is not None else None,
            gaps_over_3x_median=gaps)
with open(a.out[:-4] + ".json", "w") as f: json.dump(side, f, indent=1)
print(f"wrote {a.out}: {n} frames, {a.grid}x{a.grid}, humans={a.humans}, injected={injected}"
      + (f", {fps} Hz, {side['slice_duration_s']} s, {gaps} gaps" if fps else ", fps unknown (no _t.npy)"))
