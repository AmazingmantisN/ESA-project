"""One command for protocol v1.4: build, checks, sweep, v1.3 re-score check, delay report, held-out stress test, then summary_v14.md (short, paste it back).

From the python folder (cmd):
  python run_v14.py --jobs 18             # official run (about 10-15 min on 18 jobs)
  python run_v14.py --quick --jobs 18     # tiny smoke run, NOT the protocol run
  python run_v14.py --skip-tune           # only redo the checks/summary from existing tuning_results_v14

Order: build + test_modes; tune_sweep.py --protocol ../tuning_protocol_v1.4.json; check_v14_rescore.py (v1.3 winners must reproduce their v1.3 dev scores);
latency_check.py (report only); robust_check.py on HELD-OUT seeds 101 and 202 for the v1.4, v1.3 and (if present) v1.2 winners; summary_v14.md.
Needs ..\tuning_results_v13\tune_candidates.json (your v1.3 run). Nothing is frozen and test_* is never opened.
"""
import argparse, datetime, json, os, platform, re, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PC, PY = os.path.join(ROOT, "pc_test"), os.path.join(ROOT, "python"); EXE = ".exe" if os.name == "nt" else ""
PROT = os.path.join(ROOT, "tuning_protocol_v1.4.json"); R = {"v12": os.path.join(ROOT, "tuning_results"), "v13": os.path.join(ROOT, "tuning_results_v13"), "v14": os.path.join(ROOT, "tuning_results_v14")}
CJ = {k: os.path.join(v, "tune_candidates.json") for k, v in R.items()}; LAB = {"v12": "v1.2", "v13": "v1.3", "v14": "v1.4"}
ap = argparse.ArgumentParser(); ap.add_argument("--skip-tune", action="store_true"); ap.add_argument("--quick", action="store_true"); ap.add_argument("--jobs", type=int); a = ap.parse_args()
checks = []; t_all = time.time(); SEEDS = (101, 202)

def run(cmd, cwd):
    t = time.time(); r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    return r.returncode, (r.stdout + "\n" + r.stderr).strip(), time.time() - t

def add(name, ok, secs, note=""):
    checks.append((name, "SKIPPED" if ok is None else ("PASS" if ok else "FAIL"), secs, note.replace("\n", " ")[:200])); print(f"[{checks[-1][1]:7s}] {name} ({secs:.0f} s) {note[:140]}", flush=True)

def tail(txt, n=3): return " | ".join(txt.splitlines()[-n:])

def table(path):
    rows = open(path, encoding="utf-8").read().splitlines(); i = next(k for k, l in enumerate(rows) if l.startswith("| Variant"))
    names = [c.strip() for c in rows[i].strip("|").split("|")][1:]; out = {}
    for l in rows[i + 2:]:
        if not l.startswith("|"): break
        c = [x.strip().strip("*") for x in l.strip("|").split("|")]; out[c[0]] = dict(zip(names, map(float, c[1:])))
    return out

rc1, o1, s1 = run(["g++", "-O2", "-std=c++17", "-o", f"run_pc{EXE}", "run_pc.cpp"], PC)
rc2, o2, s2 = run(["g++", "-O2", "-std=c++17", "-o", f"test_modes{EXE}", "test_modes.cpp"], PC)
add("build run_pc + test_modes (g++)", rc1 == 0 and rc2 == 0, s1 + s2, "" if rc1 == rc2 == 0 else tail(o1 + o2))
ok = rc1 == 0 and rc2 == 0
if ok:
    rc, o, s = run([os.path.join(PC, f"test_modes{EXE}")], PC); m = re.findall(r"(\d+) tests, (\d+) failed", o)
    add("test_modes (expect 35 tests, 0 failed)", bool(m) and m[-1][1] == "0", s, (m[-1][0] + " tests, " + m[-1][1] + " failed") if m else tail(o))
    if not os.path.exists(CJ["v13"]): add("v1.3 candidates present", False, 0, "missing tuning_results_v13\\tune_candidates.json; run run_v13.py first"); ok = False
if ok:
    if not a.skip_tune:
        cmd = [sys.executable, "tune_sweep.py", "--protocol", PROT] + (["--quick"] if a.quick else []) + (["--jobs", str(a.jobs)] if a.jobs else [])
        rc, o, s = run(cmd, PY); add("tune_sweep protocol v1.4 (dev only)" + (" QUICK TEST" if a.quick else ""), rc == 0, s, tail(o, 2) if rc else ""); ok = rc == 0
    else: add("tune_sweep", None, 0, "skipped")
if ok:
    rc, o, s = run([sys.executable, "check_v14_rescore.py"], PY); add("check_v14_rescore (v1.3 winners reproduce their v1.3 dev scores)", rc == 0, s, tail(o, 1))
    have = [k for k in ("v12", "v13", "v14") if os.path.exists(CJ[k])]
    rc, o, s = run([sys.executable, "latency_check.py"] + [f"{LAB[k]}={CJ[k]}" for k in have] + ["--md", os.path.join(ROOT, "latency_report.md")], PY); add("latency_check (report only)", rc == 0, s, tail(o, 1) if rc else "")
    for k in ("v14", "v13", "v12"):
        if k not in have: continue
        for sd in SEEDS:
            rc, o, s = run([sys.executable, "robust_check.py", "--cand", CJ[k], "--seed", str(sd), "--md", os.path.join(ROOT, f"robust_summary_{k}_s{sd}.md")], PY)
            add(f"robust_check held-out seed {sd}, {LAB[k]} winners", rc == 0, s, tail(o, 1) if rc else "")

L = [f"# summary_v14.md ({datetime.datetime.now():%d %b %Y %H:%M})", "", f"Python {platform.python_version()}, {os.cpu_count()} cores, {platform.system()}. Total {time.time() - t_all:.0f} s.", ""]
J = json.load(open(CJ["v14"])) if os.path.exists(CJ["v14"]) else None; Jp = {k: json.load(open(CJ[k]))["candidates"] for k in ("v12", "v13") if os.path.exists(CJ[k])}
if J: L += [f"Protocol v{J['protocol_version']} json sha256 {J['protocol_sha256']}", f"md sha256 {J.get('protocol_md_sha256')}", f"official_run={J['official_run']} jobs={J.get('jobs')} dev streams={len(J['dev_streams'])}", ""]
L += ["## Checks", "", "| Check | Result | Seconds | Note |", "|---|---|---|---|"] + [f"| {n} | {r} | {s:.0f} | {note} |" for n, r, s, note in checks]
if J:
    L += ["", "## v1.4 dev winners (NOT frozen). Error = false% + missed%, lower is better", "",
          "| Entry | Total % (26) | False | Missed | Worst stream | Original 10 | Robustness 16 | v1.3 winner: total / original 10 | Stage-1 best | Edge params |", "|---|---|---|---|---|---|---|---|---|---|"]
    for e, c in J["candidates"].items():
        p = Jp.get("v13", {}).get(e); pv = f"{p['dev_total']:.2f} / {p.get('dev_orig_total', float('nan')):.2f}" if p else "n/a"
        L.append(f"| {e} | {c['dev_total']:.2f} | {c['dev_false']:.2f} | {c['dev_missed']:.2f} | {c['dev_worst_stream']:.1f} | {c.get('dev_orig_total', float('nan')):.2f} | {c.get('dev_rob_total', float('nan')):.2f} | {pv} | {c['stage1_best_total']:.2f} | {', '.join(c['edge_params']) or 'none'} |")
    vv = next(iter(J["candidates"].values())).get("dev_rob_by_variant", {})
    L += ["", "Robustness-16 error by variant (v1.4 winner, dev):", "", "| Entry | " + " | ".join(vv) + " |", "|---|" + "---|" * len(vv)]
    for e, c in J["candidates"].items(): L.append(f"| {e} | " + " | ".join("%.1f" % v for v in c.get("dev_rob_by_variant", {}).values()) + " |")
    L += [""] + [f"- {e}: `{json.dumps(c['params'])}`; top-10 range {c['top10_total_range'][0]:.2f}-{c['top10_total_range'][1]:.2f}" for e, c in J["candidates"].items()]
    tags = [k for k in ("v12", "v13", "v14") if all(os.path.exists(os.path.join(ROOT, f"robust_summary_{k}_s{sd}.md")) for sd in SEEDS)]
    if "v14" in tags:
        T = {(k, sd): table(os.path.join(ROOT, f"robust_summary_{k}_s{sd}.md")) for k in tags for sd in SEEDS}
        meth = [("Ours-v1 winner", "v1"), ("Ours-v2 winner", "v2"), ("B-code winner", "B-code"), ("B-paper winner", "B-paper")]
        L += ["", f"## Held-out synthetic stress test (seeds {SEEDS[0]} and {SEEDS[1]}, never used in tuning; mean of both seeds; false%+missed%)", "",
              "| Variant | " + " | ".join(f"{lab} {LAB[k]}" for _, lab in meth for k in tags) + " |", "|---|" + "---|" * (len(meth) * len(tags))]
        rows = [r for r in T[("v14", SEEDS[0])] if r not in ("all variants", "all except walker")] + ["all variants", "all except walker"]
        fam = ["steady", "jitter_s", "drift", "switch"]; rows = rows + ["tuned-family mean (steady, jitter_s, drift, switch)"]
        for r in rows:
            if r.startswith("tuned-family"): L.append(f"| {r} | " + " | ".join("%.1f" % (sum(T[(k, sd)][f][m] for sd in SEEDS for f in fam) / (len(SEEDS) * len(fam))) for m, _ in meth for k in tags) + " |"); continue
            L.append(f"| {r} | " + " | ".join("%.1f" % (sum(T[(k, sd)][r][m] for sd in SEEDS) / len(SEEDS)) for m, _ in meth for k in tags) + " |")
        L += ["", "'all except walker' per seed: " + "; ".join(f"{LAB[k]} seed {sd}: " + ", ".join(f"{lab} {T[(k, sd)]['all except walker'][m]:.1f}" for m, lab in meth) for k in tags for sd in SEEDS)]
    lp = os.path.join(ROOT, "latency_report.md")
    if os.path.exists(lp): L += ["", "## Detection delay (splice test, report only)", ""] + [l for l in open(lp, encoding="utf-8").read().splitlines()[2:] if l.strip()]
L += ["", "Any FAIL above: paste its Note and the step name. jitter_m and walker are reported only. Nothing here is frozen or tested on test_* streams."]
open(os.path.join(ROOT, "summary_v14.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", os.path.join(ROOT, "summary_v14.md"))
