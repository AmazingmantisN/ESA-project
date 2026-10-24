# dht_lag.md (frozen methods; DHT reads e degC off the true room value; steady +8 C laptop on dev slices; synthetic; NOT a result)

e = r x tau: e.g. room warming 0.1 C/min with a 5-min-lag DHT -> e = -0.5 (DHT reads low). Error % = false + missed, mean of empty and single stream.

| e (C) | ours | ours_v2 | bcode | bpaper |
|---|---|---|---|---|
| -3.00 | 1.0 | 0.0 | 50.0 | 50.0 |
| -2.00 | 1.0 | 0.0 | 49.8 | 49.7 |
| -1.00 | 1.0 | 0.0 | 97.9 | 97.8 |
| -0.50 | 1.0 | 0.0 | 58.9 | 68.6 |
| -0.25 | 1.0 | 0.0 | 45.7 | 27.2 |
| +0.00 | 1.0 | 0.0 | 22.2 | 11.9 |
| +0.25 | 1.0 | 0.0 | 8.5 | 11.9 |
| +0.50 | 1.0 | 0.0 | 15.3 | 10.2 |
| +1.00 | 1.0 | 0.0 | 23.9 | 20.5 |
| +2.00 | 1.0 | 0.0 | 48.4 | 48.5 |
| +3.00 | 1.0 | 0.0 | 50.0 | 50.0 |
