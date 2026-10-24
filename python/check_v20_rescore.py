"""Consistency check for protocol v2.0: re-score the v1.4 winners with the v2.0 tool on the two REAL dev pools.

The v2.0 tool must give the same numbers as v1.4 on the 10 original and 16 robustness streams (pool means = the v1.4 dev_orig_total / dev_rob_total). A mismatch
means the tool, the data or the binary changed. Also prints the v1.4 winners' scores on the 80 synthetic dev streams (free benchmark for the sweep).
  python check_v20_rescore.py          # ../tuning_results_v14/tune_candidates.json vs protocol v2.0.   Exit code 0 = all match.
"""
import argparse, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import tune_sweep as T, tune_sweep_v2 as V
ap = argparse.ArgumentParser(); ap.add_argument("--cand", default=os.path.join(ROOT, "tuning_results_v14", "tune_candidates.json"))
ap.add_argument("--protocol", default=os.path.join(ROOT, "tuning_protocol_v2.0.json")); a = ap.parse_args()
V.setup2(os.path.abspath(a.protocol)); V.verify_synth(T.G["P"]); bad = 0; OUT = {}
for e, c in json.load(open(a.cand))["candidates"].items():
    if e not in T.G["P"]["entries"]: continue
    ag, tot = V.aggregate(T.score((e, c["params"]))); sc = {}
    for f, t in zip(T.G["files"], tot):
        if f in T.G.get("SCEN", {}): sc.setdefault(T.G["SCEN"][f], []).append(float(t))
    OUT[e] = dict(ag, by_scenario={k: float(np.mean(v)) for k, v in sorted(sc.items())})
    old = (c["dev_orig_total"], c["dev_rob_total"]); new = (ag["pool_real_orig"], ag["pool_real_rob"]); ok = max(abs(x - y) for x, y in zip(new, old)) < 5e-3; bad += (not ok)
    print(f"{e:11s} {'PASS' if ok else 'FAIL'}  v1.4 winner re-scored: original-10 {new[0]:.2f} (was {old[0]:.2f}), robustness-16 {new[1]:.2f} (was {old[1]:.2f});  on the 80 synthetic dev streams: {ag['pool_synth_dev']:.2f}")
json.dump(OUT, open(os.path.join(ROOT, "tuning_results_v20", "v14_winners_on_v20_dev.json") if os.path.isdir(os.path.join(ROOT, "tuning_results_v20")) else os.path.join(ROOT, "v14_winners_on_v20_dev.json"), "w"), indent=1)
print("ALL MATCH: v2.0 tool reproduces the v1.4 winners' real dev scores" if bad == 0 else "MISMATCH: do not trust the v2.0 sweep until explained"); sys.exit(0 if bad == 0 else 1)
