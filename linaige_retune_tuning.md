# LINAIGE re-tune: Session 1 tuning (official, 24 Oct 2026 23:09)

protocol sha256 6ce76d198dbed8e25cec108b40bff5aab0f057750227de4253e28812a506f6cf
params file sha256 8544166aaf210d77e353b3fce08d207948e429bd7123eb5094d106f9102df68a

| Method | tuned params (Session 1) | Session-1 total % | of which false / missed | frozen v1.4 params on Session 1 | untuned reference | edge-limited |
|---|---|---|---|---|---|---|
| Ours-v1 | {"window_s": 0.5, "drift": 0.1957, "contrast": 0.8363, "k": 1.175, "smooth_s": 0.0, "maxmissed_s": 0.5} | 22.63 | 0.63 / 22.00 | 72.63 | 71.71 | window_s |
| Ours-v2 | {"window_s": 0.5, "drift": 0.3628, "contrast": 0.7516, "k": 0.9099, "smooth_s": 0.0, "maxmissed_s": 0.5, "persist_s": 0.5024, "hyst_s": 1.713, "cand_policy": 4.0, "assign_mode": 1.0} | 19.99 | 1.62 / 18.37 | 53.54 | 71.71 | window_s |
| B-paper | {"timebase": "frames", "drift": 1.2002, "dht_offset": 1.3, "smooth_s": 0.0, "maxmissed_s": 0.5} | 39.24 | 16.07 / 23.16 | 60.90 | 47.76 | none |
| B-code | {"npersist": 80.0, "drift": 0.1159, "dht_offset": 1.3, "smooth_s": 0.0, "maxmissed_s": 0.5} | 39.54 | 15.97 / 23.56 | 54.24 | 59.53 | none |

Session-1 numbers are in-sample (the tuning set); they say nothing about transfer. Commit params_linaige_session1.json and its .sha256 BEFORE running --test.
