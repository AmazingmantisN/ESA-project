# syn_summary (eval_test_v11.csv); strict error %, scenarios weighted equally

| Group | scenarios | ours | ours_v2 | bcode | bpaper | bcode_asis |
|---|---|---|---|---|---|---|
| core | 16 | 14.9 | 18.3 | 40.4 | 28.1 | 66.0 |
| fps | 6 | 24.0 | 30.1 | 63.0 | 27.0 | 47.6 |
| unseen | 6 | 19.4 | 23.3 | 57.0 | 47.7 | 58.0 |
| ALL | 28 | 17.8 | 21.9 | 48.8 | 32.1 | 60.3 |

Paired differences (negative = first is better), 95 % bootstrap over seeds within scenario:

| Group | Comparison | Diff [95 % CI] | first better in |
|---|---|---|---|
| ALL | ours - bpaper | -14.24 [-17.55, -10.88] | 21/28 scenarios |
| ALL | ours - bcode | -30.99 [-34.37, -27.43] | 21/28 scenarios |
| ALL | ours_v2 - bpaper | -10.16 [-14.78, -5.55] | 16/28 scenarios |
| ALL | ours_v2 - bcode | -26.91 [-30.92, -22.94] | 20/28 scenarios |
| ALL | ours - ours_v2 | -4.08 [-7.15, -0.98] | 8/28 scenarios |
| core | ours - bpaper | -13.18 [-17.05, -9.14] | 13/16 scenarios |
| core | ours - bcode | -25.47 [-29.50, -21.46] | 11/16 scenarios |
| core | ours_v2 - bpaper | -9.82 [-15.92, -3.79] | 11/16 scenarios |
| core | ours_v2 - bcode | -22.11 [-26.45, -17.60] | 11/16 scenarios |
| core | ours - ours_v2 | -3.36 [-7.03, +0.47] | 4/16 scenarios |
| unseen | ours - bpaper | -28.33 [-35.60, -21.06] | 6/6 scenarios |
| unseen | ours - bcode | -37.66 [-47.45, -27.97] | 5/6 scenarios |
| unseen | ours_v2 - bpaper | -24.36 [-33.46, -15.26] | 4/6 scenarios |
| unseen | ours_v2 - bcode | -33.69 [-45.02, -22.61] | 4/6 scenarios |
| unseen | ours - ours_v2 | -3.97 [-11.88, +4.45] | 1/6 scenarios |
| fps | ours - bpaper | -2.97 [-10.82, +5.42] | 2/6 scenarios |
| fps | ours - bcode | -39.04 [-45.36, -32.07] | 5/6 scenarios |
| fps | ours_v2 - bpaper | +3.13 [-7.21, +13.21] | 1/6 scenarios |
| fps | ours_v2 - bcode | -32.95 [-41.48, -24.20] | 5/6 scenarios |
| fps | ours - ours_v2 | -6.09 [-12.93, +0.47] | 3/6 scenarios |
