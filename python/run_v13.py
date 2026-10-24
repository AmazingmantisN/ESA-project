"""One command for protocol v1.3: build, checks, sweep, v1.2 consistency check, held-out stress test, then summary_v13.md (short, paste it back).

From the python folder (cmd):
  python run_v13.py --jobs 18             # official run (about 10-15 min on 18 jobs)
  python run_v13.py --quick --jobs 18     # tiny smoke run, NOT the protocol run
  python run_v13.py --skip-tune           # only redo the checks/summary from existing tuning_results_v13

What it does, in order:
  1. build run_pc + test_modes (g++), run test_modes (expect 0 failed)
  2. tune_sweep.py --protocol ../tuning_protocol_v1.3.json  (dev only: 10 original + 16 robustness streams; verifies the stream manifest first)
  3. check_v13_vs_v12.py  (stage-1 trials must score identically on the 10 original streams)
  4. robust_check.py on HELD-OUT seeds 44 and 55 for the v1.3 winners and, if ../tuning_results/tune_candidates.json (v1.2) exists, for the v1.2 winners
  5. summary_v13.md
Nothing is frozen and test_* is never opened.
"""
import argparse, datetime, json, os, platform, re, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PC, PY = os.path.join(ROOT, "pc_test"), os.path.join(ROOT, "python"); EXE = ".exe" if os.name == "nt" else ""
PROT = os.path.join(ROOT, "tuning_protocol_v1.3.json"); R13 = os.path.join(ROOT, "tuning_results_v13"); R12 = os.path.join(ROOT, "tuning_results")
ap = argparse.ArgumentParser(); ap.add_argument("--skip-tune", action="store_true"); ap.add_argument("--quick", action="store_true"); ap.add_argument("--jobs", type=int); a = ap.parse_args()
checks = []; t_all = time.time(); SEEDS = (44, 55)

def run(cmd, cwd):
    t = time.time(); r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    return r.returncode, (r.stdout + "\n" + r.stderr).strip(), time.time() - t

def add(name, ok, secs, note=""):
    checks.append((name, "SKIPPED" if ok is None else ("PASS" if ok else "FAIL"), secs, note.replace("\n", " ")[:200])); print(f"[{checks[-1][1]:7s}] {name} ({secs:.0f} s) {note[:140]}", flush=True)

def tail(txt, n=3): return " | ".join(txt.splitlines()[-n:])

def table(path):
    """first table of a robust_summary md -> {row label: {method: value}}"""
    rows = [l for l in open(path, encoding="utf-8").read().splitlines()]; i = next(k for k, l in enumerate(rows) if l.startswith("| Variant"))
    names = [c.strip() for c in rows[i].strip("|").split("|")][1:]; out = {}
    for l in rows[i + 2:]:
        if not l.startswith("|"): break
        c = [x.strip().strip("*") for x in l.strip("|").split("|")]; out[c[0]] = dict(zip(names, map(float, c[1:])))
    return out

rc1, o1, s1 = run(["g++", "-O2", "-std=c++17", "-o", f"run_pc{EXE}", "run_pc.cpp"], PC)
rc2, o2, s2 = run(["g++", "-O2", "-std=c++17", "-o", f"test_modes{EXE}", "test_modes.cpp"], PC)
add("build run_pc + test_modes (g++)", rc1 == 0 and rc2 == 0, s1 + s2, "" if rc1 == rc2 == 0 else tail(o1 + o2))
ok_build = rc1 == 0 and rc2 == 0
if ok_build:
    rc, o, s = run([os.path.join(PC, f"test_modes{EXE}")], PC); m = re.findall(r"(\d+) tests, (\d+) failed", o)
    add("test_modes (expect 35 tests, 0 failed)", bool(m) and m[-1][1] == "0", s, (m[-1][0] + " tests, " + m[-1][1] + " failed") if m else tail(o))
    if not a.skip_tune:
        cmd = [sys.executable, "tune_sweep.py", "--protocol", PROT] + (["--quick"] if a.quick else []) + (["--jobs", str(a.jobs)] if a.jobs else [])
        rc, o, s = run(cmd, PY); add("tune_sweep protocol v1.3 (dev only)" + (" QUICK TEST" if a.quick else ""), rc == 0, s, tail(o, 2) if rc else "")
        ok_build = rc == 0
    else: add("tune_sweep", None, 0, "skipped")
    if ok_build:
        rc, o, s = run([sys.executable, "check_v13_vs_v12.py"], PY); add("check_v13_vs_v12 (original streams identical to v1.2" + (", quick: only trials present in both)" if a.quick else ")"), rc == 0, s, tail(o, 1))
        c13 = os.path.join(R13, "tune_candidates.json"); c12 = os.path.join(R12, "tune_candidates.json"); sets = [("v13", c13)] + ([("v12", c12)] if os.path.exists(c12) else [])
        for tag, cj in sets:
            for sd in SEEDS:
                md = os.path.join(ROOT, f"robust_summary_{tag}_s{sd}.md")
                rc, o, s = run([sys.executable, "robust_check.py", "--cand", cj, "--seed", str(sd), "--md", md], PY); add(f"robust_check held-out seed {sd}, {tag} winners", rc == 0, s, tail(o, 1) if rc else "")

L = [f"# summary_v13.md ({datetime.datetime.now():%d %b %Y %H:%M})", "", f"Python {platform.python_version()}, {os.cpu_count()} cores, {platform.system()}. Total {time.time() - t_all:.0f} s.", ""]
cj13 = os.path.join(R13, "tune_candidates.json"); cj12 = os.path.join(R12, "tune_candidates.json")
J = json.load(open(cj13)) if os.path.exists(cj13) else None; J12 = json.load(open(cj12))["candidates"] if os.path.exists(cj12) else {}
if J: L += [f"Protocol v{J['protocol_version']} json sha256 {J['protocol_sha256']}", f"md sha256 {J.get('protocol_md_sha256')}", f"official_run={J['official_run']} jobs={J.get('jobs')} dev streams={len(J['dev_streams'])}", ""]
L += ["## Checks", "", "| Check | Result | Seconds | Note |", "|---|---|---|---|"] + [f"| {n} | {r} | {s:.0f} | {note} |" for n, r, s, note in checks]
if J:
    L += ["", "## v1.3 dev winners (NOT frozen). Error = false% + missed%, lower is better", "",
          "| Entry | Total % (26 streams) | False | Missed | Worst stream | Original 10 | Robustness 16 | v1.2 winner on original 10 | Stage-1 best | Untuned ref | Edge params |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e, c in J["candidates"].items():
        v12 = J12.get(e, {}).get("dev_total"); L.append(f"| {e} | {c['dev_total']:.2f} | {c['dev_false']:.2f} | {c['dev_missed']:.2f} | {c['dev_worst_stream']:.1f} | {c.get('dev_orig_total', float('nan')):.2f} | {c.get('dev_rob_total', float('nan')):.2f} | "
                                                       f"{'%.2f' % v12 if v12 is not None else 'n/a'} | {c['stage1_best_total']:.2f} | {c['reference_total']:.2f} | {', '.join(c['edge_params']) or 'none'} |")
    L += ["", "Robustness-16 error by variant (v1.3 winner, dev):", "", "| Entry | " + " | ".join(next(iter(J["candidates"].values())).get("dev_rob_by_variant", {"?": 0})) + " |", "|---|" + "---|" * len(next(iter(J["candidates"].values())).get("dev_rob_by_variant", {"?": 0}))]
    for e, c in J["candidates"].items(): L.append(f"| {e} | " + " | ".join("%.1f" % v for v in c.get("dev_rob_by_variant", {}).values()) + " |")
    L += [""] + [f"- {e}: `{json.dumps(c['params'])}`; top-10 range {c['top10_total_range'][0]:.2f}-{c['top10_total_range'][1]:.2f}" for e, c in J["candidates"].items()]
    # held-out stress
    have = {(t, sd): os.path.join(ROOT, f"robust_summary_{t}_s{sd}.md") for t in ("v12", "v13") for sd in SEEDS}
    have = {k: v for k, v in have.items() if os.path.exists(v)}
    if ("v13", SEEDS[0]) in have:
        T = {k: table(v) for k, v in have.items()}; tags = [t for t in ("v12", "v13") if all((t, sd) in T for sd in SEEDS)]
        meth = [("Ours-v1 winner", "v1"), ("Ours-v2 winner", "v2"), ("B-code winner", "B-code"), ("B-paper winner", "B-paper")]
        L += ["", f"## Held-out synthetic stress test (seeds {SEEDS[0]} and {SEEDS[1]}, never used in tuning; mean of both seeds; false%+missed%)", "",
              "| Variant | " + " | ".join(f"{lab} {'v1.2' if t == 'v12' else 'v1.3'}" for _, lab in meth for t in tags) + " |", "|---|" + "---|" * (len(meth) * len(tags))]
        rows = [r for r in T[("v13", SEEDS[0])] if r not in ("all variants", "all except walker")] + ["all variants", "all except walker"]
        for r in rows: L.append(f"| {r} | " + " | ".join("%.1f" % (sum(T[(t, sd)][r][m] for sd in SEEDS) / len(SEEDS)) for m, _ in meth for t in tags) + " |")
        L += ["", "'all except walker' per seed (to see the seed-to-seed spread): " + "; ".join(f"{('v1.2' if t == 'v12' else 'v1.3')} seed {sd}: " + ", ".join(f"{lab} {T[(t, sd)]['all except walker'][m]:.1f}" for m, lab in meth) for t in tags for sd in SEEDS)]
L += ["", "Any FAIL above: paste its Note and the step name. jitter_m and walker are reported only (not tuned). Nothing here is frozen or tested on test_* streams."]
open(os.path.join(ROOT, "summary_v13.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", os.path.join(ROOT, "summary_v13.md"))
