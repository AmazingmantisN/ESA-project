"""Check that v2 with v1-style flags reproduces v1 EXACTLY (raw and smoothed counts, every frame).

Builds the v1 reference (pc_test/v1_ref) and v2 side by side, then compares them on streams over many
parameter sets (defaults, the mean+std ablation, and random draws of every v1 parameter).
Usage (from pc_test/):  python check_v1_equiv.py ["../data/streams/*.csv"] [--n 60]
Exit code 0 only if every comparison is identical.
"""
import argparse, glob, io, os, random, subprocess, sys, tempfile
import pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("streams", nargs="?", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "streams", "*.csv"))
ap.add_argument("--n", type=int, default=60); ap.add_argument("--seed", type=int, default=7)
a = ap.parse_args()
exe = ".exe" if os.name == "nt" else ""
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
V1 = os.path.join(HERE, "v1_ref", "run_pc_v1" + exe); V2 = os.path.join(HERE, "run_pc" + exe)
for cmd in (["g++", "-O2", "-std=c++17", "-o", f"v1_ref/run_pc_v1{exe}", "v1_ref/run_pc_v1.cpp"],
            ["g++", "-O2", "-std=c++17", "-o", f"run_pc{exe}", "run_pc.cpp"]):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit("build failed:\n" + r.stderr)

tmp = tempfile.mkdtemp()
files = []
for f in sorted(glob.glob(a.streams)):
    lines = open(f).read().splitlines()
    hdr = lines[0].split(",")
    if "dht" in hdr:                                  # v1 cannot read the dht column: write a copy without it
        k = hdr.index("dht")
        out = os.path.join(tmp, os.path.basename(f))
        with open(out, "w") as o:
            for ln in lines:
                c = ln.split(","); del c[k]; o.write(",".join(c) + "\n")
        files.append((f, out))
    else:
        files.append((f, f))
if not files: sys.exit("no streams match " + a.streams)

rng = random.Random(a.seed)
sets = [[], ["--robust", "0"]]
for _ in range(a.n):
    s = ["--k", str(rng.choice([0.5, 1, 2, 3])), "--contrast", str(rng.choice([1.0, 1.25, 1.5, 2.0, 2.5])),
         "--window", str(rng.choice([8, 15, 23, 30, 45])), "--drift", str(rng.choice([0.08, 0.16, 0.25, 0.4, 0.8])),
         "--maxmissed", str(rng.choice([2, 5, 10])), "--smooth", str(rng.choice([1, 3, 5, 9])),
         "--minarea", str(rng.choice([20, 40, 80])), "--match", str(rng.choice([1.0, 1.5, 2.5]))]
    if rng.random() < 0.25: s += ["--robust", "0"]
    sets.append(s)

def run(exe_path, stream, flags):
    r = subprocess.run([exe_path, "--stream", stream] + flags, capture_output=True, text=True)
    if r.returncode: sys.exit(f"{exe_path} failed: {r.stderr}")
    return pd.read_csv(io.StringIO(r.stdout))

bad = total = 0
for flags in sets:
    for orig, nodht in files[:: max(1, len(files) // 6)] if flags else files:
        v1 = run(V1, os.path.abspath(nodht), flags)
        v2 = run(V2, os.path.abspath(orig), flags)   # v2 on the ORIGINAL stream (with dht column)
        total += 1
        if not (len(v1) == len(v2) and (v1.raw.values == v2.raw.values).all() and (v1.smooth.values == v2.smooth.values).all()):
            bad += 1; print("MISMATCH", os.path.basename(orig), flags)
print(f"{total} comparisons ({len(sets)} parameter sets), mismatches: {bad}")
sys.exit(1 if bad else 0)
