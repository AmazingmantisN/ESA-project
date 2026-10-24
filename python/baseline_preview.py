"""DEV-ONLY preview of the baseline presets (plan Step 5 sanity check). Refuses test_* streams.
Untuned: presets use the values from baseline_spec.md as they are. Not a result, a sanity check that the
reimplementation behaves as the spec says (static sources get locked, a seated person mostly does not).
Usage (from python/): python baseline_preview.py "../data/streams/dev_*.csv"
Columns: false% / missed% over scored frames; static% = frames with >=1 track classed static;
         locked-first = seconds until the first static flag (blank if never)."""
import glob, io, json, os, subprocess, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
EXE = next(p for p in (os.path.join(HERE, "..", "pc_test", n) for n in ("run_pc.exe", "run_pc")) if os.path.exists(p))
files = sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "../data/streams/dev_*.csv"))
if any("test_" in os.path.basename(f) for f in files): sys.exit("refusing test_* streams")
SETS = [("B-paper frames(100/15)", ["--preset", "bpaper", "--timebase", "frames"]),
        ("B-paper 10s/1.5s", ["--preset", "bpaper", "--timebase", "paper"]),
        ("B-paper 13s/2s", ["--preset", "bpaper", "--timebase", "loop"]),
        ("B-paper DHT+0.2 (frames)", ["--preset", "bpaper", "--dht_offset", "0.2"]),
        ("B-code intended", ["--preset", "bcode"]), ("B-code as published", ["--preset", "bcode_asis"])]
rows = []
for f in files:
    fps = json.load(open(f[:-4] + ".json"))["fps"]
    for label, fl in SETS:
        out = subprocess.run([EXE, "--stream", f, "--fps", str(fps)] + fl, capture_output=True, text=True, check=True).stdout
        d = pd.read_csv(io.StringIO(out)); d = d.iloc[10:]
        st = d.index[d["static"] > 0]
        rows.append((os.path.basename(f)[4:-4], label, (d.smooth > d.humans).mean() * 100, (d.smooth < d.humans).mean() * 100,
                     (d["static"] > 0).mean() * 100, (st[0] / fps) if len(st) else float("nan"), d.smooth.max()))
r = pd.DataFrame(rows, columns=["stream", "baseline", "false%", "missed%", "static%", "first_static_s", "max_count"])
print(r.to_string(index=False, float_format=lambda v: f"{v:.1f}"))
