"""LINAIGE declared re-tune, following linaige_retune_protocol.md / .json (commit and push BOTH before --tune).

  python linaige_retune.py --tune --jobs 18      # step 1: tunes all four methods on Session 1 ONLY -> params_linaige_session1.json (+ .sha256), tuning_results_linaige/
  (commit params_linaige_session1.json and its .sha256, push)
  python linaige_retune.py --test --jobs 18      # step 2: THE one scored run on Sessions 2-5 -> linaige_retune_results.md, linaige_retune_test.lock

  --quick works with either step for a tiny smoke run (not the protocol run; writes *_QUICK files, no lock, no official params file).
  Needs linaige_streams/ (python linaige_run.py <linaige folder> --convert-only builds it; that step scores nothing) and pc_test/run_pc(.exe).

Tuning refuses any stream outside Session 1. The test step refuses to run twice, refuses if the params file was edited after tuning,
and scores two arms per method on Sessions 2-5: the FROZEN v1.4 parameters (recomputed, must equal linaige_results.md) and the Session-1-tuned parameters.
"""
import argparse, glob, hashlib, io, json, math, os, random, re, subprocess, sys, time, datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--tune", action="store_true"); ap.add_argument("--test", action="store_true"); ap.add_argument("--quick", action="store_true")
ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2)); ap.add_argument("--boot", type=int, default=2000)
ap.add_argument("--protocol", default=os.path.join(ROOT, "linaige_retune_protocol.json"))
ap.add_argument("--raw", help="optional: the folder with the original LINAIGE csv files, only used to print the room of each session (from the file names)")
a = ap.parse_args()
if a.tune == a.test: sys.exit("give exactly one of --tune or --test")
PROT = os.path.abspath(a.protocol); P = json.load(open(PROT)); SUF = "_QUICK" if a.quick else ""
RES = os.path.join(ROOT, P["results_dir"] + SUF); PARAMS = os.path.join(ROOT, P["frozen_params_output"].replace(".json", SUF + ".json")); PSHA = PARAMS[:-5] + ".sha256"
LOCK = os.path.join(ROOT, P["test_lock"]); OUT = os.path.join(ROOT, P["test_results"].replace(".md", SUF + ".md"))
METHODS = ["ours", "ours_v2", "bpaper", "bcode"]; LABEL = {"ours": "Ours-v1", "ours_v2": "Ours-v2", "bpaper": "B-paper", "bcode": "B-code"}
HARD = {}

def sha(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()
def find_exe(): return next((p for p in (os.path.join(ROOT, "pc_test", n) for n in ("run_pc.exe", "run_pc")) if os.path.exists(p)), None)

# ------------------------------------------------------------------ tuning (Session 1 only)
def winit(glob_pat, prot):
    T.setup(glob_pat, prot)
    for f in T.G["files"]: HARD[f] = np.load(f[:-4] + "_hard.npy")

def score(task):
    """per Session-1 stretch: (false frames, missed frames, scored frames). Warm-up and 'h' frames are not scored."""
    entry, c = task; Pp = T.G["P"]; out = []
    for f in T.G["files"]:
        fps = T.G["FPS"][f]
        r = subprocess.run([T.G["EXE"], "--stream", f, "--fps", str(fps)] + T.args_for(entry, c), capture_output=True, text=True)
        if r.returncode: raise RuntimeError(f"run_pc failed on {os.path.basename(f)}: {r.stderr[:300]}")
        d = pd.read_csv(io.StringIO(r.stdout)); ok = np.ones(len(d), bool); ok[:math.ceil(Pp["scoring"]["warmup_s"] * fps)] = False; ok &= ~HARD[f][:len(d)]
        s = d.smooth.values[ok]; h = d.humans.values[ok]; out.append((int((s > h).sum()), int((s < h).sum()), int(ok.sum())))
    return out

def summarise(res):
    fa = sum(x[0] for x in res); mi = sum(x[1] for x in res); n = sum(x[2] for x in res); mn = P["scoring"]["worst_min_scored_frames"]
    w = [(x[0] + x[1]) / x[2] * 100 for x in res if x[2] >= mn] or [(x[0] + x[1]) / max(1, x[2]) * 100 for x in res]
    return dict(false=fa / n * 100, missed=mi / n * 100, total=(fa + mi) / n * 100, worst=max(w), n=n)

def tune():
    if os.path.exists(LOCK) and not a.quick: sys.exit(f"{LOCK} exists: the test has been run, tuning is closed.")
    if os.path.exists(PARAMS) and not a.quick: sys.exit(f"{PARAMS} exists: Session-1 tuning has been done; delete nothing, it is the frozen record.")
    glob_pat = os.path.join(ROOT, P["train_glob"]); T.setup(glob_pat, PROT)   # refuses forbidden names
    for f in T.G["files"]: HARD[f] = np.load(f[:-4] + "_hard.npy")
    names = [os.path.basename(f)[:-4] for f in T.G["files"]]
    if any(not n.startswith("Session1_") for n in names): sys.exit("tuning stream outside Session 1: " + str(names))
    os.makedirs(RES, exist_ok=True)
    n1 = 12 if a.quick else P["budget_trials_per_entry"]; top_k = 2 if a.quick else P["stage2"]["top_k"]; per = 3 if a.quick else P["stage2"]["perturbations_per_seed"]
    FZ = json.load(open(os.path.join(ROOT, "params_frozen.json"))); psha = sha(PROT); cand = {}; t0 = time.time()
    print(f"protocol L1.0 sha256 {psha[:16]}...  {n1}+{top_k}x{per} trials/entry ({'QUICK TEST, not the protocol run' if a.quick else 'OFFICIAL'})  Session-1 stretches {len(names)}  jobs {a.jobs}")
    with ProcessPoolExecutor(a.jobs, initializer=winit, initargs=(glob_pat, PROT)) as pool:
        for entry in METHODS:
            rng = random.Random(P["rng_seed"]); ref = P["entries"][entry]["reference"]
            ref_s = summarise(score((entry, ref))); fz_s = summarise(score((entry, FZ["candidates"][entry]["params"])))
            cfgs = [T.sample(entry, rng) for _ in range(n1)]; res = list(pool.map(score, [(entry, c) for c in cfgs], chunksize=2))
            rows = [dict(trial=i, stage=1, **c, res=r) for i, (c, r) in enumerate(zip(cfgs, res))]
            top = sorted(rows, key=lambda r: (summarise(r["res"])["total"], r["trial"]))[:top_k]
            rng2 = random.Random(P["rng_seed"] + P["stage2"]["rng_seed_offset"])
            cfg2 = [T.perturb(entry, {k: t[k] for k in P["entries"][entry]["space"]}, rng2) for t in top for _ in range(per)]
            res2 = list(pool.map(score, [(entry, c) for c in cfg2], chunksize=2))
            rows += [dict(trial=n1 + i, stage=2, **c, res=r) for i, (c, r) in enumerate(zip(cfg2, res2))]
            for r in rows:
                s = summarise(r.pop("res")); r.update(s)
            df = pd.DataFrame(rows); df.to_csv(os.path.join(RES, f"trials_{entry}.csv"), index=False, float_format="%.4f")
            pool_ = df[df.total <= df.total.min() + 0.10]; b = pool_.sort_values(["worst", "trial"]).iloc[0]
            bc = {k: (b[k].item() if hasattr(b[k], "item") else b[k]) for k in P["entries"][entry]["space"]}; t10 = df.sort_values("total").head(10)
            cand[entry] = {"label": P["entries"][entry]["label"], "params": bc, "session1_false": b["false"], "session1_missed": b["missed"], "session1_total": b["total"],
                           "session1_worst_stretch": b["worst"], "winner_stage": int(b["stage"]), "stage1_best_total": df[df.stage == 1].total.min(),
                           "untuned_reference_total": ref_s["total"], "frozen_v14_total_on_session1": fz_s["total"], "edge_params": T.edge_flags(entry, bc),
                           "top10_total_range": [t10.total.min(), t10.total.max()], "trials": len(df), "scored_frames": int(b["n"])}
            print(f"== {LABEL[entry]} ({time.time() - t0:.0f} s): Session-1 total {b['total']:.2f}% (false {b['false']:.2f}, missed {b['missed']:.2f}); frozen v1.4 params on Session 1: {fz_s['total']:.2f}; "
                  f"untuned reference {ref_s['total']:.2f}; edge {cand[entry]['edge_params'] or 'none'}")
    rec = {"protocol_version": P["protocol_version"], "protocol_json_sha256": psha, "tuned_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "official_run": not a.quick, "train_streams": names, "candidates": cand, "FROZEN_BEFORE_SESSIONS_2_TO_5_WERE_RE-SCORED": True}
    json.dump(rec, open(PARAMS, "w"), indent=2, default=float); h = sha(PARAMS); open(PSHA, "w").write(h + "\n")
    md = [f"# LINAIGE re-tune: Session 1 tuning ({'QUICK' if a.quick else 'official'}, {datetime.datetime.now():%d %b %Y %H:%M})", "",
          f"protocol sha256 {psha}", f"params file sha256 {h}", "",
          "| Method | tuned params (Session 1) | Session-1 total % | of which false / missed | frozen v1.4 params on Session 1 | untuned reference | edge-limited |", "|---|---|---|---|---|---|---|"]
    for m in METHODS:
        c = cand[m]; md.append(f"| {LABEL[m]} | {json.dumps(c['params'])} | {c['session1_total']:.2f} | {c['session1_false']:.2f} / {c['session1_missed']:.2f} | {c['frozen_v14_total_on_session1']:.2f} | {c['untuned_reference_total']:.2f} | {', '.join(c['edge_params']) or 'none'} |")
    md += ["", "Session-1 numbers are in-sample (the tuning set); they say nothing about transfer. Commit params_linaige_session1.json and its .sha256 BEFORE running --test."]
    open(os.path.join(ROOT, "linaige_retune_tuning" + SUF + ".md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"\nwrote {PARAMS}\nsha256 {h}\nwrote {os.path.join(ROOT, 'linaige_retune_tuning' + SUF + '.md')}\nNow: git add params_linaige_session1.json params_linaige_session1.sha256 linaige_retune_tuning.md; commit; push. Then --test.")

# ------------------------------------------------------------------ test (Sessions 2-5, one run)
KEYS = ["total", "MAE", "exact", "F1", "BAS"]
def mets(p, t):
    if len(p) == 0: return dict(total=np.nan, MAE=np.nan, exact=np.nan, F1=np.nan, BAS=np.nan)
    fa = (p > t).mean() * 100; mi = (p < t).mean() * 100; po, to = p > 0, t > 0; tp = (po & to).sum(); fp = (po & ~to).sum(); fn = (~po & to).sum()
    f1 = 2 * tp / (2 * tp + fp + fn) * 100 if (2 * tp + fp + fn) else np.nan
    return dict(total=fa + mi, MAE=np.abs(p - t).mean(), exact=(p == t).mean() * 100, F1=f1, BAS=np.mean([(p[t == c] == c).mean() for c in np.unique(t)]) * 100)

def test():
    if os.path.exists(LOCK) and not a.quick: sys.exit(f"{LOCK} exists: the Sessions 2-5 test has already been run and is not repeated.")
    if not os.path.exists(PARAMS) or not os.path.exists(PSHA): sys.exit("run --tune first (params file missing)")
    if sha(PARAMS) != open(PSHA).read().strip(): sys.exit("params file differs from its recorded sha256: it was edited after tuning. Restore it from git.")
    TUNED = json.load(open(PARAMS))["candidates"]; FZ = json.load(open(os.path.join(ROOT, "params_frozen.json")))["candidates"]
    T.G["P"] = P; T.G["EXE"] = find_exe()
    if T.G["EXE"] is None: sys.exit("build pc_test/run_pc first")
    sd = os.path.join(ROOT, P["streams_dir"]); allf = sorted(glob.glob(os.path.join(sd, "Session*_*.csv")))
    test_streams = [os.path.basename(f)[:-4] for f in allf if os.path.basename(f).split("_")[0] in P["test_sessions"]]
    if not test_streams or any(n.startswith("Session1_") for n in test_streams): sys.exit("test streams wrong: " + str(test_streams))
    sess_of = {n: n.split("_")[0] for n in test_streams}; rng = np.random.default_rng(20261025)
    ARMS = [(m, w) for m in METHODS for w in ("frozen", "tuned")]; aname = lambda m, w: f"{m}@{w}"

    def run(n, m, w):
        fps = float(json.load(open(os.path.join(sd, n + ".json")))["fps"]); c = (FZ if w == "frozen" else TUNED)[m]["params"]
        r = subprocess.run([T.G["EXE"], "--stream", os.path.join(sd, n + ".csv"), "--fps", str(fps)] + T.args_for(m, c), capture_output=True, text=True)
        if r.returncode: sys.exit(f"run_pc failed: {m} {w} on {n}: {r.stderr[:200]}")
        d = pd.read_csv(io.StringIO(r.stdout)); hard = np.load(os.path.join(sd, n + "_hard.npy")); ok = np.ones(len(d), bool); ok[:math.ceil(P["scoring"]["warmup_s"] * fps)] = False; ok &= ~hard[:len(d)]
        return d.smooth.values.astype(int), d.humans.values.astype(int), ok, fps
    jobs = [(n, m, w) for n in test_streams for (m, w) in ARMS]
    with ThreadPoolExecutor(a.jobs) as ex: R = {(n, aname(m, w)): r for (n, m, w), r in zip(jobs, ex.map(lambda x: run(*x), jobs))}
    for n in test_streams:
        p, t, ok, fps = R[(n, aname("ours", "frozen"))]; R[(n, "always1")] = (np.ones_like(p), t, ok, fps); R[(n, "always0")] = (np.zeros_like(p), t, ok, fps)
    blocks = {}
    for n in test_streams:
        fps = R[(n, aname("ours", "frozen"))][3]; L = len(R[(n, aname("ours", "frozen"))][0]); b = max(2, int(20 * fps)); nb = math.ceil(L / b)
        s = rng.integers(0, max(1, L - b + 1), size=(a.boot, nb)); blocks[n] = (s[:, :, None] + np.arange(b)[None, None, :]).reshape(a.boot, -1)[:, :L]

    def pooled(arm, sel, idx=None):
        Pp, Tt = [], []
        for n in sel:
            p, t, ok, fps = R[(n, arm)]; ii = np.flatnonzero(ok) if idx is None else idx[n][ok[idx[n]]]
            Pp.append(p[ii]); Tt.append(t[ii])
        return np.concatenate(Pp), np.concatenate(Tt)
    BS = {}
    def boot(arm, sel_key, sel):
        if (arm, sel_key) not in BS:
            o = {k: np.empty(a.boot) for k in KEYS}
            for b in range(a.boot):
                mm = mets(*pooled(arm, sel, {n: blocks[n][b] for n in sel}))
                for k in KEYS: o[k][b] = mm[k]
            BS[(arm, sel_key)] = o
        return BS[(arm, sel_key)]
    ci = lambda x, f: f"[{np.nanpercentile(x, 2.5):{f}}, {np.nanpercentile(x, 97.5):{f}}]"
    def cell(arm, sel_key, sel, k, f):
        pt = mets(*pooled(arm, sel))[k]; return f"{pt:{f}} {ci(boot(arm, sel_key, sel)[k], f)}"
    def diff(a1, a2, k, f="+.2f", sel_key="ALL", sel=None):
        sel = sel or test_streams; d = boot(a1, sel_key, sel)[k] - boot(a2, sel_key, sel)[k]; pt = mets(*pooled(a1, sel))[k] - mets(*pooled(a2, sel))[k]
        return f"{pt:{f}} {ci(d, f)}"

    rooms = {}
    if a.raw:
        for f in os.listdir(a.raw):
            m_ = re.match(r"(Session\d+)_.*?(Room[A-Za-z0-9]+)", f)
            if m_: rooms[m_.group(1)] = m_.group(2)
    sessions = sorted(set(sess_of.values())); nsc = {s: sum(int(R[(n, 'ours@frozen')][2].sum()) for n in test_streams if sess_of[n] == s) for s in sessions}
    names_all = lambda m, w: aname(m, w)
    out = [f"# linaige_retune_results.md - declared re-tune on Session 1, one scored run on Sessions 2-5 ({datetime.datetime.now():%d %b %Y %H:%M}){' QUICK TEST' if a.quick else ''}", "",
           f"protocol sha256 {sha(PROT)}; params file sha256 {sha(PARAMS)}; frozen v1.4 file sha256 {sha(os.path.join(ROOT, 'params_frozen.json'))}.",
           f"Test: {len(test_streams)} stretches in {', '.join(sessions)}; scored frames per session: " + ", ".join(f"{s}{' (' + rooms[s] + ')' if s in rooms else ''} {nsc[s]}" for s in sessions) + f" (total {sum(nsc.values())}); 30 s warm-up per stretch, 'h' frames not scored.",
           f"Two arms per method: 'frozen' = v1.4 parameters (the earlier LINAIGE run; recomputed here) and 'tuned' = tuned on Session 1 under protocol L1.0 (same budget for all four). Baselines get dht = frame median + 1.2 C. Intervals: 20 s moving-block bootstrap ({a.boot}), paired across arms within stretches. Only {len(test_streams)} stretches: intervals are wide.", ""]
    hdr = "| Arm | Total error % | MAE | Exact-count % | Occupied F1 % | BAS % |\n|---|---|---|---|---|---|"
    out += ["## Sessions 2-5 pooled", "", hdr]
    for m in METHODS:
        for w in ("frozen", "tuned"):
            ar = aname(m, w); out.append(f"| {LABEL[m]} ({w}) | " + " | ".join(cell(ar, "ALL", test_streams, k, f) for k, f in zip(KEYS, [".1f", ".3f", ".1f", ".1f", ".1f"])) + " |")
    for ar, lab in (("always1", "always answer 1 person"), ("always0", "always answer 0 people")):
        out.append(f"| reference: {lab} | " + " | ".join(f"{mets(*pooled(ar, test_streams))[k]:{f}}" for k, f in zip(KEYS, [".1f", ".3f", ".1f", ".1f", ".1f"])) + " |")
    out += ["", "## Paired change from re-tuning (tuned minus frozen; negative total error / positive exact = re-tuning helped)", "", "| Method | total error, points | exact-count, points | occupied F1, points |", "|---|---|---|---|"]
    for m in METHODS:
        out.append(f"| {LABEL[m]} | {diff(aname(m, 'tuned'), aname(m, 'frozen'), 'total')} | {diff(aname(m, 'tuned'), aname(m, 'frozen'), 'exact')} | {diff(aname(m, 'tuned'), aname(m, 'frozen'), 'F1')} |")
    out += ["", "## Paired differences between methods, tuned arms (negative total error = first method better)", "", "| Comparison | total error, points | exact-count, points |", "|---|---|---|"]
    for x, y in (("ours", "bpaper"), ("ours", "bcode"), ("ours_v2", "bpaper"), ("ours_v2", "bcode"), ("ours_v2", "ours")):
        out.append(f"| {LABEL[x]} - {LABEL[y]} | {diff(aname(x, 'tuned'), aname(y, 'tuned'), 'total')} | {diff(aname(x, 'tuned'), aname(y, 'tuned'), 'exact')} |")
    out += ["", "## Per session (descriptive: one to two stretches each; total error % and exact-count %)", "", "| Arm | " + " | ".join(f"{s}{' (' + rooms[s] + ')' if s in rooms else ''}" for s in sessions) + " |", "|---|" + "---|" * len(sessions)]
    for m in METHODS:
        for w in ("frozen", "tuned"):
            ar = aname(m, w); cells = []
            for s in sessions:
                sel = [n for n in test_streams if sess_of[n] == s]; cells.append(f"{cell(ar, s, sel, 'total', '.1f')} / {cell(ar, s, sel, 'exact', '.1f')}")
            out.append(f"| {LABEL[m]} ({w}) | " + " | ".join(cells) + " |")
    out += ["", "## By true count, tuned arms (share of scored frames where the smoothed count equals the truth / mean count produced)", "", "| True count | scored frames | " + " | ".join(LABEL[m] for m in METHODS) + " |", "|---|---|" + "---|" * len(METHODS)]
    for c in range(4):
        cells = []; nfr = 0
        for m in METHODS:
            p, t = pooled(aname(m, "tuned"), test_streams); s_ = t == c; nfr = int(s_.sum()); cells.append(f"{(p[s_] == c).mean() * 100:.1f} / {p[s_].mean():.2f}" if nfr else "n/a")
        out.append(f"| {c} | {nfr} | " + " | ".join(cells) + " |")
    out += ["", "Consistency check: the 'frozen' arm per-session numbers must equal the matching rows of linaige_results.md (same code, same parameters). Reading guide: this is a declared follow-up tuned on one session; it shows whether the methods can adapt to a ceiling-mounted geometry, not how they would do in a room they have never seen with parameters they have never seen. Report whatever it shows."]
    open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
    if not a.quick: open(LOCK, "w").write(f"LINAIGE re-tune test done {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}; params sha256 {sha(PARAMS)}\n")
    print("\nwrote", OUT, "" if a.quick else "and " + LOCK + " (the test is now used up)")

if __name__ == "__main__":
    tune() if a.tune else test()
