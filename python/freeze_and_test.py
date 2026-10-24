"""Step 8: freeze the protocol-v1.4 winners, then score the held-out test_* streams exactly once.

  python freeze_and_test.py freeze                  # writes ..\\params_frozen.json from ..\\tuning_results_v14 (refuses to overwrite)
  python freeze_and_test.py test --dry-run          # rehearsal on the 10 ORIGINAL DEV streams -> ..\\dry_run\\ (no lock, safe to repeat)
  python freeze_and_test.py test                    # THE one test run on data\\streams\\test_*.csv -> ..\\test_results.md/.csv, then writes ..\\test_run.lock

Safeguards: freeze checks that the candidates file comes from an official v1.4 run with the current protocol json/md hashes; test refuses to run if params_frozen.json is
missing or changed since freezing, if test_run.lock or test_results.md already exists, or if it does not find exactly the 10 test streams. After the real run the lock stays;
any later look at test_* must be a new, openly declared analysis, not a re-tune.

Scoring is identical to tuning: first 30 s not scored, error = false% + missed% of the smoothed count vs the true number of people, each stream weighted equally.
Uncertainty: a moving-block bootstrap (20 s blocks, 2000 resamples, same resampled blocks for every method so differences are paired) gives 95 % intervals.
"""
import argparse, datetime, glob, hashlib, io, json, math, os, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T

PROT = os.path.join(ROOT, "tuning_protocol_v1.4.json"); PROT_MD = os.path.join(ROOT, "tuning_protocol_v1.4.md")
FROZEN = os.path.join(ROOT, "params_frozen.json"); LOCK = os.path.join(ROOT, "test_run.lock")
ENTRIES = ["ours", "ours_v2", "bcode", "bpaper"]; PUB = "bcode_asis"
NOTE = ("Ours-v2 is the protocol-v1.4 winner, chosen by the user on 23 Oct 2026 over the v1.3 winner. The R1 tie-break in the v1.4 protocol (v1.4 not better than v1.3 on the "
        "held-out 'all except walker' row, so the earlier winner stays) would have kept the v1.3 winner; the deviation is deliberate and recorded: that row is dominated by jitter_m, "
        "where both winners fail and results swing by about 15 points between seed pairs, while the v1.4 winner is better on dev (0.64 vs 1.80), on the tuned-family stress row and on detection delay (4.2 s vs 14.0 s).")

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

def freeze(a):
    if os.path.exists(a.out): sys.exit(f"{a.out} already exists: nothing is overwritten. Delete it only if you are certain it was never used for a test run.")
    J = json.load(open(a.cand)); P = json.load(open(PROT))
    if J.get("protocol_version") != "1.4" or not J.get("official_run"): sys.exit("candidates file is not an official protocol v1.4 run")
    if J["protocol_sha256"] != sha(PROT) or (J.get("protocol_md_sha256") and J["protocol_md_sha256"] != sha(PROT_MD)): sys.exit("protocol files changed since the sweep (hash mismatch)")
    F = {"frozen_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "protocol_version": "1.4", "protocol_json_sha256": sha(PROT), "protocol_md_sha256": sha(PROT_MD),
         "candidates_file_sha256": sha(a.cand), "decision_note": NOTE, "candidates": {}, "references": {}}
    for e in ENTRIES + [PUB]:
        c = J["candidates"][e]; F["candidates" if e in ENTRIES else "references"][e] = {"label": c["label"], "params": c["params"], "dev_total": c["dev_total"], "dev_false": c["dev_false"], "dev_missed": c["dev_missed"],
                                                                                          "dev_orig_total": c.get("dev_orig_total"), "dev_rob_total": c.get("dev_rob_total")}
    F["untuned_references"] = {e: P["entries"][e]["reference"] for e in ENTRIES + [PUB]}
    json.dump(F, open(a.out, "w"), indent=2); print("wrote", a.out, "sha256", sha(a.out))
    for e, c in F["candidates"].items(): print(f"  {e:8s} dev {c['dev_total']:.2f}  {json.dumps(c['params'])}")

def per_frame(entry, params, f, fps, warm):
    r = subprocess.run([T.G["EXE"], "--stream", f, "--fps", str(fps)] + T.args_for(entry, params), capture_output=True, text=True)
    if r.returncode: sys.exit(f"run_pc failed on {os.path.basename(f)}: {r.stderr[:300]}")
    d = pd.read_csv(io.StringIO(r.stdout)).iloc[warm:]
    return (d.smooth.values > d.humans.values).astype(float), (d.smooth.values < d.humans.values).astype(float)

def test(a):
    if not os.path.exists(a.frozen): sys.exit("params_frozen.json missing: run 'freeze' first")
    F = json.load(open(a.frozen)); T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), PROT)       # loads protocol + run_pc path
    if F["protocol_json_sha256"] != sha(PROT): sys.exit("protocol json changed since freezing")
    if a.dry_run:
        files = sorted(f for f in glob.glob(os.path.join(ROOT, "data", "streams", "dev_*.csv")) if "dev_rob_" not in f); out = os.path.join(ROOT, "dry_run"); os.makedirs(out, exist_ok=True)
        tag = "DRY RUN ON DEV STREAMS (rehearsal, not a test result)"
    else:
        if os.path.exists(LOCK) or os.path.exists(os.path.join(ROOT, "test_results.md")): sys.exit("test_run.lock / test_results.md exists: the test run has already been done. It is not repeated.")
        files = sorted(glob.glob(os.path.join(ROOT, "data", "streams", "test_*.csv"))); out = ROOT; tag = "HELD-OUT TEST RUN (one shot)"
        if len(files) != 10: sys.exit(f"expected 10 test streams, found {len(files)}")
    names = [os.path.basename(f)[:-4] for f in files]; fps = {f: float(json.load(open(f[:-4] + ".json")).get("fps", 3.8)) for f in files}
    P = T.G["P"]; warm_s = P["scoring"]["warmup_s"]; rng = np.random.default_rng(20261024)
    methods = [(e, "frozen", F["candidates"][e]["params"]) for e in ENTRIES] + [(PUB + " (as published, tuned)", "frozen", F["references"][PUB]["params"])] + \
              [(e + " (untuned reference)", "ref", F["untuned_references"][e]) for e in ENTRIES]
    raw = {}
    for lab, kind, prm in methods:
        e = lab.split(" ")[0]; raw[lab] = [per_frame(e, prm, f, fps[f], math.ceil(warm_s * fps[f])) for f in files]
    # shared block-bootstrap indices (paired across methods)
    B = 2000; blk = {i: max(2, int(20 * fps[f])) for i, f in enumerate(files)}; idx = {}
    for i in range(len(files)):
        n = len(raw[methods[0][0]][i][0]); nb = math.ceil(n / blk[i]); starts = rng.integers(0, max(1, n - blk[i] + 1), size=(B, nb))
        idx[i] = (starts[:, :, None] + np.arange(blk[i])[None, None, :]).reshape(B, -1)[:, :n]
    def stream_tot(lab, i, ix=None):
        fa, mi = raw[lab][i]; return (fa.mean() + mi.mean()) * 100 if ix is None else (fa[ix].mean(1) + mi[ix].mean(1)) * 100
    tot = {lab: np.array([stream_tot(lab, i) for i in range(len(files))]) for lab, _, _ in methods}
    boot = {lab: np.mean([stream_tot(lab, i, idx[i]) for i in range(len(files))], axis=0) for lab, _, _ in methods}
    ci = lambda x: (np.percentile(x, 2.5), np.percentile(x, 97.5))
    L = [f"# {'test_results' if not a.dry_run else 'dry_run'}.md - {tag} ({datetime.datetime.now():%d %b %Y %H:%M})", "",
         f"params_frozen.json sha256 {sha(a.frozen)}; protocol v1.4 json {sha(PROT)[:16]}...; {len(files)} streams; warm-up {warm_s} s; error = false% + missed%; 95 % interval = 20 s moving-block bootstrap ({B}).", "",
         "| Method | Total % [95 % CI] | False % | Missed % | Dev total (26 streams) | Dev original-10 |", "|---|---|---|---|---|---|"]
    for lab, kind, prm in methods:
        e = lab.split(" ")[0]; fa = np.mean([raw[lab][i][0].mean() for i in range(len(files))]) * 100; mi = np.mean([raw[lab][i][1].mean() for i in range(len(files))]) * 100
        src = F["candidates"].get(e) or F["references"].get(e) if kind == "frozen" else None; lo, hi = ci(boot[lab])
        L.append(f"| {lab} | {tot[lab].mean():.2f} [{lo:.2f}, {hi:.2f}] | {fa:.2f} | {mi:.2f} | " + (f"{src['dev_total']:.2f} | {src['dev_orig_total']:.2f} |" if src else "- | - |"))
    variants = ["clean", "laptop_weak", "laptop", "heater_weak", "heater"]
    def vsel(v): return [i for i, n in enumerate(names) if n.endswith("_" + v) and (v != "laptop" or not n.endswith("laptop_weak")) and (v != "heater" or not n.endswith("heater_weak"))]
    L += ["", "Error % by source variant (mean of the empty-room and single-person stream):", "", "| Method | " + " | ".join(variants) + " | empty room | single person |", "|---|" + "---|" * (len(variants) + 2)]
    for lab, _, _ in methods:
        cells = [f"{np.mean([tot[lab][i] for i in vsel(v)]):.1f}" for v in variants]
        ie = [i for i, n in enumerate(names) if "empty" in n]; isg = [i for i, n in enumerate(names) if "single" in n]
        L.append(f"| {lab} | " + " | ".join(cells) + f" | {np.mean(tot[lab][ie]):.1f} | {np.mean(tot[lab][isg]):.1f} |")
    L += ["", "Paired differences, total % (negative = first is better), 95 % block-bootstrap interval:", "", "| Comparison | Difference [95 % CI] |", "|---|---|"]
    for x, y in [("ours_v2", "ours"), ("ours_v2", "bcode"), ("ours_v2", "bpaper"), ("ours", "bpaper"), ("ours", "bcode")]:
        d = boot[x] - boot[y]; lo, hi = ci(d); L.append(f"| {x} - {y} | {tot[x].mean() - tot[y].mean():+.2f} [{lo:+.2f}, {hi:+.2f}] |")
    L += ["", "Error % per stream (total):", "", "| Method | " + " | ".join(n.replace("test_", "").replace("dev_", "") for n in names) + " |", "|---|" + "---|" * len(names)]
    for lab, _, _ in methods: L.append(f"| {lab} | " + " | ".join(f"{t:.1f}" for t in tot[lab]) + " |")
    L += ["", "Reading: test_* starts 20 s after the dev slices end, same session and room, so this is a held-out time window, not a new room or person. Sources are the same steady injected laptops/heaters as dev.",
          "Uncertainty is from temporal blocks of two real slices only; it does not include room-to-room or person-to-person variation."]
    open(os.path.join(out, "test_results.md" if not a.dry_run else "dry_run.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
    pd.DataFrame({lab: tot[lab] for lab, _, _ in methods}, index=names).to_csv(os.path.join(out, "test_results.csv" if not a.dry_run else "dry_run.csv"), float_format="%.3f")
    if not a.dry_run:
        open(LOCK, "w").write(f"test run done {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}; params_frozen sha256 {sha(a.frozen)}\n"); print("\nwrote test_results.md, test_results.csv and test_run.lock (the test run is now used up)")

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest="cmd", required=True)
f = sp.add_parser("freeze"); f.add_argument("--cand", default=os.path.join(ROOT, "tuning_results_v14", "tune_candidates.json")); f.add_argument("--out", default=FROZEN)
t = sp.add_parser("test"); t.add_argument("--frozen", default=FROZEN); t.add_argument("--dry-run", action="store_true")
a = ap.parse_args(); freeze(a) if a.cmd == "freeze" else test(a)
