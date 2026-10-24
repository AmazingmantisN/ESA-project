"""Stream a stream CSV through the firmware's serial protocol and compare with run_pc, frame for frame.

Two modes:
  --shim ./fw          a PC build of thermal_poc.ino with a fake Serial (what Claude used; no hardware needed)
  --port COM7          the REAL ESP32 (same checks; needs pyserial and the sketch flashed)
Usage (from pc_test/):  python check_firmware_protocol.py --shim /tmp/shim/fw --stream ../data/streams/dev_single_laptop_weak.csv [--frames 600]
It runs several parameter sets (v1 defaults, tuned ours, B-paper x3 time bases, B-code, B-code as published,
DHT offset 0.2) and reports mismatches in raw count, smoothed count and static count. Exit code 0 = identical.
"""
import argparse, csv, io, os, subprocess, sys, time
import pandas as pd

ap = argparse.ArgumentParser()
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--shim"); g.add_argument("--port")
ap.add_argument("--stream", required=True); ap.add_argument("--frames", type=int, default=600); ap.add_argument("--baud", type=int, default=921600)
ap.add_argument("--fps", default="3.8")
a = ap.parse_args()
exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_pc.exe" if os.name == "nt" else "run_pc")

class Link:
    def __init__(self):
        if a.shim:
            self.p = subprocess.Popen([a.shim], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
            self.tx = lambda s: (self.p.stdin.write(s + "\n"), self.p.stdin.flush(), self.p.stdout.readline().strip())[2]
        else:
            import serial
            ser = serial.Serial(a.port, a.baud, timeout=2); time.sleep(2.5); ser.reset_input_buffer()
            self.tx = lambda s: (ser.write((s + "\n").encode()), ser.readline().decode(errors="ignore").strip())[1]
link = Link()

rows = list(csv.reader(open(a.stream)))
names, body = rows[0], rows[1:1 + a.frames]
lab = 0
while not (len(names[lab]) > 1 and names[lab][0] == "p" and names[lab][1].isdigit()): lab += 1
dcol = names.index("dht") if "dht" in names else None
small = os.path.join(os.path.dirname(os.path.abspath(a.stream)), "_proto_check.csv")
with open(small, "w", newline="") as f:
    w = csv.writer(f); w.writerow(names); w.writerows(body)

SETS = [
    ("v1 defaults", []),
    ("ours tuned (4 s, drift 0.4, contrast 1.0, k 0.5)", ["--window_s", "4", "--drift", "0.4", "--contrast", "1.0", "--k", "0.5"]),
    ("mean+std ablation", ["--robust", "0"]),
    ("B-paper frames", ["--preset", "bpaper", "--timebase", "frames"]),
    ("B-paper paper-time", ["--preset", "bpaper", "--timebase", "paper"]),
    ("B-paper loop-time", ["--preset", "bpaper", "--timebase", "loop"]),
    ("B-paper DHT+0.2", ["--preset", "bpaper", "--dht_offset", "0.2"]),
    ("B-code intended", ["--preset", "bcode"]),
    ("B-code as published", ["--preset", "bcode_asis"]),
    ("Ours-v2 nested defaults", ["--pers_mode", "3"]),
    ("Ours-v2 policy 4 + global assign", ["--pers_mode", "3", "--assign_mode", "1", "--window_s", "4", "--drift", "0.4", "--persist_frames", "8", "--hyst_frames", "3", "--cand_policy", "4"]),
    ("Ours-v2 origin gate", ["--pers_mode", "3", "--window_s", "4", "--drift", "0.4", "--persist_frames", "15", "--hyst_frames", "4", "--cand_policy", "2"]),
    ("Ours-v2 size gate + merge", ["--pers_mode", "3", "--assign_mode", "1", "--window_s", "4", "--drift", "0.4", "--persist_frames", "10", "--hyst_frames", "4", "--cand_policy", "3", "--cand_min_area", "500", "--cand_max_peak", "4", "--merge_area", "700"]),
]
bad = 0
for label, flags in SETS:
    if dcol is None and any(x in flags for x in ("--preset",)):
        print(f"skip {label}: stream has no dht column"); continue
    fl = flags + ["--fps", a.fps]
    pl = subprocess.run([exe, "--print_pline", "1"] + fl, capture_output=True, text=True).stdout.strip()
    pc = pd.read_csv(io.StringIO(subprocess.run([exe, "--stream", small] + fl, capture_output=True, text=True).stdout))
    if link.tx("R") != "OK": sys.exit("no OK for R")
    if flags and link.tx(pl) != "OK": sys.exit("no OK for P: " + pl)
    got = []
    for r in body:
        vals = ",".join(r[lab:])
        msg = f"D,{r[0]},{r[dcol]},{vals}" if dcol is not None else f"F,{r[0]},{vals}"
        resp = link.tx(msg).split(",")
        got.append((int(resp[2]), int(resp[3]), int(resp[5])))
    fw = pd.DataFrame(got, columns=["raw", "smooth", "static"])
    m = [(c, int((fw[c].values != pc[c].values).sum())) for c in ("raw", "smooth", "static")]
    ok = all(n == 0 for _, n in m); bad += (not ok)
    print(f"{'OK  ' if ok else 'FAIL'} {label:50s} frames {len(fw)}  mismatches raw/smooth/static: {m[0][1]}/{m[1][1]}/{m[2][1]}")
os.remove(small)
sys.exit(1 if bad else 0)
