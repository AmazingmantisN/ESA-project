"""Shared generator for non-ideal injected heat sources (used by robust_check.py and make_robust_dev.py).

The functions inject() / ar1() are the ones robust_check.py used in Step 5e, moved here unchanged (the seed-77 robust_summary.md must reproduce exactly);
the only addition is the 'jitter_xs' variant (protocol v1.3). Nothing here reads test_* streams.

Variants (position in (row, col) pixels, amplitude in degC; every source also has laptop size sigma 0.7 px at (1,1) as in dev):
  steady    same as the dev laptops (0.3 C slow wobble only)
  jitter_xs position wanders 0.05 px/frame + flicker 0.15 C (AR 0.8): a very quiet laptop          (v1.3 only)
  jitter_s  position wanders 0.10 px/frame + flicker 0.30 C: a laptop with a fan
  jitter_m  position wanders 0.25 px/frame + flicker 0.60 C: a rough laptop
  drift     the source slides 1.5 px along the row over the stream
  switch    OFF for the first 35 %, ramps on over 5 s, jumps 1 px at 70 %
  walker    ADVERSARY: random walk 0.35 px/frame (behaves like a person)
"""
import csv, json, os
import numpy as np

BASES = ["dev_empty_clean", "dev_single_clean"]; AMPS = {"w": 3.0, "s": 8.0}; SIGMA = 0.7; POS = (1.0, 1.0)   # (row, col)
JITTER = {"jitter_xs": (0.05, 0.15), "jitter_s": (0.10, 0.3), "jitter_m": (0.25, 0.6)}                         # (position sd px, flicker sd C)

def ar1(rng, n, sd, rho=0.8):
    x = np.zeros(n); e = rng.normal(0, sd * np.sqrt(1 - rho ** 2), n); x[0] = rng.normal(0, sd)
    for i in range(1, n): x[i] = rho * x[i - 1] + e[i]
    return x

def inject(frames, fps, variant, amp, rng):
    n = len(frames); t = np.arange(n) / fps; r = np.full(n, POS[0]); c = np.full(n, POS[1]); A = amp + 0.3 * np.sin(t / 15.0) * np.ones(n)
    if variant in JITTER:
        sd, fl = JITTER[variant]
        r = r + rng.normal(0, sd, n); c = c + rng.normal(0, sd, n); A = A + ar1(rng, n, fl)
    elif variant == "drift": c = c + np.linspace(0, 1.5, n)
    elif variant == "switch":
        on = int(0.35 * n); ramp = max(1, int(5 * fps)); gain = np.clip((np.arange(n) - on) / ramp, 0, 1); A = A * gain; r = r + (np.arange(n) >= int(0.7 * n))
    elif variant == "walker":
        r = np.clip(POS[0] + np.cumsum(rng.normal(0, 0.35, n)), 0.5, 6.5); c = np.clip(POS[1] + np.cumsum(rng.normal(0, 0.35, n)), 0.5, 6.5)
    ys, xs = np.mgrid[0:8, 0:8]
    g = np.exp(-((xs[None] - c[:, None, None]) ** 2 + (ys[None] - r[:, None, None]) ** 2) / (2 * SIGMA ** 2))
    return frames + A[:, None, None] * g + rng.normal(0, 0.1, frames.shape) * g

def read_base(src_dir, b):
    """Read a clean dev slice: returns (header, body rows, index of p0, sidecar json, fps, frames[N,8,8])."""
    rows = list(csv.reader(open(os.path.join(src_dir, b + ".csv")))); head = rows[0]; body = rows[1:]
    lab = next(i for i, nm in enumerate(head) if len(nm) > 1 and nm[0] == "p" and nm[1:].isdigit())
    side = json.load(open(os.path.join(src_dir, b + ".json"))); fps = float(side.get("fps") or 3.8)
    frames = np.array([[float(v) for v in r[lab:lab + 64]] for r in body]).reshape(-1, 8, 8)
    return head, body, lab, side, fps, frames

def write_stream(out_dir, name, head, body, lab, fr, side, variant, amp):
    """Write one injected stream (csv + sidecar json), format identical to the Step 5e robust streams."""
    with open(os.path.join(out_dir, name + ".csv"), "w", newline="") as f:
        f.write(",".join(head[:lab]) + "," + ",".join(f"p{i}" for i in range(64)) + "\n")
        for i, r in enumerate(body):
            pre = list(r[:lab]); pre[2] = "1"
            f.write(",".join(pre) + "," + ",".join(f"{x:.2f}" for x in fr[i]) + "\n")
    json.dump(dict(side, injected=1, injected_info=dict(kind="robust:" + variant, amp=amp, sigma=SIGMA, spots=[[int(POS[0]), int(POS[1])]])),
              open(os.path.join(out_dir, name + ".json"), "w"))
