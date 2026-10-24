"""Step 5c guarantees, checked on real streams (dev_* only: equality checks have no reason to open test_*).

 1. NESTED: Ours-v2 (--pers_mode 3) with persist 1 frame, hyst 1 frame, cand_policy 0, merge_area 0 gives
    EXACTLY the same raw / smoothed / static counts as the v1 rule (--pers_mode 0), on many random parameter sets.
    So v2 is a superset of v1: tuning it cannot do worse than v1 except through search noise.
 2. REGRESSION (optional, --ref OLD_RUN_PC): the baseline presets (B-paper x3 time bases, B-code, B-code as published)
    and the v1 rule give identical output with the new run_pc and with the previous one, so Step 5c changed nothing else.
Usage (from pc_test/, after building run_pc):  python check_v2_nested.py [--ref path\\to\\old\\run_pc.exe] [--n 40]
Exit code 0 only if every comparison is identical.
"""
import argparse, glob, io, os, random, subprocess, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); exe = ".exe" if os.name == "nt" else ""
ap = argparse.ArgumentParser(); ap.add_argument("--ref"); ap.add_argument("--n", type=int, default=40); ap.add_argument("--seed", type=int, default=11)
ap.add_argument("--streams", default=os.path.join(HERE, "..", "data", "streams", "dev_*.csv")); a = ap.parse_args()
NEW = os.path.join(HERE, "run_pc" + exe)
files = sorted(glob.glob(a.streams)) or sys.exit("no streams match " + a.streams)
if any(os.path.basename(f).startswith(("test_", "expl_")) for f in files): sys.exit("refusing test_/expl_ streams")

def run(exe_path, stream, flags):
    r = subprocess.run([exe_path, "--stream", stream, "--fps", "3.8"] + flags, capture_output=True, text=True)
    if r.returncode: sys.exit(f"{exe_path} failed: {r.stderr}")
    return pd.read_csv(io.StringIO(r.stdout))

def same(x, y): return len(x) == len(y) and all((x[c].values == y[c].values).all() for c in ("raw", "smooth", "static"))

rng = random.Random(a.seed); bad = total = 0
# 1. nested
sets = [[], ["--robust", "0"]]
for _ in range(a.n):
    sets.append(["--k", str(rng.choice([0, 0.07, 0.5, 1, 2, 3])), "--contrast", str(rng.choice([0.8, 1.0, 1.04, 1.5, 2.5])),
                 "--window_s", str(rng.choice([1.5, 3, 4, 6, 8.9, 12])), "--drift", str(rng.choice([0.08, 0.16, 0.4, 0.48, 0.8, 1.5])),
                 "--maxmissed_s", str(rng.choice([0.5, 1, 2.5])), "--smooth_s", str(rng.choice([0, 0.5, 1.3])),
                 "--minarea", str(rng.choice([20, 40, 80])), "--match", str(rng.choice([1.0, 1.5, 2.5]))])
sub = files[:: max(1, len(files) // 5)]
for fl in sets:
    for f in sub:
        total += 1
        if not same(run(NEW, f, fl), run(NEW, f, fl + ["--pers_mode", "3", "--persist_frames", "1", "--hyst_frames", "1", "--cand_policy", "0", "--merge_area", "0"])):
            bad += 1; print("NESTED MISMATCH", os.path.basename(f), fl)
print(f"nested (mode 3 defaults == mode 0): {total} comparisons, mismatches: {bad}")

# 2. regression against the previous build
if a.ref:
    t2 = b2 = 0
    regs = [[]] + [["--preset", "bpaper", "--timebase", tb] for tb in ("frames", "paper", "loop")] + [["--preset", "bpaper", "--dht_offset", "0.2"],
            ["--preset", "bcode"], ["--preset", "bcode_asis"], ["--preset", "bcode", "--npersist", "10", "--drift", "0.14"],
            ["--preset", "bpaper", "--timebase", "paper", "--drift", "0.28", "--smooth_s", "0", "--maxmissed_s", "0.5"]] + sets[2:12]
    for fl in regs:
        for f in files:
            if "--preset" in fl and "dht" not in open(f).readline(): continue
            t2 += 1
            if not same(run(NEW, f, fl), run(a.ref, f, fl)):
                b2 += 1; print("REGRESSION MISMATCH", os.path.basename(f), fl)
    print(f"regression vs previous build: {t2} comparisons, mismatches: {b2}"); bad += b2; total += t2
sys.exit(1 if bad else 0)
