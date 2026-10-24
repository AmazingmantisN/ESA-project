"""Convert a papanashi esp32_raw_data.csv into frames.npy (N, 8, 8) in degC, plus metadata.

Usage:
  python load_dataset.py "../data/raw/0 persons/csv_data/esp32_raw_data.csv" ../data/empty.npy
  python load_dataset.py <raw_csv> <out.npy> [--drop-dht-dropouts]

Input schema (esp32_raw_data.csv): timestamp (ISO), gridEye ("[64 floats]"), dht_temperature.
Do NOT feed data.csv here: it has duplicated rows and their algorithm's counts.

Outputs:
  <out>.npy        float32 (N, 8, 8) cleaned frames
  <out>_t.npy      float64 (N,) seconds since first kept frame
  <out>.meta.json  measured frame rate, dropout counts, gaps, per-session temp stats
  <out>_dht.npy    float32 (N,) DHT ambient reading per kept frame; bad readings (<5 degC) are replaced
                   by the last valid reading (first valid reading for a leading run). Needed only by
                   the DHT-threshold baseline (plan Step 5).
  <out>_dhtraw.npy float32 (N,) the DHT readings exactly as recorded (includes the 0.1 / -0.2 dropouts)

Dropped as dropouts: all-zero grids, non-finite or out-of-range values (<0 or >80 degC).
Frames whose DHT reading is bad (<5 degC: 0, 0.1, -0.2 seen) are KEPT by default, because the
grid in those rows is valid and the filter does not use the DHT; they are only counted in the
meta. Use --drop-dht-dropouts to drop them anyway.
NOTE: the all-zero grids from the earlier inspection live in data.csv, not in esp32_raw_data.csv.
Downstream code should convert seconds -> frames with meta["fps_median"].
"""
import argparse, ast, json
import numpy as np
import pandas as pd


def parse_grid(s):
    try:
        v = ast.literal_eval(s)
        a = np.asarray(v, dtype=np.float64)
        return a if a.size == 64 else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--drop-dht-dropouts", action="store_true")
    ap.add_argument("--gap-factor", type=float, default=3.0,
                    help="a gap longer than this x median dt is reported as a gap")
    a = ap.parse_args()

    df = pd.read_csv(a.src)
    need = {"timestamp", "gridEye", "dht_temperature"}
    if not need <= set(df.columns):
        raise SystemExit(f"expected columns {sorted(need)}, got {list(df.columns)}. "
                         "Is this data.csv instead of esp32_raw_data.csv?")
    n_raw = len(df)

    grids = [parse_grid(s) for s in df["gridEye"]]
    unparsable = np.array([g is None for g in grids])
    G = np.array([g if g is not None else np.zeros(64) for g in grids])
    ts = pd.to_datetime(df["timestamp"])
    dht = df["dht_temperature"].to_numpy(dtype=float)

    all_zero = (G == 0).all(axis=1)
    bad_range = ~np.isfinite(G).all(axis=1) | (G < 0).any(axis=1) | (G > 80).any(axis=1)
    bad_dht = ~(dht >= 5)
    drop = unparsable | all_zero | bad_range
    if a.drop_dht_dropouts:
        drop = drop | bad_dht

    keep = ~drop
    frames = G[keep].reshape(-1, 8, 8).astype(np.float32)
    t = (ts[keep] - ts[keep].iloc[0]).dt.total_seconds().to_numpy()

    order_ok = bool(np.all(np.diff(t) > 0))
    dt = np.diff(t)
    med_dt = float(np.median(dt))
    big = np.where(dt > a.gap_factor * med_dt)[0]
    gaps = [{"after_frame": int(i), "at_s": round(float(t[i]), 2), "gap_s": round(float(dt[i]), 2)}
            for i in big]
    # repeats are a property of the source file; report so nobody assumes they are absent
    repeats = int((np.diff(frames.reshape(len(frames), -1), axis=0) == 0).all(axis=1).sum())

    meta = {
        "source": a.src, "rows_raw": n_raw, "frames_kept": int(len(frames)),
        "dropped_total": int(drop.sum()),
        "dropped_all_zero_grid": int(all_zero.sum()),
        "dropped_bad_range": int(bad_range.sum()),
        "dropped_unparsable": int(unparsable.sum()),
        "rows_with_bad_dht": int(bad_dht.sum()),
        "dht_dropouts_dropped": a.drop_dht_dropouts,
        "fps_median": round(1.0 / med_dt, 3), "median_dt_s": round(med_dt, 4),
        "dt_p95_s": round(float(np.percentile(dt, 95)), 4),
        "duration_s": round(float(t[-1]), 1),
        "timestamps_strictly_increasing": order_ok,
        "n_gaps_over_factor": len(gaps), "gaps": gaps[:20],
        "exact_repeat_frames": repeats,
        "temp_min": round(float(frames.min()), 2), "temp_max": round(float(frames.max()), 2),
        "temp_median": round(float(np.median(frames)), 2),
        "dht_values_kept": sorted({round(float(x), 2) for x in dht[keep]})[:8],
    }
    dht_raw = dht[keep].astype(np.float32)
    good = dht_raw >= 5
    if not good.any(): raise SystemExit("no valid DHT reading in this file")
    dht_clean = dht_raw.copy()
    first = int(np.argmax(good)); last_v = float(dht_raw[first])
    for i in range(len(dht_clean)):                       # forward fill, leading run gets the first valid value
        if good[i]: last_v = float(dht_raw[i])
        else: dht_clean[i] = last_v
    meta["dht_rows_filled"] = int((~good).sum())
    np.save(a.dst.replace(".npy", "_dht.npy"), dht_clean)
    np.save(a.dst.replace(".npy", "_dhtraw.npy"), dht_raw)
    np.save(a.dst, frames)
    np.save(a.dst.replace(".npy", "_t.npy"), t)
    with open(a.dst.replace(".npy", ".meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"{a.src}\n  rows {n_raw} -> kept {len(frames)} (dropped {drop.sum()}: "
          f"{all_zero.sum()} all-zero, {bad_range.sum()} bad range, {unparsable.sum()} unparsable, "
          f"{bad_dht.sum()} rows have bad DHT, {'dropped' if a.drop_dht_dropouts else 'kept'})")
    print(f"  frame rate {meta['fps_median']} Hz (median dt {med_dt*1000:.0f} ms, p95 {meta['dt_p95_s']*1000:.0f} ms), "
          f"duration {meta['duration_s']} s, strictly increasing: {order_ok}")
    print(f"  gaps > {a.gap_factor}x median dt: {len(gaps)}  | exact repeated frames: {repeats}")
    print(f"  temps {meta['temp_min']}..{meta['temp_max']} degC, median {meta['temp_median']}")
    print(f"  saved {a.dst}, {a.dst.replace('.npy','_t.npy')}, {a.dst.replace('.npy','.meta.json')}")
    if not (20 <= meta["temp_median"] <= 35):
        print("  WARNING: median temp outside 20-35 degC, check the input")


if __name__ == "__main__":
    main()
