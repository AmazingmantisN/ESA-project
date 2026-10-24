"""Steady-vs-stress trade-off of the tuning rounds (DECLARED POST-HOC, descriptive; reads existing result files, runs nothing).

Combines  posthoc_versions.md (test_* total %, steady sources)  with  robust_summary_v1{2,3,4}_s{101,202}.md (held-out synthetic stress, row 'all except walker' and row 'steady').
Question it answers: does a method have to give up steady accuracy to be robust? A method that is good on both axes dominates.
  python tradeoff.py [--posthoc ../posthoc_versions.md] [--dir ..] [--md ../tradeoff.md] [--png ../tradeoff.png]
Stress columns: Ours-v1 winner, Ours-v2 winner, B-code winner, B-paper winner (columns are found by header name). Mean of the two seeds.
"""
import argparse, os, re
import numpy as np
ap = argparse.ArgumentParser(); H = os.path.dirname(os.path.abspath(__file__)); ap.add_argument("--posthoc", default=os.path.join(H, "..", "posthoc_versions.md")); ap.add_argument("--dir", default=os.path.join(H, ".."))
ap.add_argument("--md", default=os.path.join(H, "..", "tradeoff.md")); ap.add_argument("--png", default=os.path.join(H, "..", "tradeoff.png")); a = ap.parse_args()
ENT = {"ours": "Ours-v1 winner", "ours_v2": "Ours-v2 winner", "bcode": "B-code winner", "bpaper": "B-paper winner"}; VER = {"v1.2": "v12", "v1.3": "v13", "v1.4": "v14"}; SEEDS = (101, 202)
test = {}
for ln in open(a.posthoc, encoding="utf-8"):
    m = re.match(r"\|\s*(ours|ours_v2|bcode|bpaper)\s*\|\s*(v1\.\d)\s*\|\s*([\d.]+)\s*\[\s*([\d.]+),\s*([\d.]+)\]", ln)
    if m: test[(m[1], m[2])] = (float(m[3]), float(m[4]), float(m[5]))
def stress(v, row):
    out = {e: [] for e in ENT}
    for s in SEEDS:
        lines = open(os.path.join(a.dir, f"robust_summary_{VER[v]}_s{s}.md"), encoding="utf-8").read().splitlines(); hdr = None
        for i, ln in enumerate(lines):
            if ln.startswith("| Variant"): hdr = [c.strip() for c in ln.strip().strip("|").split("|")]
            elif hdr and ln.startswith("|") and ln.strip("| ").replace("*", "").split("|")[0].strip().lower().startswith(row):
                cells = [c.strip().replace("*", "") for c in ln.strip().strip("|").split("|")]
                for e, name in ENT.items(): out[e].append(float(cells[hdr.index(name)]))
                break
    return {e: np.mean(x) for e, x in out.items() if x}
S = {v: stress(v, "all except walker") for v in VER}; ST = {v: stress(v, "steady") for v in VER}
L = ["# tradeoff.md - DECLARED POST-HOC, descriptive (existing results only)", "",
     "Test = held-out test_* total % (steady injected sources). Stress = held-out synthetic robustness, seeds 101/202 mean: 'all except walker' and 'steady' rows. Lower is better on every column.", "",
     "| Entry | Version | Test steady % [95 % CI] | Stress steady % | Stress all-except-walker % | Good on both (test<15 and stress<20)? |", "|---|---|---|---|---|---|"]
for e in ENT:
    for v in VER:
        if (e, v) not in test or e not in S[v]: continue
        t = test[(e, v)]; ok = "yes" if t[0] < 15 and S[v][e] < 20 else "no"
        L.append(f"| {e} | {v} | {t[0]:.2f} [{t[1]:.2f}, {t[2]:.2f}] | {ST[v].get(e, float('nan')):.1f} | {S[v][e]:.1f} | {ok} |")
L += ["", "Reading: a method that needs a different tuning round to be good on each axis (low on one, high on the other) has a real trade-off; one that is low on both in a single round does not.",
      "Thresholds 15 / 20 are descriptive cut-offs chosen for the table, not pre-registered tests."]
open(a.md, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    col = {"ours": "#1f77b4", "ours_v2": "#2ca02c", "bcode": "#d62728", "bpaper": "#ff7f0e"}; fig, ax = plt.subplots(figsize=(6.2, 4.6))
    for e in ENT:
        pts = [(test[(e, v)][0], S[v][e], v) for v in VER if (e, v) in test and e in S[v]]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", color=col[e], label=e, alpha=.85)
        for x, y, v in pts: ax.annotate(v[1:], (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)
    ax.set_xlabel("Test error, steady sources (%)"); ax.set_ylabel("Held-out stress error, all except walker (%)"); ax.legend(frameon=False); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(a.png, dpi=200); print("wrote", a.png)
except Exception as ex: print("no figure:", ex)
