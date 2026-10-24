"""Robustness check (Step 5e): do the tuned dev winners still work when the injected heat source is NOT perfectly steady?

WHY: the dev laptops/heaters are perfectly steady (only a slow 0.3 C wobble). Ours-v2's winner (origin gate) can separate such a source from a
person trivially: it never moves, a person always does. This script rebuilds the SAME dev slices (dev_empty_clean, dev_single_clean) with
injected sources that behave less ideally, then scores every winner on them with the unchanged protocol metric (warm-up 30 s, false% + missed%).

  python robust_check.py                      # uses ../tuning_results/tune_candidates.json, writes ../data/robust/ and ../robust_summary.md
  python robust_check.py --cand path.json     # other candidates file

Variants (each at +3 C "weak" and +8 C, laptop size sigma 0.7 px, position (1,1) as in dev):
  steady    control: same as dev (should reproduce the dev numbers roughly)
  jitter_s  position wanders 0.10 px/frame (white) + fast amplitude flicker 0.3 C (AR 0.8): a laptop with a fan
  jitter_m  position wanders 0.25 px/frame + flicker 0.6 C: a rough laptop
  drift     the source slides 1.5 px along the row over the stream (slow convection / object nudged)
  switch    source OFF for the first 35%, ramps on over 5 s (laptop opened), jumps 1 px at 70% (moved)
  walker    ADVERSARY: random walk 0.35 px/frame, i.e. behaves like a person. Every motion-based rule should call this a person;
            it is shown only to mark the ceiling nobody can beat without Layer 2.
Reads dev_* clean streams only. Nothing here is a result: it is a stress test of dev winners with synthetic sources. test_* is never opened.
Extra diagnostic rows: the v2 winner with cand_policy 4 and 0 (which part of v2 matters).
"""
import argparse, glob, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
ap = argparse.ArgumentParser(); ap.add_argument("--cand", default=os.path.join(ROOT, "tuning_results", "tune_candidates.json"))
ap.add_argument("--data", default=os.path.join(ROOT, "data")); ap.add_argument("--seed", type=int, default=77)
ap.add_argument("--md", default=os.path.join(ROOT, "robust_summary.md")); ap.add_argument("--protocol", default=None); a = ap.parse_args()

sys.path.insert(0, HERE)
import tune_sweep as T
src_dir = os.path.join(a.data, "streams"); out_dir = os.path.join(a.data, "robust"); os.makedirs(out_dir, exist_ok=True)
for f in glob.glob(os.path.join(out_dir, "rob_*")): os.remove(f)
import robust_lib as R
BASES, AMPS = R.BASES, R.AMPS
VARIANTS = ["steady", "jitter_s", "jitter_m", "drift", "switch", "walker"]   # unchanged since Step 5e (jitter_xs is tuning-only, v1.3)

rng = np.random.default_rng(a.seed); made = 0
for b in BASES:
    head, body, lab, side, fps, frames = R.read_base(src_dir, b)
    for v in VARIANTS:
        for ak, amp in AMPS.items():
            fr = R.inject(frames, fps, v, amp, rng).reshape(len(frames), 64)
            R.write_stream(out_dir, f"rob_{b[4:].replace('_clean', '')}_{v}_{ak}", head, body, lab, fr, side, v, amp)
            made += 1
print(f"built {made} stress streams in {out_dir}")

T.setup(os.path.join(out_dir, "rob_*.csv"), os.path.abspath(a.protocol)) if a.protocol else T.setup(os.path.join(out_dir, "rob_*.csv")); P = T.G["P"]
J = json.load(open(a.cand))["candidates"]; names = [os.path.basename(f)[:-4] for f in T.G["files"]]
methods = [("Ours-v1 winner", "ours", J["ours"]["params"]), ("Ours-v2 winner", "ours_v2", J["ours_v2"]["params"]),
           ("v2 winner, policy 4", "ours_v2", dict(J["ours_v2"]["params"], cand_policy=4)), ("v2 winner, policy 0", "ours_v2", dict(J["ours_v2"]["params"], cand_policy=0)),
           ("B-code winner", "bcode", J["bcode"]["params"]), ("B-paper winner", "bpaper", J["bpaper"]["params"])]
if "ours_v3" in J: methods.insert(2, ("Ours-v3 winner", "ours_v3", J["ours_v3"]["params"]))     # protocol v2.0 candidates only
res = {m[0]: T.score((m[1], m[2])) for m in methods}     # list of (false, missed) per stream, same order as names

def agg(label, pick):
    idx = [i for i, n in enumerate(names) if pick(n)]; fa = np.mean([res[label][i][0] for i in idx]); mi = np.mean([res[label][i][1] for i in idx]); return fa, mi
L = ["# robust_summary.md (stress test of DEV winners; synthetic sources; NOT a result)", "",
     f"{len(names)} streams from dev_empty_clean / dev_single_clean. Cells = false% + missed% (mean over both bases and both amplitudes); smaller is better.", "",
     "| Variant | " + " | ".join(m[0] for m in methods) + " |", "|---|" + "---|" * len(methods)]
for v in VARIANTS:
    L.append(f"| {v} | " + " | ".join("%.1f" % sum(agg(m[0], lambda n, v=v: f"_{v}_" in n)) for m in methods) + " |")
L.append("| **all variants** | " + " | ".join("**%.1f**" % sum(agg(m[0], lambda n: True)) for m in methods) + " |")
L.append("| all except walker | " + " | ".join("%.1f" % sum(agg(m[0], lambda n: "_walker_" not in n)) for m in methods) + " |")
L += ["", "False-alarm % / missed % split (all except walker):", "", "| Method | false % | missed % |", "|---|---|---|"]
for m in methods:
    fa, mi = agg(m[0], lambda n: "_walker_" not in n); L.append(f"| {m[0]} | {fa:.1f} | {mi:.1f} |")
L += ["", "By base (all except walker): empty room (every count is false) vs single person (false + missed):", "", "| Method | empty: false % | single: false % | single: missed % |", "|---|---|---|---|"]
for m in methods:
    fe, _ = agg(m[0], lambda n: n.startswith("rob_empty") and "_walker_" not in n); fs, ms = agg(m[0], lambda n: n.startswith("rob_single") and "_walker_" not in n)
    L.append(f"| {m[0]} | {fe:.1f} | {fs:.1f} | {ms:.1f} |")
L += ["", "Reading guide: if Ours-v2 stays well below Ours-v1 on jitter/drift/switch, its dev gain is not only a 'perfectly steady source' effect.",
      "If it jumps up on jitter_m or walker while v1 does not, the origin gate depends on sources that never move. walker is a ceiling for every motion-based rule."]
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print("\nwrote", a.md)
