"""One command for protocol v2.0 (Ours-v3 + synthetic dev data): build, checks, sweep, delay report, held-out stress, then summary_v20.md (short, paste it back).

From the python folder (cmd):
  python run_v20.py --jobs 18             # official run (about 45-70 min on 18 jobs)
  python run_v20.py --quick --jobs 18     # tiny smoke run, NOT the protocol run (about 5 min)
  python run_v20.py --skip-tune           # only redo the checks/summary from existing tuning_results_v20

Order: build run_pc + test_modes (expect 38 tests); regression checks (v2 == v1 when nested, v1 reference unchanged); tune_sweep_v2.py (protocol v2.0);
check_v20_rescore.py (the v1.4 winners must reproduce their real dev scores); latency_check.py (report only); robust_check.py on FRESH seeds 303 and 404 for the
v2.0 winners AND the v1.4 frozen winners; summary_v20.md. Nothing is frozen, test_* is never opened, the fresh synthetic test is not generated here.
"""
import argparse, datetime, json, os, platform, re, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PC, PY = os.path.join(ROOT, "pc_test"), os.path.join(ROOT, "python"); EXE = ".exe" if os.name == "nt" else ""
PROT = os.path.join(ROOT, "tuning_protocol_v2.0.json"); RES = os.path.join(ROOT, "tuning_results_v20"); C20 = os.path.join(RES, "tune_candidates.json"); C14 = os.path.join(ROOT, "tuning_results_v14", "tune_candidates.json")
ap = argparse.ArgumentParser(); ap.add_argument("--skip-tune", action="store_true"); ap.add_argument("--quick", action="store_true"); ap.add_argument("--jobs", type=int); a = ap.parse_args()
checks = []; t_all = time.time(); SEEDS = (303, 404); os.makedirs(RES, exist_ok=True)
if a.quick: RES_OUT = os.path.join(ROOT, "tuning_results_v20_quick"); C20 = os.path.join(RES_OUT, "tune_candidates.json"); os.makedirs(RES_OUT, exist_ok=True)

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
    add("test_modes (expect 38 tests, 0 failed)", bool(m) and m[-1] == ("38", "0"), s, (m[-1][0] + " tests, " + m[-1][1] + " failed") if m else tail(o))
    rc, o, s = run([sys.executable, "check_v1_equiv.py", os.path.join("..", "data", "streams", "dev_*.csv"), "--n", "20"], PC); add("check_v1_equiv (v2 code with v1 flags == v1 reference)", rc == 0, s, tail(o, 1))
    rc, o, s = run([sys.executable, "check_v2_nested.py", "--n", "20"], PC); add("check_v2_nested (v2 nested == v1; liveness off changes nothing)", rc == 0, s, tail(o, 1))
    if not os.path.exists(C14): add("v1.4 candidates present", False, 0, "missing tuning_results_v14\\tune_candidates.json"); ok = False
if ok:
    if not a.skip_tune:
        cmd = [sys.executable, "tune_sweep_v2.py", "--protocol", PROT] + (["--quick", "--out", os.path.dirname(C20)] if a.quick else []) + (["--jobs", str(a.jobs)] if a.jobs else [])
        rc, o, s = run(cmd, PY); add("tune_sweep_v2 protocol v2.0 (dev only)" + (" QUICK TEST" if a.quick else ""), rc == 0, s, tail(o, 2) if rc else ""); ok = rc == 0
    else: add("tune_sweep_v2", None, 0, "skipped")
if ok:
    rc, o, s = run([sys.executable, "check_v20_rescore.py"], PY); add("check_v20_rescore (v1.4 winners reproduce their real dev scores)", rc == 0, s, tail(o, 1))
    rc, o, s = run([sys.executable, "latency_check.py", f"v2.0={C20}", f"v1.4={C14}", "--protocol", PROT, "--md", os.path.join(ROOT, "latency_report_v20.md")], PY); add("latency_check (report only)", rc == 0, s, tail(o, 1) if rc else "")
    for tag, cj in (("v20", C20), ("v14", C14)):
        for sd in SEEDS:
            rc, o, s = run([sys.executable, "robust_check.py", "--cand", cj, "--seed", str(sd), "--protocol", PROT, "--md", os.path.join(ROOT, f"robust_summary_{tag}_s{sd}.md")], PY)
            add(f"robust_check FRESH seed {sd}, {tag} winners", rc == 0, s, tail(o, 1) if rc else "")

L = [f"# summary_v20.md ({datetime.datetime.now():%d %b %Y %H:%M})", "", f"Python {platform.python_version()}, {os.cpu_count()} cores, {platform.system()}. Total {time.time() - t_all:.0f} s.", ""]
J = json.load(open(C20)) if os.path.exists(C20) else None
if J: L += [f"Protocol v{J['protocol_version']} json sha256 {J['protocol_sha256']}", f"md sha256 {J.get('protocol_md_sha256')}", f"official_run={J['official_run']} jobs={J.get('jobs')} dev streams={len(J['dev_streams'])}", ""]
L += ["## Checks", "", "| Check | Result | Seconds | Note |", "|---|---|---|---|"] + [f"| {n} | {r} | {s:.0f} | {note} |" for n, r, s, note in checks]
if J:
    C = J["candidates"]
    L += ["", "## v2.0 dev winners (NOT frozen; in-sample). Error = false% + missed%, lower is better", "",
          "| Entry | Dev total | Real orig-10 | Real rob-16 | Synth dev-80 | False | Missed | Worst stream | Untuned ref | Stage-1 best | Edge params |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e, c in C.items():
        L.append(f"| {e} | {c['dev_total']:.2f} | {c['dev_real_orig']:.2f} | {c['dev_real_rob']:.2f} | {c['dev_synth']:.2f} | {c['dev_false']:.2f} | {c['dev_missed']:.2f} | {c['dev_worst_stream']:.1f} | {c['reference_total']:.2f} | {c['stage1_best_total']:.2f} | {', '.join(c['edge_params']) or 'none'} |")
    pj = os.path.join(RES, "v14_winners_on_v20_dev.json"); P14 = json.load(open(pj)) if os.path.exists(pj) else {}
    if P14:
        L += ["", "Same dev pools, the v1.4 frozen winners (for comparison; they were tuned only on the 26 real streams):", "", "| Entry | Dev total (equal pool weights) | Real orig-10 | Real rob-16 | Synth dev-80 |", "|---|---|---|---|---|"]
        for e, c in P14.items(): L.append(f"| {e} (v1.4) | {c['total']:.2f} | {c['pool_real_orig']:.2f} | {c['pool_real_rob']:.2f} | {c['pool_synth_dev']:.2f} |")
    scs = sorted({s for c in C.values() for s in c["dev_synth_by_scenario"]}); cols = [(f"{e}", C[e]["dev_synth_by_scenario"]) for e in C] + [(f"{e} v1.4", P14[e]["by_scenario"]) for e in ("ours", "ours_v2") if e in P14]
    L += ["", "Synthetic dev error by scenario (winner of each entry; mean over 5 seeds; in-sample):", "", "| Scenario | " + " | ".join(n for n, _ in cols) + " |", "|---|" + "---|" * len(cols)]
    for sc in scs: L.append(f"| {sc} | " + " | ".join("%.1f" % d.get(sc, float("nan")) for _, d in cols) + " |")
    L += [""] + [f"- {e}: `{json.dumps(c['params'])}`; top-10 range {c['top10_total_range'][0]:.2f}-{c['top10_total_range'][1]:.2f}" for e, c in C.items()]
    if all(os.path.exists(os.path.join(ROOT, f"robust_summary_{t}_s{sd}.md")) for t in ("v20", "v14") for sd in SEEDS):
        T = {(t, sd): table(os.path.join(ROOT, f"robust_summary_{t}_s{sd}.md")) for t in ("v20", "v14") for sd in SEEDS}
        meth = [("v20", "Ours-v1 winner", "v1 (v2.0)"), ("v20", "Ours-v2 winner", "v2 (v2.0)"), ("v20", "Ours-v3 winner", "v3 (v2.0)"), ("v14", "Ours-v1 winner", "v1 (v1.4)"), ("v14", "Ours-v2 winner", "v2 (v1.4)"),
                ("v20", "B-code winner", "B-code (v2.0)"), ("v20", "B-paper winner", "B-paper (v2.0)")]
        L += ["", f"## Held-out synthetic-source stress test (FRESH seeds {SEEDS[0]} and {SEEDS[1]}; mean of both; false%+missed%; real-slice bases with injected sources)", "",
              "| Variant | " + " | ".join(lab for _, _, lab in meth) + " |", "|---|" + "---|" * len(meth)]
        rows = [r for r in T[("v20", SEEDS[0])] if r not in ("all variants", "all except walker")] + ["all variants", "all except walker"]
        for r in rows + ["tuned-family mean"]:
            if r == "tuned-family mean": L.append(f"| {r} (steady, jitter_s, drift, switch) | " + " | ".join("%.1f" % (sum(T[(t, sd)][f][m] for sd in SEEDS for f in ("steady", "jitter_s", "drift", "switch")) / 8) for t, m, _ in meth) + " |"); continue
            L.append(f"| {r} | " + " | ".join("%.1f" % (sum(T[(t, sd)][r][m] for sd in SEEDS) / 2) for t, m, _ in meth) + " |")
    lp = os.path.join(ROOT, "latency_report_v20.md")
    if os.path.exists(lp): L += ["", "## Detection delay (splice test, report only)", ""] + [l for l in open(lp, encoding="utf-8").read().splitlines()[2:] if l.strip()]
L += ["", "Any FAIL above: paste its Note and the step name. Nothing here is frozen; test_* and the fresh synthetic test are untouched. Dev numbers are in-sample, the stress table is the first out-of-sample look."]
open(os.path.join(ROOT, "summary_v20.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", os.path.join(ROOT, "summary_v20.md"))
