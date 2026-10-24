"""Equal-budget two-stage tuning on DEV streams only (reads the protocol json, default ../tuning_protocol.json = v1.2; writes ../tuning_results/ or the json's results_dir).

  python tune_sweep.py                      # official run, all enabled entries, --jobs = cores-2
  python tune_sweep.py --jobs 18            # explicit parallelism (results do not depend on it)
  python tune_sweep.py --quick              # tiny smoke run (NOT the protocol run)
  python tune_sweep.py --protocol ../tuning_protocol_v1.3.json --jobs 18     # protocol v1.3 (writes ../tuning_results_v13/)

Refuses any stream whose name contains test_ or expl_. Freezes nothing: writes tune_candidates.json.
"""
import argparse, glob, hashlib, io, json, math, os, random, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
PROT_PATH = os.path.join(ROOT, "tuning_protocol.json"); MD_PATH = os.path.join(ROOT, "tuning_protocol.md")
G = {}   # per-process globals, filled by setup()

def setup(glob_pat, prot_path=None):
    G["P"] = P = json.load(open(prot_path or PROT_PATH))
    G["EXE"] = next((p for p in (os.path.join(ROOT, "pc_test", n) for n in ("run_pc.exe", "run_pc")) if os.path.exists(p)), None)
    if G["EXE"] is None: sys.exit("build pc_test/run_pc first")
    files = sorted(glob.glob(glob_pat))
    bad = [f for f in files if any(t in os.path.basename(f) for t in P["forbidden_in_tuning"])]
    if bad: sys.exit("refusing to tune on: " + ", ".join(map(os.path.basename, bad)))
    if not files: sys.exit("no streams match " + glob_pat)
    if not P.get("stream_manifest"): files = [f for f in files if not os.path.basename(f).startswith("dev_rob_")]   # v1.0-v1.2 protocols never saw the v1.3 robustness streams
    G["files"] = files
    G["FPS"] = {f: float(json.load(open(f[:-4] + ".json")).get("fps", 3.8)) if os.path.exists(f[:-4] + ".json") else 3.8 for f in files}

def args_for(entry, c):
    P = G["P"]; cli = P["entries"][entry]["cli"]
    sm = ["--smooth_s", str(c["smooth_s"])] if c.get("smooth_s") is not None else []
    mm = ["--maxmissed_s", str(c["maxmissed_s"])] if c.get("maxmissed_s") is not None else []
    if cli == "ours_v2":
        return (["--pers_mode", "3", "--window_s", str(c["window_s"]), "--drift", str(c["drift"]), "--contrast", str(c["contrast"]), "--k", str(c["k"]),
                 "--persist_s", str(c["persist_s"]), "--hyst_s", str(c["hyst_s"]), "--cand_policy", str(c["cand_policy"]), "--assign_mode", str(c["assign_mode"])] + sm + mm)
    if cli == "ours_v3":      # Ours-v2 + liveness (protocol v2.0): cand_policy bit 8 and the two liveness parameters
        return (["--pers_mode", "3", "--window_s", str(c["window_s"]), "--drift", str(c["drift"]), "--contrast", str(c["contrast"]), "--k", str(c["k"]),
                 "--persist_s", str(c["persist_s"]), "--hyst_s", str(c["hyst_s"]), "--cand_policy", str(int(c["cand_policy"])), "--assign_mode", str(int(c["assign_mode"])),
                 "--live_s", str(c["live_s"]), "--live_thresh", str(c["live_thresh"])] + sm + mm)
    if cli == "ours":
        return ["--window_s", str(c["window_s"]), "--drift", str(c["drift"]), "--contrast", str(c["contrast"]), "--k", str(c["k"])] + sm + mm
    if cli == "bpaper":
        return ["--preset", "bpaper", "--timebase", c["timebase"], "--drift", str(c["drift"]), "--dht_offset", str(c["dht_offset"])] + sm + mm
    return ["--preset", cli, "--npersist", str(c["npersist"]), "--drift", str(c["drift"]), "--dht_offset", str(c["dht_offset"])] + sm + mm

def score(task):
    entry, c = task; P = G["P"]; out = []
    for f in G["files"]:
        fps = G["FPS"][f]
        r = subprocess.run([G["EXE"], "--stream", f, "--fps", str(fps)] + args_for(entry, c), capture_output=True, text=True)
        if r.returncode: raise RuntimeError(f"run_pc failed on {os.path.basename(f)}: {r.stderr[:300]}")
        d = pd.read_csv(io.StringIO(r.stdout)).iloc[math.ceil(P["scoring"]["warmup_s"] * fps):]
        out.append(((d.smooth > d.humans).mean() * 100, (d.smooth < d.humans).mean() * 100))
    return out

def choices(s): return G["P"]["shared_choices"][s["from"]] if "from" in s else s["values"]

def sample(entry, rng):
    c = {}
    for k, s in G["P"]["entries"][entry]["space"].items():
        if s["type"] == "loguniform": c[k] = round(math.exp(rng.uniform(math.log(s["lo"]), math.log(s["hi"]))), 4)
        elif s["type"] == "uniform": c[k] = round(rng.uniform(s["lo"], s["hi"]), 4)
        else: c[k] = rng.choice(choices(s))
    return c

def perturb(entry, c, rng):
    st = G["P"]["stage2"]; n = {}
    for k, s in G["P"]["entries"][entry]["space"].items():
        if s["type"] == "loguniform": n[k] = round(min(s["hi"], max(s["lo"], c[k] * math.exp(rng.gauss(0, st["continuous_log_sigma"])))), 4)
        elif s["type"] == "uniform": n[k] = round(min(s["hi"], max(s["lo"], c[k] + rng.gauss(0, st["continuous_lin_sigma_frac"] * (s["hi"] - s["lo"])))), 4)
        else: n[k] = rng.choice(choices(s)) if rng.random() < st["discrete_resample_prob"] else c[k]
    return n

def edge_flags(entry, c):
    fl = []; fr = G["P"]["scoring"]["edge_rule_fraction"]
    for k, s in G["P"]["entries"][entry]["space"].items():
        if s["type"] in ("loguniform", "uniform"):
            lo, hi, v = (math.log(s["lo"]), math.log(s["hi"]), math.log(c[k])) if s["type"] == "loguniform" else (s["lo"], s["hi"], c[k])
            nat = s.get("natural_bounds", []); op = s.get("operational_bounds", [])      # operational bound (v1.4): declared limit, e.g. detection delay
            if (v - lo) / (hi - lo) < fr: fl.append(k + (" (natural bound, no widening)" if "lo" in nat else " (operational limit, no widening)" if "lo" in op else ""))
            elif (hi - v) / (hi - lo) < fr: fl.append(k + (" (natural bound, no widening)" if "hi" in nat else " (operational limit, no widening)" if "hi" in op else ""))
    return fl

def check_manifest(P):
    """v1.3: the robustness dev streams are shipped as files; refuse to run if they differ from the hashes recorded with the protocol."""
    mp = P.get("stream_manifest")
    if not mp: return
    mp = os.path.join(ROOT, mp); M = json.load(open(mp)); bad = []
    for name, h in M["files"].items():
        p = os.path.join(ROOT, "data", "streams", name)
        if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != h: bad.append(name)
    extra = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "data", "streams", "dev_rob_*.csv")) if os.path.basename(f) not in M["files"])
    if bad or extra: sys.exit(f"robustness dev streams differ from {os.path.basename(mp)}: changed/missing {bad[:4]}, unexpected {extra[:4]}. Use the shipped files (do not regenerate).")
    print(f"robustness dev streams verified against {os.path.basename(mp)} ({len(M['files'])} files, seed {M['seed']})")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entries", nargs="+"); ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--glob", default=os.path.join(ROOT, "data", "streams", "dev_*.csv"))
    ap.add_argument("--protocol", default=PROT_PATH); ap.add_argument("--out"); a = ap.parse_args()
    prot = os.path.abspath(a.protocol); md_path = prot[:-5] + ".md" if prot.endswith(".json") else MD_PATH
    setup(a.glob, prot); P = G["P"]
    a.out = a.out or os.path.join(ROOT, P.get("results_dir", "tuning_results"))
    check_manifest(P)
    sha = hashlib.sha256(open(prot, "rb").read()).hexdigest(); md_sha = hashlib.sha256(open(md_path, "rb").read()).hexdigest() if os.path.exists(md_path) else None
    n1 = 12 if a.quick else P["budget_trials_per_entry"]; top_k = 2 if a.quick else P["stage2"]["top_k"]; per = 3 if a.quick else P["stage2"]["perturbations_per_seed"]
    entries = [e for e in (a.entries or P["entries"]) if P["entries"][e].get("enabled", True)]
    names = [os.path.basename(f)[:-4] for f in G["files"]]; os.makedirs(a.out, exist_ok=True); cand = {}; t0 = time.time()
    print(f"protocol v{P['protocol_version']} sha256 {sha[:16]}...  {n1}+{top_k}x{per} trials/entry ({'QUICK TEST, not the protocol run' if a.quick else 'OFFICIAL'})  streams {len(names)}  jobs {a.jobs}")
    with ProcessPoolExecutor(a.jobs, initializer=setup, initargs=(a.glob, prot)) as pool:
        for entry in entries:
            rng = random.Random(P["rng_seed"]); ref = P["entries"][entry]["reference"]
            ref_s = score((entry, ref)); rt = float(np.mean([x + y for x, y in ref_s]))
            cfgs = [sample(entry, rng) for _ in range(n1)]
            res = list(pool.map(score, [(entry, c) for c in cfgs], chunksize=2))
            rows = [dict(trial=i, stage=1, **c, res=r) for i, (c, r) in enumerate(zip(cfgs, res))]
            top = sorted(rows, key=lambda r: (np.mean([x + y for x, y in r["res"]]), r["trial"]))[:top_k]
            rng2 = random.Random(P["rng_seed"] + P["stage2"]["rng_seed_offset"])
            cfg2 = [perturb(entry, {k: t[k] for k in P["entries"][entry]["space"]}, rng2) for t in top for _ in range(per)]
            res2 = list(pool.map(score, [(entry, c) for c in cfg2], chunksize=2))
            rows += [dict(trial=n1 + i, stage=2, **c, res=r) for i, (c, r) in enumerate(zip(cfg2, res2))]
            for r in rows:
                s = r.pop("res"); r["false"] = np.mean([x[0] for x in s]); r["missed"] = np.mean([x[1] for x in s]); tot = [x + y for x, y in s]
                r["total"] = np.mean(tot); r["worst"] = max(tot); r.update({f"tot_{n}": t for n, t in zip(names, tot)})
                orig = [t for n, t in zip(names, tot) if not n.startswith("dev_rob_")]; rob = [t for n, t in zip(names, tot) if n.startswith("dev_rob_")]
                if orig and rob: r["total_orig"] = np.mean(orig); r["total_rob"] = np.mean(rob)
            df = pd.DataFrame(rows); df.to_csv(os.path.join(a.out, f"trials_{entry}.csv"), index=False, float_format="%.4f")
            pool_ = df[df.total <= df.total.min() + 0.10]; b = pool_.sort_values(["worst", "trial"]).iloc[0]
            bc = {k: (b[k].item() if hasattr(b[k], "item") else b[k]) for k in P["entries"][entry]["space"]}; t10 = df.sort_values("total").head(10)
            s1best = df[df.stage == 1].total.min()
            cand[entry] = {"label": P["entries"][entry]["label"], "params": bc, "dev_false": b["false"], "dev_missed": b["missed"], "dev_total": b["total"], "dev_worst_stream": b["worst"],
                           "winner_stage": int(b["stage"]), "stage1_best_total": s1best, "reference_total": rt, "edge_params": edge_flags(entry, bc),
                           "top10_total_range": [t10.total.min(), t10.total.max()], "trials": len(df)}
            if "total_rob" in df:
                cand[entry]["dev_orig_total"] = b["total_orig"]; cand[entry]["dev_rob_total"] = b["total_rob"]
                cand[entry]["dev_rob_by_variant"] = {v: float(np.mean([b[f"tot_{n}"] for n in names if f"_{v}_" in n and n.startswith("dev_rob_")])) for v in P.get("robust_dev", {}).get("variants", [])}
                so = [x for x, n in zip(ref_s, names) if not n.startswith("dev_rob_")]; cand[entry]["reference_orig_total"] = float(np.mean([x + y for x, y in so]))
            print(f"== {cand[entry]['label']} ({time.time() - t0:.0f} s): best total {b['total']:.2f}% (false {b['false']:.2f}, missed {b['missed']:.2f}, worst stream {b['worst']:.1f}); "
                  f"stage-1 best {s1best:.2f}; untuned reference {rt:.2f}; edge {cand[entry]['edge_params'] or 'none'}")
    json.dump({"protocol_version": P["protocol_version"], "protocol_sha256": sha, "protocol_md_sha256": md_sha, "official_run": not a.quick, "dev_streams": names,
               "jobs": a.jobs, "candidates": cand, "NOT_FROZEN": True}, open(os.path.join(a.out, "tune_candidates.json"), "w"), indent=2, default=float)
    print("wrote", os.path.join(a.out, "tune_candidates.json"), "(candidates only; nothing is frozen)")

if __name__ == "__main__":
    main()
