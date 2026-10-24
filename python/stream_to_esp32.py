"""Send a stream CSV to the ESP32 one frame at a time and log what it answers.

pip install pyserial
Usage: python stream_to_esp32.py --port COM7 --stream ../data/streams/dev_single_clean.csv --out ../data/res_esp32.csv

PARAMETERS: every other flag is passed straight to run_pc, so the ESP32 gets EXACTLY the settings the PC
run uses (including --preset bpaper|bcode|bcode_asis, --timebase, --window_s, --drift, ...). run_pc resolves them
to frames and prints the firmware's P line (run_pc --print_pline); that line is sent before streaming.
  python stream_to_esp32.py --port COM7 --stream S.csv --out R.csv --window_s 4 --drift 0.4 --contrast 1.0 --k 0.5
  python stream_to_esp32.py --port COM7 --stream S.csv --out R.csv --preset bpaper --timebase paper
Seconds-based flags need --fps (or a <stream>.json sidecar with fps). No parameter flags = firmware defaults.
--dry-run prints the P line and exits without touching the serial port.

Protocol (text lines, '\\n' terminated)
  PC -> ESP32:  F,<id>,<v0>...      frame (no DHT)      D,<id>,<dht>,<v0>...   frame with DHT (used when the stream has a dht column)
                R                   reset filter state  P,<20 or 27 comma-separated parameters>   set parameters (also resets), reply OK
  ESP32 -> PC:  R,<id>,<raw_count>,<smoothed_count>,<microseconds_in_filter>,<static_count>
"""
import argparse, csv, json, os, subprocess, sys, time

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--port", required=True); ap.add_argument("--baud", type=int, default=921600)
ap.add_argument("--stream", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--dry-run", action="store_true")
a, rest = ap.parse_known_args()

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = next((p for p in (os.path.join(HERE, "..", "pc_test", n) for n in ("run_pc.exe", "run_pc")) if os.path.exists(p)), None)

pline = None
if rest:
    if EXE is None: raise SystemExit("parameter flags need ../pc_test/run_pc(.exe) to resolve them: build it first")
    if "--fps" not in rest:
        try: rest += ["--fps", str(float(json.load(open(a.stream[:-4] + ".json"))["fps"]))]
        except Exception: pass
    r = subprocess.run([EXE, "--print_pline", "1"] + rest, capture_output=True, text=True)
    if r.returncode or not r.stdout.startswith("P,"): raise SystemExit("run_pc rejected the flags:\n" + (r.stderr or r.stdout))
    pline = r.stdout.strip()
print("parameters:", pline if pline else "(all firmware defaults)")
if a.dry_run: raise SystemExit(0)

import serial
ser = serial.Serial(a.port, a.baud, timeout=2)
time.sleep(2.5)                      # ESP32 reboots when the port opens
ser.reset_input_buffer()
ser.write(b"R\n")
ack = ser.readline().decode(errors="ignore").strip()
if ack != "OK":
    raise SystemExit(f"ESP32 did not acknowledge reset (got {ack!r}). Check port/baud/firmware.")
if pline:
    ser.write((pline + "\n").encode())
    ack = ser.readline().decode(errors="ignore").strip()
    if ack != "OK": raise SystemExit(f"ESP32 did not accept parameters (got {ack!r}). Is the sketch current (v2)?")

with open(a.stream) as fin, open(a.out, "w", newline="") as fout:
    rd = csv.reader(fin); names = next(rd)
    lab = 0
    while lab < len(names) and not (len(names[lab]) > 1 and names[lab][0] == "p" and names[lab][1].isdigit()): lab += 1
    dcol = names.index("dht") if "dht" in names else None
    w = csv.writer(fout); w.writerow(["frame", "humans", "injected", "raw", "smooth", "us", "static"])
    for i, row in enumerate(rd):
        fid, humans, injected, vals = row[0], row[1], row[2], row[lab:]
        msg = f"D,{fid},{row[dcol]},{','.join(vals)}\n" if dcol is not None else f"F,{fid},{','.join(vals)}\n"
        ser.write(msg.encode())
        resp = ser.readline().decode(errors="ignore").strip().split(",")
        if len(resp) not in (5, 6) or resp[0] != "R":
            raise SystemExit(f"bad reply at frame {fid}: {resp}")
        w.writerow([fid, humans, injected, resp[2], resp[3], resp[4], resp[5] if len(resp) == 6 else ""])
        if i % 500 == 0: print("frame", i)
print("done ->", a.out)
