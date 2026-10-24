"""Consistency check for protocol v1.4: the widened ranges changed the stage-1 samples, so instead of comparing trials we RE-SCORE the v1.3 winners.

Every v1.3 winner lies inside the v1.4 ranges (they were only widened), so scoring it with the v1.4 tool on the same 26 dev streams must reproduce its v1.3
dev scores (total, original-10, robustness-16). A mismatch means the tool, data or binary changed between versions. Also a free benchmark: a v1.4 winner whose
dev total is WORSE than its v1.3 winner's is search noise from the larger space (reported, not hidden).

  python check_v14_rescore.py            # ../tuning_results_v13/tune_candidates.json vs protocol v1.4
Exit code 0 = all match.
"""
import argparse, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path.insert(0, HERE)
import tune_sweep as T
ap = argparse.ArgumentParser(); ap.add_argument("--cand", default=os.path.join(ROOT, "tuning_results_v13", "tune_candidates.json"))
ap.add_argument("--protocol", default=os.path.join(ROOT, "tuning_protocol_v1.4.json")); ap.add_argument("--jobs", type=int, default=1); a = ap.parse_args()
T.setup(os.path.join(ROOT, "data", "streams", "dev_*.csv"), os.path.abspath(a.protocol)); T.check_manifest(T.G["P"])
names = [os.path.basename(f)[:-4] for f in T.G["files"]]; J = json.load(open(a.cand))["candidates"]; bad = 0
for e, c in J.items():
    if e not in T.G["P"]["entries"]: continue
    res = T.score((e, c["params"])); tot = [x + y for x, y in res]
    new = (np.mean(tot), np.mean([t for n, t in zip(names, tot) if not n.startswith("dev_rob_")]), np.mean([t for n, t in zip(names, tot) if n.startswith("dev_rob_")]))
    old = (c["dev_total"], c.get("dev_orig_total", np.nan), c.get("dev_rob_total", np.nan)); d = max(abs(x - y) for x, y in zip(new, old))
    ok = d < 5e-3; bad += (not ok)
    print(f"{e:11s} {'PASS' if ok else 'FAIL'}  v1.3 winner re-scored: total {new[0]:.2f} (was {old[0]:.2f}), original-10 {new[1]:.2f} (was {old[1]:.2f}), robustness-16 {new[2]:.2f} (was {old[2]:.2f})")
print("ALL MATCH: v1.4 tool reproduces the v1.3 winners' dev scores" if bad == 0 else "MISMATCH: do not trust the v1.4 sweep until explained")
sys.exit(0 if bad == 0 else 1)
