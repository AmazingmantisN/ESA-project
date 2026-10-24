"""Protocol v1.3: build the robustness DEV streams (non-ideal injected sources) from the two clean dev slices.

  python make_robust_dev.py            # writes data/streams/dev_rob_*.csv/.json + dev_rob_manifest.json (sha256 of every csv)

16 streams = 2 bases (dev_empty_clean, dev_single_clean) x 4 variants (jitter_xs, jitter_s, drift, switch) x 2 amplitudes (+3 C weak, +8 C strong).
NOT built for tuning: jitter_m and walker (reported only, see tuning_protocol.md section 2).
Seed 20261023 (each stream gets its own generator, so the result does not depend on build order). The held-out stress seeds 44 and 55 and the
earlier seed 77 are NOT used here, so robust_check.py on seeds 44/55 stays untouched by tuning.
The generated files are shipped with the protocol: tune_sweep.py checks their sha256 against the manifest and refuses to run if they differ
(different numpy builds could in principle round differently). Reads dev_*_clean only; test_* and expl_* are never opened.
"""
import glob, hashlib, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path.insert(0, HERE)
import robust_lib as R

SEED = 20261023; VARIANTS = ["jitter_xs", "jitter_s", "drift", "switch"]
src = os.path.join(ROOT, "data", "streams")
for f in glob.glob(os.path.join(src, "dev_rob_*")): os.remove(f)
files = {}; idx = 0
for b in R.BASES:
    head, body, lab, side, fps, frames = R.read_base(src, b)
    for v in VARIANTS:
        for ak, amp in R.AMPS.items():
            rng = np.random.default_rng([SEED, idx]); idx += 1
            name = f"dev_rob_{b.split('_')[1]}_{v}_{ak}"          # dev_rob_empty_jitter_s_w ...
            R.write_stream(src, name, head, body, lab, R.inject(frames, fps, v, amp, rng).reshape(len(frames), 64), side, v, amp)
            files[name + ".csv"] = hashlib.sha256(open(os.path.join(src, name + ".csv"), "rb").read()).hexdigest()
json.dump({"seed": SEED, "variants": VARIANTS, "amps": R.AMPS, "files": files}, open(os.path.join(src, "dev_rob_manifest.json"), "w"), indent=1)
print(f"built {len(files)} robustness dev streams in {src} (seed {SEED}); manifest written")
