"""One command: build, self-checks, stream rebuild, (optional) ESP32 protocol check, tuning sweep, then summary.md.

From the python folder:
  python run_all.py                       # everything except the ESP32 check
  python run_all.py --port COM7           # also check the real ESP32 against run_pc (close the Serial Monitor first)
  python run_all.py --skip-tune           # checks only
  python run_all.py --quick               # tiny tuning smoke test (not the protocol run)
  python run_all.py --jobs 18             # parallel workers for tuning (default cores-2)
Paste summary.md (project root) back to Claude: it is short on purpose.
"""
import argparse, datetime, json, os, platform, re, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PC, PY = os.path.join(ROOT, "pc_test"), os.path.join(ROOT, "python"); EXE = ".exe" if os.name == "nt" else ""
ap = argparse.ArgumentParser(); ap.add_argument("--port"); ap.add_argument("--skip-tune", action="store_true"); ap.add_argument("--quick", action="store_true")
ap.add_argument("--jobs", type=int); a = ap.parse_args()
checks = []; t_all = time.time()

def run(cmd, cwd):
    t = time.time(); r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    return r.returncode, (r.stdout + "\n" + r.stderr).strip(), time.time() - t

def add(name, ok, secs, note=""):
    checks.append((name, "SKIPPED" if ok is None else ("PASS" if ok else "FAIL"), secs, note.replace("\n", " ")[:200])); print(f"[{checks[-1][1]:7s}] {name} ({secs:.0f} s) {note[:120]}", flush=True)

def tail(txt, n=6): return " | ".join(txt.splitlines()[-n:])

rc1, o1, s1 = run(["g++", "-O2", "-std=c++17", "-o", f"run_pc{EXE}", "run_pc.cpp"], PC)
rc2, o2, s2 = run(["g++", "-O2", "-std=c++17", "-o", f"test_modes{EXE}", "test_modes.cpp"], PC)
add("build run_pc + test_modes (g++)", rc1 == 0 and rc2 == 0, s1 + s2, "" if rc1 == rc2 == 0 else tail(o1 + o2))
if rc1 == 0 and rc2 == 0:
    rc, o, s = run([os.path.join(PC, f"test_modes{EXE}")], PC); m = re.findall(r"(\d+) tests, (\d+) failed", o)
    add("test_modes (expect 35 tests, 0 failed)", bool(m) and m[-1][1] == "0", s, m[-1][0] + " tests, " + m[-1][1] + " failed" if m else tail(o))
    rc, o, s = run([sys.executable, "check_v1_equiv.py"], PC); add("check_v1_equiv (v2 reproduces v1 exactly)", rc == 0, s, tail(o, 2))
    rc, o, s = run([sys.executable, "check_v2_nested.py"], PC); add("check_v2_nested (v2 defaults == v1; length of nested equivalence)", rc == 0, s, tail(o, 2))
    rc, o, s = run([sys.executable, "make_real_streams.py"], PY)
    n = {}
    for name in ("test_empty_clean", "test_single_clean"):
        p = os.path.join(ROOT, "data", "streams", name + ".csv")
        n[name] = sum(1 for _ in open(p)) - 1 if os.path.exists(p) else -1
    add("make_real_streams (guard gap; expect test_empty 1152, test_single 918 frames)", rc == 0 and n["test_empty_clean"] == 1152 and n["test_single_clean"] == 918, s, f"test_empty {n['test_empty_clean']}, test_single {n['test_single_clean']}")
    if a.port:
        rc, o, s = run([sys.executable, "check_firmware_protocol.py", "--port", a.port, "--stream", os.path.join("..", "data", "streams", "dev_single_laptop_weak.csv"), "--frames", "600"], PC)
        add(f"ESP32 firmware vs run_pc on {a.port}", rc == 0, s, tail(o, 3))
    else: add("ESP32 firmware vs run_pc (needs --port COM7)", None, 0, "not run")
    if not a.skip_tune:
        cmd = [sys.executable, "tune_sweep.py"] + (["--quick"] if a.quick else []) + (["--jobs", str(a.jobs)] if a.jobs else [])
        rc, o, s = run(cmd, PY); add("tune_sweep (protocol v1.2, dev only)" + (" QUICK TEST" if a.quick else ""), rc == 0, s, tail(o, 2) if rc else "")
    else: add("tune_sweep", None, 0, "skipped")
else: print("build failed; stopping.")

L = [f"# summary.md ({datetime.datetime.now():%d %b %Y %H:%M})", "", f"Python {platform.python_version()}, {os.cpu_count()} cores, {platform.system()}. Total {time.time() - t_all:.0f} s.", ""]
cj = os.path.join(ROOT, "tuning_results", "tune_candidates.json")
if os.path.exists(cj) and not a.skip_tune:
    J = json.load(open(cj)); L += [f"Protocol v{J['protocol_version']} sha256 {J['protocol_sha256'][:16]}... md {str(J.get('protocol_md_sha256'))[:16]}... official_run={J['official_run']} jobs={J.get('jobs')}", ""]
L += ["## Checks", "", "| Check | Result | Seconds | Note |", "|---|---|---|---|"] + [f"| {n} | {r} | {s:.0f} | {note} |" for n, r, s, note in checks]
if os.path.exists(cj) and not a.skip_tune:
    L += ["", "## Tuning candidates (dev only, NOT frozen)", "", "| Entry | Best total % | False % | Missed % | Worst stream % | Stage-1 best % | Untuned ref % | Won in stage | Edge params |", "|---|---|---|---|---|---|---|---|---|"]
    for e, c in J["candidates"].items():
        L.append(f"| {e} | {c['dev_total']:.2f} | {c['dev_false']:.2f} | {c['dev_missed']:.2f} | {c['dev_worst_stream']:.1f} | {c['stage1_best_total']:.2f} | {c['reference_total']:.2f} | {c['winner_stage']} | {', '.join(c['edge_params']) or 'none'} |")
    L += [""] + [f"- {e}: `{json.dumps(c['params'])}`; top-10 range {c['top10_total_range'][0]:.2f}-{c['top10_total_range'][1]:.2f}" for e, c in J["candidates"].items()]
L += ["", "Any FAIL above: paste the Note text and the failing step's name. Nothing here is frozen or tested on test_* streams."]
open(os.path.join(ROOT, "summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", os.path.join(ROOT, "summary.md"))
