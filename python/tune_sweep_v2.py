"""Protocol v2.0 tuning sweep: equal-budget two-stage tuning on DEV streams only, with three weighted dev pools.

Pools (tuning_protocol_v2.0.json, "dev_pools"): real_orig (10 real-slice streams), real_rob (16 robustness streams), synth_dev (80 synthetic Stage-1.1 streams, 16 scenarios,
scenarios weighted equally). Each pool has weight 1/3 in the dev total. Everything else (sampler, two stages, tie-break, edge rule) is tune_sweep.py unchanged.

  python tune_sweep_v2.py --jobs 18                          # official run, all entries (about 45-70 min on 18 jobs)
  python tune_sweep_v2.py --jobs 18 --entries ours ours_v3   # a subset (results of the other entries are not touched; run the rest later)
  python tune_sweep_v2.py --quick --jobs 18                  # tiny smoke run, NOT the protocol run
Writes ../tuning_results_v20/tune_candidates.json (candidates only; nothing is frozen) and trials_<entry>.csv. test_*, expl_*, syn_test*, quiet* are refused.
"""
import argparse, glob, hashlib, json, math, os, random, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T

def setup2(prot_path):
    P = json.load(open(prot_path)); T.G["P"] = P
    T.G["EXE"] = next((p for p in (os.path.join(ROOT, "pc_test", n) for n in ("run_pc.exe", "run_pc")) if os.path.exists(p)), None)
    if T.G["EXE"] is None: sys.exit("build pc_test/run_pc first")
    files, wts, pools = [], [], []
    for pool in P["dev_pools"]:
        fs = sorted(glob.glob(os.path.join(ROOT, pool["glob"])))
        if pool.get("exclude_prefix"): fs = [f for f in fs if not os.path.basename(f).startswith(pool["exclude_prefix"])]
        bad = [f for f in fs if any(t in os.path.basename(f) for t in P["forbidden_in_tuning"])]
        if bad: sys.exit("refusing to tune on: " + ", ".join(map(os.path.basename, bad)))
        if not fs: sys.exit(f"pool {pool['name']}: no streams match {pool['glob']}")
        if pool.get("group_by") == "scenario":
            idx = pd.read_csv(os.path.join(ROOT, pool["index"])); sc = dict(zip(idx.stream, idx.scenario))
            grp = [sc[os.path.basename(f)[:-4]] for f in fs]; cnt = {g: grp.count(g) for g in set(grp)}
            w = [pool["weight"] / (len(cnt) * cnt[g]) for g in grp]; T.G.setdefault("SCEN", {}).update({f: g for f, g in zip(fs, grp)})
        else: w = [pool["weight"] / len(fs)] * len(fs)
        files += fs; wts += w; pools += [pool["name"]] * len(fs)
    T.G["files"] = files; T.G["W"] = np.array(wts); T.G["POOL"] = pools
    T.G["FPS"] = {f: float(json.load(open(f[:-4] + ".json")).get("fps", 3.8)) for f in files}

def verify_synth(P):
    for pool in P["dev_pools"]:
        if not pool.get("manifest"): continue
        M = json.load(open(os.path.join(ROOT, pool["manifest"]))); bad = []
        for name, h in M["files"].items():
            p = os.path.join(ROOT, os.path.dirname(pool["glob"]), name)
            if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != h: bad.append(name)
        extra = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, pool["glob"])) if os.path.basename(f) not in M["files"])
        if bad or extra: sys.exit(f"synthetic dev streams differ from {pool['manifest']}: changed/missing {bad[:4]}, unexpected {extra[:4]}")
        print(f"synthetic dev streams verified against {pool['manifest']} ({M['n_streams']} streams; {M['source']})")

def aggregate(s):
    """s = list of (false, missed) per stream in G['files'] order -> dict of weighted totals."""
    W = T.G["W"]; fa = np.array([x[0] for x in s]); mi = np.array([x[1] for x in s]); tot = fa + mi
    out = {"false": float((W * fa).sum()), "missed": float((W * mi).sum()), "total": float((W * tot).sum()), "worst": float(tot.max())}
    pools = np.array(T.G["POOL"])
    for name in dict.fromkeys(T.G["POOL"]):
        m = pools == name; out["pool_" + name] = float((W[m] * tot[m]).sum() / W[m].sum())
    return out, tot

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entries", nargs="+"); ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--protocol", default=os.path.join(ROOT, "tuning_protocol_v2.0.json")); ap.add_argument("--out"); a = ap.parse_args()
    prot = os.path.abspath(a.protocol); md_path = prot[:-5] + ".md"
    setup2(prot); P = T.G["P"]; a.out = a.out or os.path.join(ROOT, P["results_dir"]); T.check_manifest(P); verify_synth(P)
    sha = hashlib.sha256(open(prot, "rb").read()).hexdigest(); md_sha = hashlib.sha256(open(md_path, "rb").read()).hexdigest() if os.path.exists(md_path) else None
    n1 = 12 if a.quick else P["budget_trials_per_entry"]; top_k = 2 if a.quick else P["stage2"]["top_k"]; per = 3 if a.quick else P["stage2"]["perturbations_per_seed"]
    entries = [e for e in (a.entries or P["entries"]) if P["entries"][e].get("enabled", True)]
    names = [os.path.basename(f)[:-4] for f in T.G["files"]]; os.makedirs(a.out, exist_ok=True); t0 = time.time()
    cpath = os.path.join(a.out, "tune_candidates.json"); prev = json.load(open(cpath)) if os.path.exists(cpath) and a.entries and not a.quick else None
    cand = dict(prev["candidates"]) if prev else {}
    print(f"protocol v{P['protocol_version']} sha256 {sha[:16]}...  {n1}+{top_k}x{per} trials/entry ({'QUICK TEST, not the protocol run' if a.quick else 'OFFICIAL'})  streams {len(names)}  jobs {a.jobs}", flush=True)
    with ProcessPoolExecutor(a.jobs, initializer=setup2, initargs=(prot,)) as pool:
        for entry in entries:
            rng = random.Random(P["rng_seed"]); ref = P["entries"][entry]["reference"]
            rt = aggregate(T.score((entry, ref)))[0]["total"]
            cfgs = [T.sample(entry, rng) for _ in range(n1)]
            res = list(pool.map(T.score, [(entry, c) for c in cfgs], chunksize=2))
            rows = [dict(trial=i, stage=1, **c, res=r) for i, (c, r) in enumerate(zip(cfgs, res))]
            for r in rows: r["_tot"] = aggregate(r["res"])[0]["total"]
            top = sorted(rows, key=lambda r: (r["_tot"], r["trial"]))[:top_k]
            rng2 = random.Random(P["rng_seed"] + P["stage2"]["rng_seed_offset"])
            cfg2 = [T.perturb(entry, {k: t[k] for k in P["entries"][entry]["space"]}, rng2) for t in top for _ in range(per)]
            res2 = list(pool.map(T.score, [(entry, c) for c in cfg2], chunksize=2))
            rows += [dict(trial=n1 + i, stage=2, **c, res=r) for i, (c, r) in enumerate(zip(cfg2, res2))]
            for r in rows:
                r.pop("_tot", None); s = r.pop("res"); ag, tot = aggregate(s)
                r.update({k: v for k, v in ag.items()}); r.update({f"tot_{n}": t for n, t in zip(names, tot)}); r["_tot"] = tot
            df = pd.DataFrame([{k: v for k, v in r.items() if k != "_tot"} for r in rows]); df.to_csv(os.path.join(a.out, f"trials_{entry}.csv"), index=False, float_format="%.4f")
            pool_ = df[df.total <= df.total.min() + 0.10]; b = pool_.sort_values(["worst", "trial"]).iloc[0]; bt = rows[int(b["trial"])]["_tot"]
            bc = {k: (b[k].item() if hasattr(b[k], "item") else b[k]) for k in P["entries"][entry]["space"]}; t10 = df.sort_values("total").head(10)
            scen = {}
            for f, t in zip(T.G["files"], bt):
                if f in T.G.get("SCEN", {}): scen.setdefault(T.G["SCEN"][f], []).append(float(t))
            cand[entry] = {"label": P["entries"][entry]["label"], "params": bc, "dev_false": b["false"], "dev_missed": b["missed"], "dev_total": b["total"], "dev_worst_stream": b["worst"],
                           "dev_real_orig": b["pool_real_orig"], "dev_real_rob": b["pool_real_rob"], "dev_synth": b["pool_synth_dev"], "dev_orig_total": b["pool_real_orig"], "dev_rob_total": b["pool_real_rob"],
                           "dev_synth_by_scenario": {k: float(np.mean(v)) for k, v in sorted(scen.items())}, "winner_stage": int(b["stage"]),
                           "stage1_best_total": df[df.stage == 1].total.min(), "reference_total": rt, "edge_params": T.edge_flags(entry, bc),
                           "top10_total_range": [t10.total.min(), t10.total.max()], "trials": len(df)}
            print(f"== {cand[entry]['label'][:60]} ({time.time() - t0:.0f} s): total {b['total']:.2f}% (real-orig {b['pool_real_orig']:.2f}, real-rob {b['pool_real_rob']:.2f}, synth {b['pool_synth_dev']:.2f}; "
                  f"false {b['false']:.2f}, missed {b['missed']:.2f}); stage-1 best {cand[entry]['stage1_best_total']:.2f}; untuned reference {rt:.2f}; edge {cand[entry]['edge_params'] or 'none'}", flush=True)
            json.dump({"protocol_version": P["protocol_version"], "protocol_sha256": sha, "protocol_md_sha256": md_sha, "official_run": not a.quick, "dev_streams": names, "jobs": a.jobs,
                       "candidates": cand, "NOT_FROZEN": True}, open(cpath, "w"), indent=2, default=float)
    print("wrote", cpath, "(candidates only; nothing is frozen)")

if __name__ == "__main__":
    main()
