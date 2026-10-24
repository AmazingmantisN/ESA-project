"""Make FAKE 8x8 frames so you can test the whole pipeline today, before the dataset arrives.
NOT for paper results - only for checking that the code works.

Usage:  python synthetic.py ../data/synth_single.npy --humans 1 --frames 3000
        python synthetic.py ../data/synth_empty.npy  --humans 0 --frames 3000
"""
import argparse
import numpy as np

def blob(cx, cy, amp, sigma):
    ys, xs = np.mgrid[0:8, 0:8]
    return amp * np.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / (2 * sigma ** 2))

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--humans", type=int, default=1)
ap.add_argument("--frames", type=int, default=3000); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)
amb = 26.0
starts = [(2.0, 2.5), (5.5, 5.0)][: a.humans]
pos = [np.array(s, dtype=float) for s in starts]
out = np.zeros((a.frames, 8, 8), dtype=np.float32)
for t in range(a.frames):
    f = amb + 0.2 * np.sin(t / 700.0) + rng.normal(0, 0.15, (8, 8))       # ambient + sensor noise
    for k, p in enumerate(pos):
        p += rng.normal(0, 0.03, 2)                                        # fidgeting random walk
        p[:] = np.clip(p, 1.0, 6.0)
        breathe = 1.0 + 0.05 * np.sin(t / 8.0 + k)
        f += blob(p[0], p[1], 4.0 * breathe, 1.1)
    out[t] = f
np.save(a.out, out)
print("saved", a.out, out.shape)
