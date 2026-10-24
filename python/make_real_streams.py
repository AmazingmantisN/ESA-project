"""Build every labelled stream for the real-data study in one command (reproducible split).

Usage (from the python/ folder, after load_dataset.py produced the .npy files in ../data):
  python make_real_streams.py                 # reads ../data, writes ../data/streams
  python make_real_streams.py --data ../data --seed 1

SPLIT (all times in seconds from the start of each session; edit the table below to change it)
  empty      0-320 s  = DEV     320-end = TEST          truth: 0 people
  single_t1  120-420  = DEV     420-end = TEST          truth: 1 person
                      (first 120 s skipped: the person signal ramps up slowly, so the
                       'always 1 person' label is not trustworthy there)
  two        180-end  = EXPLORATORY ONLY (86 timing gaps, people merge at 8x8; not for tuning)
  single_t2  EXCLUDED: 71 s long and its heat signal is indistinguishable from the empty room
GUARD GAP: test_* streams start 20 s after the dev slice ends (measured: frame-to-frame correlation of the
  hot-pixel features is ~0.1 or lower after 15 s, ~0 after 40 s), so test is not a continuation of dev.
RULE: tune on dev_* only. Touch test_* once, after the parameters are frozen.

Variants of injected static source (same position in every stream, far from the person):
  clean         nothing injected
  laptop        preset +8 degC, small   (much hotter than a person: the easy case)
  laptop_weak   +3 degC, small          (comparable to a person's ~+2.3 degC: the hard case)
  heater        preset +15 degC, wide
  heater_weak   +3 degC, wide
"""
import argparse, os, subprocess, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="../data"); ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--guard-s", type=float, default=20.0, help="seconds dropped from the start of every test_* stream (decorrelation gap after the dev slice)")
a = ap.parse_args()
out = os.path.join(a.data, "streams"); os.makedirs(out, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))

# (name, source npy, humans, start_s, end_s)
SEGMENTS = [
    ("dev_empty",   "empty",     0,   0,  320),
    ("test_empty",  "empty",     0, 320, None),
    ("dev_single",  "single_t1", 1, 120,  420),
    ("test_single", "single_t1", 1, 420, None),
    ("expl_two",    "two",       2, 180, None),
]
VARIANTS = {  # suffix -> extra make_stream args
    "clean": [],
    "laptop": ["--inject", "laptop"],
    "laptop_weak": ["--inject", "laptop", "--amp", "3"],
    "heater": ["--inject", "heater"],
    "heater_weak": ["--inject", "heater", "--amp", "3"],
}
EXPL_VARIANTS = ["clean", "laptop_weak"]

def far_pos(npy, start, end):
    """Interior pixel farthest from where the person usually is (same rule as make_stream)."""
    f = np.load(npy); t = np.load(npy[:-4] + "_t.npy")
    m = (t >= start) & ((t < end) if end else True)
    mean = f[m].mean(axis=0) - np.median(f[m])
    py, px = np.unravel_index(np.argmax(mean), mean.shape)
    best, bd = (3, 3), -1
    for r in range(1, 7):
        for c in range(1, 7):
            d = (r - py) ** 2 + (c - px) ** 2
            if d > bd: bd, best = d, (r, c)
    return best

paths = {k: os.path.join(a.data, k + ".npy") for k in ("empty", "single_t1", "two")}
for k, p in paths.items():
    if not os.path.exists(p): sys.exit(f"missing {p}: run load_dataset.py for this session first")

pos_single = far_pos(paths["single_t1"], 120, 420)        # fixed from DEV slice only
pos = {"empty": pos_single, "single_t1": pos_single, "two": far_pos(paths["two"], 180, None)}
print("injected source positions (row,col):", pos)

print(f"guard gap: first {a.guard_s:g} s of every test_* stream dropped")
n = 0
for name, src, humans, s0, s1 in SEGMENTS:
    if name.startswith("test_"): s0 = s0 + a.guard_s
    variants = EXPL_VARIANTS if name.startswith("expl") else list(VARIANTS)
    for v in variants:
        dst = os.path.join(out, f"{name}_{v}.csv")
        cmd = [sys.executable, os.path.join(here, "make_stream.py"), paths[src], "--humans", str(humans),
               "--start-s", str(s0), "--pos", f"{pos[src][0]},{pos[src][1]}", "--seed", str(a.seed), "--out", dst] + VARIANTS[v]
        if s1: cmd += ["--end-s", str(s1)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode: sys.exit(r.stderr or r.stdout)
        print(r.stdout.strip().splitlines()[-1]); n += 1
print(f"\n{n} streams in {out}")
