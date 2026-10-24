"""ESP32 final check of the FROZEN methods: (1) parity with the PC reference, frame for frame, (2) filter time per frame. Runs on your laptop with the board on COM7.

For every frozen entry (params_frozen.json: ours, ours_v2, bcode, bpaper + the as-published reference) and each stream it
  - resolves the parameters to the firmware 'P' line with run_pc (exactly what stream_to_esp32.py does), sends it, streams the frames,
  - compares raw / smoothed / static counts with run_pc frame by frame (expected: 0 mismatches),
  - records the microseconds the ESP32 spent in filt.process() (not serial/parsing time) and reports mean / median / p95 / max.
Memory: this protocol cannot read the heap, so use the Arduino IDE compile report ("Global variables use N bytes") plus pc_test/sizeof_filter.exe (static filter size per grid).

  pip install pyserial
  python esp32_final_check.py --port COM7 [--frozen ..\\params_frozen.json] [--frames 0] [--md ..\\esp32_check.md]
  python esp32_final_check.py --shim ..\\pc_test\\fw.exe      # same thing against a PC build of the sketch (no board; timing then is PC timing, labelled as such)
Streams used (dev only, never test_*): dev_single_laptop_weak, dev_empty_heater, dev_single_clean. --frames 0 = all frames. ~5 methods x 3 streams x 1000 frames, a few minutes.
Exit code 0 = zero mismatches everywhere.
"""
import argparse, csv, io, json, math, os, subprocess, sys, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T
ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--port"); g.add_argument("--shim")
ap.add_argument("--frozen", default=os.path.join(ROOT, "params_frozen.json")); ap.add_argument("--frames", type=int, default=0); ap.add_argument("--baud", type=int, default=921600)
ap.add_argument("--streams", default="dev_single_laptop_weak,dev_empty_heater,dev_single_clean"); ap.add_argument("--md", default=os.path.join(ROOT, "esp32_check.md")); a = ap.parse_args()
T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.join(ROOT, "tuning_protocol_v1.4.json")); EXE = T.G["EXE"]
F = json.load(open(a.frozen)); M = {e: c["params"] for e, c in F["candidates"].items()}; M.update({e: c["params"] for e, c in F.get("references", {}).items()})

if a.shim:
    p = subprocess.Popen([a.shim], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    tx = lambda s: (p.stdin.write(s + "\n"), p.stdin.flush(), p.stdout.readline().strip())[2]; link = f"PC shim ({a.shim}) - timings are PC timings, NOT the ESP32"
else:
    import serial
    ser = serial.Serial(a.port, a.baud, timeout=3); time.sleep(2.5); ser.reset_input_buffer()
    tx = lambda s: (ser.write((s + "\n").encode()), ser.readline().decode(errors="ignore").strip())[1]; link = f"ESP32 on {a.port} @ {a.baud}"
if tx("R") != "OK": sys.exit("no OK for R: is the sketch flashed and the port free (close the Arduino serial monitor)?")

rows_out = []; bad = 0; detail = []
for sname in a.streams.split(","):
    csvp = os.path.join(ROOT, "data", "streams", sname + ".csv"); fps = float(json.load(open(csvp[:-4] + ".json"))["fps"])
    rows = list(csv.reader(open(csvp))); names, body = rows[0], rows[1:]
    if a.frames: body = body[:a.frames]
    lab = next(i for i, n in enumerate(names) if len(n) > 1 and n[0] == "p" and n[1:].isdigit()); dcol = names.index("dht") if "dht" in names else None
    small = os.path.join(ROOT, "data", "latency", "_esp_check.csv"); os.makedirs(os.path.dirname(small), exist_ok=True)
    with open(small, "w", newline="") as f: w = csv.writer(f); w.writerow(names); w.writerows(body)
    for e, prm in M.items():
        fl = T.args_for(e, prm) + ["--fps", str(fps)]
        pl = subprocess.run([EXE, "--print_pline", "1"] + fl, capture_output=True, text=True).stdout.strip()
        pc = pd.read_csv(io.StringIO(subprocess.run([EXE, "--stream", small] + fl, capture_output=True, text=True).stdout))
        if tx("R") != "OK" or tx(pl) != "OK": sys.exit(f"no OK for P line of {e}: {pl[:80]}")
        got = []
        for r in body:
            vals = ",".join(r[lab:lab + 64]); resp = tx(f"D,{r[0]},{r[dcol]},{vals}" if dcol is not None else f"F,{r[0]},{vals}").split(",")
            if len(resp) < 6 or resp[0] != "R": sys.exit(f"bad reply on {e}/{sname}: {resp}")
            got.append((int(resp[2]), int(resp[3]), int(resp[5]), int(resp[4])))
        fw = pd.DataFrame(got, columns=["raw", "smooth", "static", "us"]); mm = {c: int((fw[c].values != pc[c].values).sum()) for c in ("raw", "smooth", "static")}
        ok = sum(mm.values()) == 0; bad += (not ok); us = fw.us.values
        rows_out.append(dict(stream=sname, method=e, frames=len(fw), ok=ok, mm_raw=mm["raw"], mm_smooth=mm["smooth"], mm_static=mm["static"], us_mean=us.mean(), us_median=np.median(us), us_p95=np.percentile(us, 95), us_max=us.max()))
        print(f"{'OK  ' if ok else 'FAIL'} {sname:24s} {e:11s} frames {len(fw)} mismatches raw/smooth/static {mm['raw']}/{mm['smooth']}/{mm['static']}  us mean {us.mean():.0f} p95 {np.percentile(us, 95):.0f} max {us.max()}")
    os.remove(small)

df = pd.DataFrame(rows_out); df.to_csv(a.md.replace(".md", ".csv"), index=False)
L = [f"# esp32_check.md - frozen methods, link: {link}", "", f"params_frozen.json; streams {a.streams}; frames per stream {a.frames or 'all'}. Counts compared with run_pc frame by frame.", "",
     "## Parity (mismatching frames, summed over streams; 0 = identical)", "", "| Method | frames | raw | smooth | static | all OK |", "|---|---|---|---|---|---|"]
for e in M:
    d = df[df.method == e]; L.append(f"| {e} | {d.frames.sum()} | {d.mm_raw.sum()} | {d.mm_smooth.sum()} | {d.mm_static.sum()} | {'yes' if d.ok.all() else 'NO'} |")
L += ["", "## Time inside filt.process() per frame (microseconds; mean over frames, worst stream for p95/max)", "", "| Method | mean | median | p95 | max | % of a 100 ms frame period (10 Hz) at p95 |", "|---|---|---|---|---|---|"]
for e in M:
    d = df[df.method == e]; L.append(f"| {e} | {d.us_mean.mean():.0f} | {d.us_median.mean():.0f} | {d.us_p95.max():.0f} | {d.us_max.max():.0f} | {d.us_p95.max() / 1000:.2f} |")
L += ["", "Memory (fill in from your machine): Arduino IDE 'Global variables use N bytes' = ____ ; sizeof_filter.exe table = ____ (8x8 filter object is ~41.6 KB on a 64-bit PC; 16x16 would be ~166 KB and is unlikely to fit as a static global on an ESP32).",
      "Limits: timing covers filt.process() only (no parsing or serial); it is for the dev streams (few simultaneous blobs); worst-case frames with many blobs/tracks may take longer."]
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", a.md); sys.exit(1 if bad else 0)
