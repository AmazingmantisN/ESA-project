"""Live viewer: 8x8 heatmap + the ESP32's people count, updating frame by frame.

pip install matplotlib pyserial        (run from the python/ folder, Serial Monitor closed)

LIVE  (real ESP32, frames sent over USB at real-time speed):
  python live_viewer.py --port COM7 --stream ..\\data\\streams\\dev_single_laptop_weak.csv --window_s 6 --drift 0.4 --contrast 1.0 --k 0.5
REPLAY (no board; shows a saved run, e.g. as a backup or for rehearsal):
  python live_viewer.py --stream ..\\data\\streams\\dev_single_laptop_weak.csv --results ..\\data\\demo_esp.csv
Options: --speed 2 (twice as fast)  --fps 3.79  --png out.png --at 400 (save frame 400 and exit, no window)
Any other flag (--window_s, --drift, --contrast, --k, --preset ...) goes to run_pc exactly as in stream_to_esp32.py.
The heatmap is the recorded sensor data, NOT a live sensor. A "+" marks an injected (fake) heat source.
"""
import argparse, csv, json, os, subprocess, sys, time
import numpy as np

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--stream", required=True); ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=921600)
ap.add_argument("--results"); ap.add_argument("--fps", type=float); ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--png"); ap.add_argument("--at", type=int, default=400); ap.add_argument("--warmup", type=int, default=40)
a, rest = ap.parse_known_args()
if not a.port and not a.results: raise SystemExit("give --port COM7 (live) or --results file.csv (replay)")

import matplotlib
if a.png: matplotlib.use("Agg")
import matplotlib.pyplot as plt

try: side = json.load(open(a.stream[:-4] + ".json"))
except Exception: side = {}
fps = a.fps or side.get("fps") or 3.79
rows = list(csv.reader(open(a.stream))); names = rows[0]; body = rows[1:]
lab = next(i for i, n in enumerate(names) if len(n) > 1 and n[0] == "p" and n[1:].isdigit())
grids = np.array([[float(v) for v in r[lab:lab + 64]] for r in body]).reshape(-1, 8, 8)
truth = np.array([int(r[1]) for r in body]); dcol = names.index("dht") if "dht" in names else None
N = len(body)

if a.results:                                    # ---- replay a saved results CSV
    res = list(csv.DictReader(open(a.results)))
    def ask(i): r = res[i]; return int(r["raw"]), int(r["smooth"]), int(r["us"]), int(r["static"] or 0)
    mode = "REPLAY of a logged run (not live)"
else:                                            # ---- live ESP32
    HERE = os.path.dirname(os.path.abspath(__file__))
    EXE = next((p for p in (os.path.join(HERE, "..", "pc_test", n) for n in ("run_pc.exe", "run_pc")) if os.path.exists(p)), None)
    pline = None
    if rest:
        if EXE is None: raise SystemExit("parameter flags need ../pc_test/run_pc(.exe): build it first")
        r = subprocess.run([EXE, "--print_pline", "1", "--fps", str(fps)] + rest, capture_output=True, text=True)
        if r.returncode or not r.stdout.startswith("P,"): raise SystemExit("run_pc rejected the flags:\n" + (r.stderr or r.stdout))
        pline = r.stdout.strip(); print("parameters:", pline)
    import serial
    ser = serial.Serial(a.port, a.baud, timeout=2); time.sleep(2.5); ser.reset_input_buffer()
    ser.write(b"R\n")
    if ser.readline().decode(errors="ignore").strip() != "OK": raise SystemExit("ESP32 did not acknowledge reset")
    if pline:
        ser.write((pline + "\n").encode())
        if ser.readline().decode(errors="ignore").strip() != "OK": raise SystemExit("ESP32 rejected parameters (is the sketch v2?)")
    def ask(i):
        v = ",".join(body[i][lab:lab + 64])
        ser.write((f"D,{i},{body[i][dcol]},{v}\n" if dcol is not None else f"F,{i},{v}\n").encode())
        p = ser.readline().decode(errors="ignore").strip().split(",")
        if len(p) not in (5, 6) or p[0] != "R": raise SystemExit(f"bad reply at frame {i}: {p}")
        return int(p[2]), int(p[3]), int(p[4]), int(p[5]) if len(p) == 6 else 0
    mode = "LIVE on ESP32 (%s)" % a.port

fig = plt.figure(figsize=(11, 5.6)); gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.35], height_ratios=[3, 2])
axh, axc, axt = fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 1]); axt.axis("off")
lo, hi = np.percentile(grids, 1), np.percentile(grids, 99.8)
im = axh.imshow(grids[0], cmap="inferno", vmin=lo, vmax=hi, interpolation="nearest")
fig.colorbar(im, ax=axh, fraction=0.046, label="sensor temperature (C)")
axh.set_title("Recorded 8x8 thermal frame (not a live sensor)", fontsize=10)
for s in (side.get("injected_info") or {}).get("spots", []): axh.plot(s[1], s[0], "c+", ms=16, mew=2)
if (side.get("injected_info") or {}).get("spots"): axh.set_xlabel("+ = injected (fake) %s" % side["injected_info"].get("kind", "heat source"), fontsize=9)
t = np.arange(N) / fps; ys, yt = [], []
(lt,) = axc.step([], [], color="0.6", lw=3, label="true people (session label)"); (ls,) = axc.plot([], [], color="tab:blue", lw=1.8, label="ESP32 smoothed count")
axc.set_ylim(-0.3, max(2, truth.max()) + 0.6); axc.set_yticks(range(0, max(2, truth.max()) + 1)); axc.set_xlabel("time (s)"); axc.legend(loc="upper left", fontsize=8)
txt = axt.text(0, 1, "", va="top", family="monospace", fontsize=11)
fig.suptitle("Persistence filter on ESP32 | " + mode, fontsize=12); fig.tight_layout()

ok = scored = 0; t0 = time.time(); stop = min(N, a.at + 1) if a.png else N
for i in range(stop):
    raw, sm, us, st = ask(i); ys.append(sm); yt.append(truth[i])
    if i >= a.warmup: scored += 1; ok += (sm == truth[i])
    im.set_data(grids[i]); lt.set_data(t[:i + 1], yt); ls.set_data(t[:i + 1], ys)
    axc.set_xlim(max(0, t[i] - 60), max(60, t[i] + 1))
    tm = f"{us/1000:.2f} ms/frame" if us else "n/a (PC run, not timed)"
    state = "PERSON PRESENT" if sm > 0 else "nobody seen"
    txt.set_text(f"frame {i}/{N}   t = {t[i]:6.1f} s\ntrue people      : {truth[i]}\nESP32 says       : {sm}  ({state})\nstatic blobs     : {st}\nfilter time      : {us/1000:.2f} ms/frame\n"
                 f"running accuracy : {100*ok/scored:5.1f} %  (after {a.warmup}-frame warm-up)" if scored else
                 f"frame {i}/{N}   t = {t[i]:6.1f} s\nESP32 says       : {sm}\nfilter time      : {tm}\n(warming up...)")
    if a.png: continue
    plt.pause(max(0.001, t0 + i / (fps * a.speed) - time.time()))
if a.png: fig.savefig(a.png, dpi=110); print("saved", a.png)
else: print("done"); plt.show()
