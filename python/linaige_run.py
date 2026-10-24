"""LINAIGE transfer test, following linaige_protocol.md and linaige_protocol_amendment1.md (commit both BEFORE the real run).
FROZEN parameters only (params_frozen.json). No tuning. The real run happens ONCE: linaige_run.lock is written when results exist.

  step 1  python linaige_run.py "C:\\VIT life\\Project\\linaige" --convert-only     # builds the streams and prints what they hold; scores nothing
  step 2  python linaige_run.py "C:\\VIT life\\Project\\linaige" --run --jobs 18    # THE one scored run -> ..\\linaige_results.md, ..\\linaige_run.lock

Rules (amendment 1): sort each file by timestamp; split into stretches wherever the step exceeds 3 x the median step; keep stretches of at least 60 s;
30 s warm-up inside each stretch; frames with confidence 'h' (hard to label) stay in the stream but are not scored; truth = people_number;
B-paper / B-code get dht = frame median + 1.2 C (the offset measured in Papanashi's pod) - an assumption, stated in the results.
"""
import argparse, io, json, math, os, subprocess, sys, datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("linaige"); ap.add_argument("--convert-only", action="store_true"); ap.add_argument("--run", action="store_true")
ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--boot", type=int, default=2000)
ap.add_argument("--streams", default=os.path.join(ROOT, "linaige_streams")); ap.add_argument("--out", default=os.path.join(ROOT, "linaige_results.md"))
ap.add_argument("--lock", default=os.path.join(ROOT, "linaige_run.lock"))
a = ap.parse_args()
if a.convert_only == a.run: sys.exit("give exactly one of --convert-only or --run")
MIN_LEN, WARM, DHT_OFF = 60.0, 30.0, 1.2

def to_sec(s):
    h, m, x = str(s).split("_"); return int(h) * 3600 + int(m) * 60 + float(x)

def convert():
    os.makedirs(a.streams, exist_ok=True); meta = []; rows = []
    for f in sorted(x for x in os.listdir(a.linaige) if x.lower().endswith(".csv")):
        sess = f.split("_")[0]; d = pd.read_csv(os.path.join(a.linaige, f))
        t = np.array([to_sec(x) for x in d.timestamp], float)
        if (np.diff(t) < -43200).any(): t = np.where(np.arange(len(t)) > np.argmax(np.diff(t) < -43200), t + 86400, t)
        o = np.argsort(t, kind="stable"); d = d.iloc[o].reset_index(drop=True); t = t[o]
        dt = np.diff(t); med = float(np.median(dt[dt > 0])); fps = round(1 / med, 3)
        cut = np.flatnonzero((dt > 3 * med) | (dt <= 0)) + 1; segs = np.split(np.arange(len(t)), cut); k = 0
        pix = d[[f"pixel{i}" for i in range(64)]].values.astype(float)
        for s in segs:
            if len(s) < 2 or t[s[-1]] - t[s[0]] < MIN_LEN: continue
            k += 1; name = f"{sess}_{k:02d}"; P = pix[s]; dht = np.round(np.median(P, axis=1) + DHT_OFF, 1)
            out = pd.DataFrame({"frame": np.arange(len(s)), "humans": d.people_number.values[s].astype(int), "injected": 0, "dht": dht})
            for i in range(64): out[f"p{i}"] = P[:, i]
            out.to_csv(os.path.join(a.streams, name + ".csv"), index=False, float_format="%.2f")
            json.dump({"fps": fps, "session": sess, "start_s": float(t[s[0]]), "duration_s": float(t[s[-1]] - t[s[0]])}, open(os.path.join(a.streams, name + ".json"), "w"))
            np.save(os.path.join(a.streams, name + "_hard.npy"), (d.confidence.astype(str).values[s] == "h"))
            meta.append(name); rows.append((sess, name, len(s), t[s[-1]] - t[s[0]], int((d.confidence.astype(str).values[s] == "h").sum()), np.bincount(d.people_number.values[s].astype(int), minlength=4)))
    print(f"{len(meta)} stretches of at least {MIN_LEN:.0f} s written to {a.streams}\n")
    print("| Session | stretches | frames | seconds | hard frames | frames with 0 / 1 / 2 / 3 people |\n|---|---|---|---|---|---|")
    for sess in sorted({r[0] for r in rows}):
        R = [r for r in rows if r[0] == sess]; c = sum(r[5] for r in R)
        print(f"| {sess} | {len(R)} | {sum(r[2] for r in R)} | {sum(r[3] for r in R):.0f} | {sum(r[4] for r in R)} | {' / '.join(str(int(x)) for x in c)} |")
    return meta

if a.convert_only: convert(); print("\nNothing was scored. Paste this table back."); sys.exit(0)

# ---------------- the one scored run ----------------
if os.path.exists(a.lock): sys.exit(f"{a.lock} exists: the LINAIGE run has already been done and is not repeated.")
import tune_sweep as T
T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.join(ROOT, "tuning_protocol_v1.4.json"))
J = json.load(open(os.path.join(ROOT, "params_frozen.json"))); F = dict(J["candidates"])
METHODS = ["ours", "ours_v2", "bpaper", "bcode"]; LABEL = {"ours": "Ours-v1", "ours_v2": "Ours-v2", "bpaper": "B-paper", "bcode": "B-code"}
names = convert(); rng = np.random.default_rng(20261024)

def run(n, m):
    fps = float(json.load(open(os.path.join(a.streams, n + ".json")))["fps"])
    r = subprocess.run([T.G["EXE"], "--stream", os.path.join(a.streams, n + ".csv"), "--fps", str(fps)] + T.args_for(m, F[m]["params"]), capture_output=True, text=True)
    if r.returncode: sys.exit(f"run_pc failed: {m} on {n}: {r.stderr[:200]}")
    d = pd.read_csv(io.StringIO(r.stdout)); w = math.ceil(WARM * fps); hard = np.load(os.path.join(a.streams, n + "_hard.npy"))
    ok = np.ones(len(d), bool); ok[:w] = False; ok &= ~hard[:len(d)]
    return d.smooth.values.astype(int), d.humans.values.astype(int), ok, fps

with ThreadPoolExecutor(a.jobs) as ex: R = dict(zip([(n, m) for n in names for m in METHODS], ex.map(lambda x: run(*x), [(n, m) for n in names for m in METHODS])))

def mets(p, t):
    if len(p) == 0: return dict(total=np.nan, MAE=np.nan, exact=np.nan, F1=np.nan, BAS=np.nan)
    fa = (p > t).mean() * 100; mi = (p < t).mean() * 100; po, to = p > 0, t > 0; tp = (po & to).sum(); fp = (po & ~to).sum(); fn = (~po & to).sum()
    f1 = 2 * tp / (2 * tp + fp + fn) * 100 if (2 * tp + fp + fn) else np.nan
    return dict(total=fa + mi, MAE=np.abs(p - t).mean(), exact=(p == t).mean() * 100, F1=f1, BAS=np.mean([(p[t == c] == c).mean() for c in np.unique(t)]) * 100)
KEYS = ["total", "MAE", "exact", "F1", "BAS"]
sess_of = {n: n.split("_")[0] for n in names}

def pooled(sel, idx=None):
    P, Tt = [], []
    for n in sel:
        p, t, ok, fps = R[(n, cur)]; ii = np.flatnonzero(ok) if idx is None else idx[n]; ii = ii[ok[ii]] if idx is not None else ii
        P.append(p[ii]); Tt.append(t[ii])
    return np.concatenate(P), np.concatenate(Tt)

blocks = {}
for n in names:
    fps = R[(n, METHODS[0])][3]; L = len(R[(n, METHODS[0])][0]); b = max(2, int(20 * fps)); nb = math.ceil(L / b)
    s = rng.integers(0, max(1, L - b + 1), size=(a.boot, nb)); blocks[n] = (s[:, :, None] + np.arange(b)[None, None, :]).reshape(a.boot, -1)[:, :L]

out = [f"# linaige_results.md - one-shot transfer test, frozen parameters (run {datetime.datetime.now():%d %b %Y %H:%M})", "",
       f"params_frozen.json frozen_at {J.get('frozen_at')}. LINAIGE v2, {len(names)} continuous stretches >= {MIN_LEN:.0f} s; {WARM:.0f} s warm-up per stretch; frames marked 'h' (hard to label) not scored.",
       f"B-paper and B-code were given dht = frame median + {DHT_OFF} C (assumption, from Papanashi's pod). Intervals: 20 s moving-block bootstrap ({a.boot}), paired across methods, within stretches. Truth = people_number (0-3).", ""]
groups = [("ALL sessions pooled", names)] + [(s, [n for n in names if sess_of[n] == s]) for s in sorted(set(sess_of.values()))]
for title, sel in groups:
    out += [f"## {title}", "", "| Method | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |", "|---|---|---|---|---|---|"]
    for m in METHODS:
        cur = m; pt = mets(*pooled(sel)); bs = {k: [] for k in KEYS}
        for b in range(a.boot):
            mm = mets(*pooled(sel, {n: blocks[n][b] for n in sel}))
            for k in KEYS: bs[k].append(mm[k])
        cell = lambda k, f: f"{pt[k]:{f}} [{np.nanpercentile(bs[k], 2.5):{f}}, {np.nanpercentile(bs[k], 97.5):{f}}]"
        out.append(f"| {LABEL[m]} | {cell('total', '.1f')} | {cell('MAE', '.3f')} | {cell('exact', '.1f')} | {cell('F1', '.1f')} | {cell('BAS', '.1f')} |")
    out.append("")
out += ["## By true count (all sessions pooled): share of scored frames where the smoothed count equals the truth, and the mean count produced", "",
        "| True count | scored frames | " + " | ".join(f"{LABEL[m]} exact % / mean count" for m in METHODS) + " |", "|---|---|" + "---|" * len(METHODS)]
for c in range(4):
    cells = []; nfr = 0
    for m in METHODS:
        cur = m; p, t = pooled(names); sel_ = t == c; nfr = int(sel_.sum())
        cells.append(f"{(p[sel_] == c).mean() * 100:.1f} / {p[sel_].mean():.2f}" if nfr else "n/a")
    out.append(f"| {c} | {nfr} | " + " | ".join(cells) + " |")
out += ["", "Reading guide: LINAIGE is a ceiling-mounted sensor in other rooms, with up to 3 people and no placed heat sources; the frozen parameters were tuned on a corner-mounted sensor in one study pod. "
        "Counts of 2 or more people close together are expected to fail at 8x8. This is a transfer test, not a benchmark win."]
open(a.out, "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
open(a.lock, "w").write(f"LINAIGE run done {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}; params_frozen.json used as frozen\n")
print("\nwrote", a.out, "and", a.lock, "(the run is now used up)")
