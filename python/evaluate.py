"""Score a results CSV (from run_pc or stream_to_esp32).

Usage: python evaluate.py results.csv [--warmup 40]

false-alarm rate = frames where smoothed count > true humans  (static source mistaken for a person)
missed rate      = frames where smoothed count < true humans  (person masked / not seen)
The first --warmup frames are skipped: the filter needs N frames before it can judge a blob.
"""
import argparse
import pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--warmup", type=int, default=40)
a = ap.parse_args()
d = pd.read_csv(a.csv).iloc[a.warmup:]
n = len(d)
fa = (d.smooth > d.humans).mean() * 100
miss = (d.smooth < d.humans).mean() * 100
acc = (d.smooth == d.humans).mean() * 100
print(f"frames scored : {n} (after {a.warmup} warm-up)")
print(f"accuracy      : {acc:6.2f} %")
print(f"false alarms  : {fa:6.2f} %   (count > true humans)")
print(f"missed        : {miss:6.2f} %   (count < true humans)")
if (d.us > 0).any():
    ms = d.us[d.us > 0] / 1000.0
    print(f"latency (ESP32): mean {ms.mean():.3f} ms | p95 {ms.quantile(.95):.3f} ms | max {ms.max():.3f} ms")
