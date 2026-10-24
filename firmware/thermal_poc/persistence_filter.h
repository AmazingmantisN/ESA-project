// persistence_filter.h
// Persistence-based centroid-drift differentiation for a low-res thermal array.
// Header-only, no dynamic allocation, no ML. Same file is used on the PC test
// harness and on the ESP32 so results are identical on both.
//
// Pipeline per frame:
//   raw ROWSxCOLS -> bilinear upsample (x10) -> adaptive threshold
//   -> flood-fill blobs + weighted centroids -> track blobs across frames
//   -> a track whose centroid stays inside a tiny window for N frames is STATIC
//   -> count tracks that keep drifting (HUMAN) -> majority-vote smoothing
//
// v2 (Plan Step 5) adds BASELINE MODES so the Papanashi et al. rule can be run on the same streams:
//   persistence_mode 0 EXTENT            ours: spread of the last N centroids
//                    1 ENDPOINT_COUNTER  B-paper (their main.py): endpoint displacement over N_window
//                                        updates + consecutive counter (n_persist) + lock/reset
//                    2 BIRTH_ENDPOINT    B-code (their ESP32 firmware/README): distance from the track's
//                                        first position once the path is n_persist long, no counter
//   threshold_mode   0 ROBUST (median+MAD) | 1 DHT (their: dht + dht_offset, >=) | 2 MEANSTD (ablation)
//                    3 CANDIDATE         Ours-v2 (Plan Step 5c, "Layer 1" of the stationary-candidate idea):
//                                        extent test as in mode 0, but a track that stays still for persist_frames
//                                        becomes a STATIONARY CANDIDATE instead of being silently suppressed, and a
//                                        policy (cand_policy) decides whether candidates count as people:
//                                          bit 1 size/warmth gate (blob area >= cand_min_area, peak excess <= cand_max_peak)
//                                          bit 2 origin gate (the track was seen moving at some point)
//                                          bit 8 liveness (Ours-v3): counts if the slow centroid wander (live_frames, live_thresh) says the track lives; OR-ed with the other bits
//                                          bit 4 always count candidates
//                                          0     never count them (= v1 rule)
//                                        A candidate is released only after hyst_frames consecutive moving frames.
//                                        merge_area > 0 flags a very large blob (person + object merged): never suppressed.
//                                        With persist_frames=1, hyst_frames=1, cand_policy=0, merge_area=0 mode 3 equals mode 0
//                                        exactly (checked by check_v1_equiv.py), so v2 is a superset of v1.
//   assign_mode      0 per-track greedy in track order (v1) | 1 global nearest pair first (one-to-one, any mode)
// Not in v2 yet: per-pixel background calibration, gap-aware frame handling (needs timestamps in the stream and
// protocol), the thermal-feature classifier (Layer 2).
// Defaults reproduce v1 exactly (checked by pc_test/check_v1_equiv.py). No dynamic allocation anywhere.
// Nothing in the baseline modes is copied from their code; it is reimplemented from the paper's
// equations and from the behaviour described in baseline_spec.md.
#pragma once
#include <stdint.h>
#include <string.h>
#include <math.h>

struct FilterParams {
  float k_sigma      = 3.0f;   // threshold = background + k_sigma * spread ...
  float min_contrast = 2.5f;   // ... but never less than (median + min_contrast) degC
  int   robust_stats = 1;      // 1: median + MAD (a hot laptop cannot hide a person)
                               // 0: mean + std of the whole frame (original idea; ablation)
  int   min_area     = 40;     // min blob size, in upsampled cells (100 cells ~ 1 source pixel)
  float match_radius = 1.5f;   // max centroid jump between frames to be the same blob (source px)
  int   window       = 30;     // N frames of history for the persistence test (<= 64)
  float drift_thresh = 0.16f;  // centroid extent (source px) below this over N frames => STATIC
  int   max_missed   = 10;     // frames a track may vanish before it is dropped
  int   smooth_window = 5;     // majority vote over last W counts (<= 15)
  // ---- v2 (all defaults = v1 behaviour) ----
  int   threshold_mode   = 0;     // 0 ROBUST, 1 DHT, 2 MEANSTD. Legacy: robust_stats=0 with mode 0 => MEANSTD
  int   persistence_mode = 0;     // 0 EXTENT, 1 ENDPOINT_COUNTER (B-paper), 2 BIRTH_ENDPOINT (B-code)
  float dht_offset   = 0.1f;      // DHT mode: threshold = dht + dht_offset, pixel counts if >= threshold
  int   n_persist    = 100;       // mode 1: consecutive static steps to lock; mode 2: path length (20)
  float reset_thresh = 0.2f;      // modes 1,2: SOURCE px from the locked centroid that un-locks (their 2.0 cells)
  int   centroid_mode = 0;        // 0 intensity-weighted (ours), 1 plain mean of cells (theirs)
  int   match_metric  = 0;        // 0 Euclidean, 1 Manhattan (theirs); match_radius is in SOURCE px
  int   connectivity  = 4;        // flood fill 4 (ours, firmware) or 8 (their OpenCV main.py)
  int   count_static  = 0;        // 1: static tracks are ALSO counted as people (firmware as published)
  int   max_tracks    = 8;        // runtime limit (<= MAX_TRACKS)
  int   max_blobs     = 8;        // runtime limit (<= MAX_BLOBS)
  // ---- Ours-v2 (Step 5c). Only persistence_mode 3 uses all of these; assign_mode works in every mode. Defaults = no change. ----
  int   persist_frames = 1;       // consecutive still frames before a track becomes a STATIONARY CANDIDATE (>= 1)
  int   hyst_frames    = 1;       // consecutive moving frames needed to release a candidate (>= 1)
  int   cand_policy    = 0;       // 0 never count candidates | 1 size/warmth gate | 2 origin gate | 4 always (bit mask)
  int   cand_min_area  = 0;       // gate 1: smoothed blob area in upsampled cells (100 ~ 1 source px) must be >= this
  float cand_max_peak  = 0.f;     // gate 1: smoothed peak excess over the frame median must be <= this degC (0 = no limit)
  int   assign_mode    = 0;       // 0 per-track greedy (v1) | 1 global nearest pair first
  int   merge_area     = 0;       // > 0: a blob whose smoothed area exceeds this is MERGED and its track is never suppressed
  // ---- Ours-v3 (liveness). cand_policy bit 8: a stationary candidate COUNTS if its slow centroid wander is >= live_thresh. Defaults = no change. ----
  int   live_frames    = 1;       // time constant (frames) of the exponential estimate of the centroid's rms deviation (>= 1)
  float live_thresh    = 0.f;     // source px; wander (rms centroid deviation about its slow mean) at or above this => a living (person-like) track
};

// Convert a duration in seconds to a whole number of frames at the measured frame rate.
// Used on the host side (run_pc, sweep, stream_to_esp32) so parameters are defined in
// SECONDS and survive a change of sensor rate. The ESP32 itself still receives frame counts.
// Round-half-up, never less than 1. Double arithmetic so PC and Python agree exactly.
inline int secondsToFrames(double seconds, double fps) {
  int f = (int)(seconds * fps + 0.5);
  return f < 1 ? 1 : f;
}

constexpr int UPSCALE    = 10;   // 8x8 -> 71x71  ((8-1)*10+1)
constexpr int MAX_WINDOW = 64;
constexpr int MAX_TRACKS = 10;
constexpr int MAX_BLOBS  = 16;
constexpr int MAX_SMOOTH = 15;

template <int ROWS, int COLS>
class PersistenceFilter {
 public:
  static_assert(ROWS >= 2 && COLS >= 2, "sensor must be at least 2x2");
  static constexpr int OR    = (ROWS - 1) * UPSCALE + 1;
  static constexpr int OC    = (COLS - 1) * UPSCALE + 1;
  static constexpr int NCELL = OR * OC;

  explicit PersistenceFilter(const FilterParams& p = FilterParams()) { setParams(p); reset(); }

  void setParams(const FilterParams& p) {
    p_ = p;
    if (p_.window < 2) p_.window = 2;
    if (p_.window > MAX_WINDOW) p_.window = MAX_WINDOW;
    if (p_.smooth_window < 1) p_.smooth_window = 1;
    if (p_.smooth_window > MAX_SMOOTH) p_.smooth_window = MAX_SMOOTH;
    if (p_.threshold_mode == 0 && p_.robust_stats == 0) p_.threshold_mode = 2;   // legacy alias
    if (p_.max_tracks < 1) p_.max_tracks = 1;
    if (p_.max_tracks > MAX_TRACKS) p_.max_tracks = MAX_TRACKS;
    if (p_.max_blobs < 1) p_.max_blobs = 1;
    if (p_.max_blobs > MAX_BLOBS) p_.max_blobs = MAX_BLOBS;
    if (p_.connectivity != 8) p_.connectivity = 4;
    if (p_.n_persist < 1) p_.n_persist = 1;
    if (p_.persist_frames < 1) p_.persist_frames = 1;
    if (p_.hyst_frames < 1) p_.hyst_frames = 1;
    if (p_.cand_policy < 0) p_.cand_policy = 0;
    p_.cand_policy &= 15;
    if (p_.live_frames < 1) p_.live_frames = 1;
    if (p_.live_thresh < 0.f) p_.live_thresh = 0.f;
    if (p_.cand_min_area < 0) p_.cand_min_area = 0;
    if (p_.cand_max_peak < 0.f) p_.cand_max_peak = 0.f;
    if (p_.assign_mode != 1) p_.assign_mode = 0;
    if (p_.merge_area < 0) p_.merge_area = 0;
  }

  void reset() {
    for (int i = 0; i < MAX_TRACKS; i++) tr_[i] = Track();
    for (int i = 0; i < MAX_SMOOTH; i++) sm_[i] = 0;
    smHead_ = 0; smFilled_ = 0; rawCount_ = 0; nBlobs_ = 0; nStatic_ = 0; nTracks_ = 0; nCand_ = 0;
  }

  int lastRawCount() const { return rawCount_; }   // unsmoothed count of the last frame
  int lastBlobCount() const { return nBlobs_; }    // all hot blobs, static or not
  int lastStaticCount() const { return nStatic_; } // tracks currently classed STATIC
  int lastTrackCount() const { return nTracks_; }  // all live tracks (modes 1,2: incl. missed-but-kept)
  int lastCandidateCount() const { return nCand_; } // mode 3: stationary candidates this frame, counted or not

  // raw: ROWS*COLS temperatures in degC, row-major. dht: ambient reading (only used by threshold_mode 1).
  // Returns smoothed human count.
  int process(const float* raw, float dht = 0.f) {
    // --- 1. background estimate = median of the raw frame (64 values, trivial cost)
    float tmp[ROWS * COLS];
    for (int i = 0; i < ROWS * COLS; i++) tmp[i] = raw[i];
    for (int i = 1; i < ROWS * COLS; i++) {            // insertion sort
      float v = tmp[i]; int j = i - 1;
      while (j >= 0 && tmp[j] > v) { tmp[j + 1] = tmp[j]; j--; }
      tmp[j + 1] = v;
    }
    const float med = tmp[(ROWS * COLS) / 2];

    // --- 2. bilinear upsampling + frame statistics (shifted by median for precision)
    float sum = 0.f, sumsq = 0.f;
    for (int i = 0; i < OR; i++) {
      float sy = (float)i / UPSCALE; int y0 = (int)sy; if (y0 > ROWS - 2) y0 = ROWS - 2;
      float fy = sy - y0;
      for (int j = 0; j < OC; j++) {
        float sx = (float)j / UPSCALE; int x0 = (int)sx; if (x0 > COLS - 2) x0 = COLS - 2;
        float fx = sx - x0;
        float a = raw[y0 * COLS + x0],       b = raw[y0 * COLS + x0 + 1];
        float c = raw[(y0 + 1) * COLS + x0], d = raw[(y0 + 1) * COLS + x0 + 1];
        float top = a + (b - a) * fx, bot = c + (d - c) * fx;
        float v = top + (bot - top) * fy;
        grid_[i * OC + j] = v;
        float dv = v - med; sum += dv; sumsq += dv * dv;
      }
    }

    // --- 3. adaptive threshold (+ minimum-contrast gate so an empty room yields no blobs)
    float thr;
    if (p_.threshold_mode == 1) {
      thr = dht + p_.dht_offset;                         // baseline: no median, no contrast floor
    } else if (p_.threshold_mode == 0) {
      // median absolute deviation of the raw frame: ignores the few hot pixels, so a
      // very hot static source does not raise the bar above a cooler human.
      for (int i = 0; i < ROWS * COLS; i++) { float d = raw[i] - med; tmp[i] = d < 0.f ? -d : d; }
      for (int i = 1; i < ROWS * COLS; i++) {
        float v = tmp[i]; int j = i - 1;
        while (j >= 0 && tmp[j] > v) { tmp[j + 1] = tmp[j]; j--; }
        tmp[j + 1] = v;
      }
      float sigma = 1.4826f * tmp[(ROWS * COLS) / 2];
      thr = med + p_.k_sigma * sigma;
    } else {
      float mean = sum / NCELL;
      float var = sumsq / NCELL - mean * mean; if (var < 0.f) var = 0.f;
      thr = med + mean + p_.k_sigma * sqrtf(var);
    }
    if (p_.threshold_mode != 1) {
      float floorThr = med + p_.min_contrast;
      if (thr < floorThr) thr = floorThr;
    }
    geq_ = (p_.threshold_mode == 1);                     // their mask is >=, ours is >

    // --- 4. blob extraction: iterative 4-connected flood fill, weighted centroid
    memset(vis_, 0, sizeof(vis_));
    int nb = 0;
    for (int s = 0; s < NCELL && nb < p_.max_blobs; s++) {
      if (vis_[s] || !hot(grid_[s], thr)) continue;
      int sp = 0; stk_[sp++] = (int16_t)s; vis_[s] = 1;
      int area = 0; float sw = 0.f, swx = 0.f, swy = 0.f, pk = -1e9f;
      while (sp) {
        int c = stk_[--sp]; int cy = c / OC, cx = c % OC;
        float w = (p_.centroid_mode == 1) ? 1.f : grid_[c] - thr;
        area++; sw += w; swx += w * cx; swy += w * cy;
        if (grid_[c] - med > pk) pk = grid_[c] - med;                   // peak excess over the frame median (mode 3 gate)
        if (cy > 0)      push(c - OC, thr, sp);
        if (cy < OR - 1) push(c + OC, thr, sp);
        if (cx > 0)      push(c - 1,  thr, sp);
        if (cx < OC - 1) push(c + 1,  thr, sp);
        if (p_.connectivity == 8) {
          if (cy > 0 && cx > 0)           push(c - OC - 1, thr, sp);
          if (cy > 0 && cx < OC - 1)      push(c - OC + 1, thr, sp);
          if (cy < OR - 1 && cx > 0)      push(c + OC - 1, thr, sp);
          if (cy < OR - 1 && cx < OC - 1) push(c + OC + 1, thr, sp);
        }
      }
      if (area >= p_.min_area && sw > 0.f) {
        bx_[nb] = swx / sw / UPSCALE;   // centroid in SOURCE-pixel units
        by_[nb] = swy / sw / UPSCALE;
        ba_[nb] = (float)area; bp_[nb] = pk;
        nb++;
      }
    }
    nBlobs_ = nb;

    // --- 5a. associate blobs with existing tracks
    bool claimed[MAX_BLOBS];
    for (int b = 0; b < MAX_BLOBS; b++) claimed[b] = false;
    const bool manh = (p_.match_metric == 1);
    const float rlim = manh ? p_.match_radius : p_.match_radius * p_.match_radius;
    if (p_.assign_mode == 0) {
      // greedy in track order: each track takes its nearest free blob (v1 and the baselines)
      for (int t = 0; t < p_.max_tracks; t++) {
        Track& T = tr_[t];
        T.matched = false;
        if (!T.active) continue;
        int best = -1; float bd = rlim;
        for (int b = 0; b < nb; b++) {
          if (claimed[b]) continue;
          float dx = bx_[b] - T.lx, dy = by_[b] - T.ly;
          float d = manh ? (fabsf(dx) + fabsf(dy)) : (dx * dx + dy * dy);
          if (d < bd) { bd = d; best = b; }
        }
        if (best >= 0) { claimed[best] = true; T.matched = true; T.missed = 0; pushHist(T, bx_[best], by_[best]); onUpdate(T); blobStats(T, best); }
        else if (++T.missed > p_.max_missed) T.active = false;
      }
    } else {
      // global one-to-one: repeatedly take the closest (track, blob) pair among those still free. Tie -> lowest track, then blob.
      bool done[MAX_TRACKS];
      for (int t = 0; t < MAX_TRACKS; t++) { done[t] = false; tr_[t].matched = false; }
      for (;;) {
        int bt = -1, bb = -1; float bd = rlim;
        for (int t = 0; t < p_.max_tracks; t++) {
          if (!tr_[t].active || done[t]) continue;
          for (int b = 0; b < nb; b++) {
            if (claimed[b]) continue;
            float dx = bx_[b] - tr_[t].lx, dy = by_[b] - tr_[t].ly;
            float d = manh ? (fabsf(dx) + fabsf(dy)) : (dx * dx + dy * dy);
            if (d < bd) { bd = d; bt = t; bb = b; }
          }
        }
        if (bt < 0) break;
        Track& T = tr_[bt]; claimed[bb] = true; done[bt] = true;
        T.matched = true; T.missed = 0; pushHist(T, bx_[bb], by_[bb]); onUpdate(T); blobStats(T, bb);
      }
      for (int t = 0; t < p_.max_tracks; t++) if (tr_[t].active && !tr_[t].matched && ++tr_[t].missed > p_.max_missed) tr_[t].active = false;
    }
    // --- 5b. unmatched blobs start new tracks
    for (int b = 0; b < nb; b++) {
      if (claimed[b]) continue;
      for (int t = 0; t < p_.max_tracks; t++) {
        if (!tr_[t].active) {
          tr_[t] = Track(); tr_[t].active = true; tr_[t].matched = true;
          pushHist(tr_[t], bx_[b], by_[b]);
          tr_[t].fx = bx_[b]; tr_[t].fy = by_[b]; tr_[t].pc = 1;
          tr_[t].ma = ba_[b]; tr_[t].mp = bp_[b];
          tr_[t].lvx = bx_[b]; tr_[t].lvy = by_[b]; tr_[t].lvv = 0.f;
          break;
        }
      }
    }

    // --- 5c. persistence test
    int count = 0, nStat = 0, nTr = 0, nCand = 0;
    if (p_.persistence_mode == 3) {
      // CANDIDATE (Ours-v2): same extent test as mode 0, but with a state machine per track:
      //   NEW        not enough history yet, or still for fewer than persist_frames: not counted (as v1)
      //   DYNAMIC    moving (extent >= drift) or a merged blob: counted. A DYNAMIC track that pauses stays DYNAMIC
      //              (counted) until it has been still for persist_frames: a short pause cannot hide a person.
      //   CANDIDATE  still for persist_frames: counted or suppressed according to cand_policy. Released back to
      //              DYNAMIC only after hyst_frames consecutive moving frames (no flicker on a single noisy centroid).
      for (int t = 0; t < p_.max_tracks; t++) {
        Track& T = tr_[t];
        if (!T.active || !T.matched || T.filled < p_.window) continue;
        float minx = T.hx[0], maxx = T.hx[0], miny = T.hy[0], maxy = T.hy[0];
        for (int i = 1; i < p_.window; i++) {
          if (T.hx[i] < minx) minx = T.hx[i];
          if (T.hx[i] > maxx) maxx = T.hx[i];
          if (T.hy[i] < miny) miny = T.hy[i];
          if (T.hy[i] > maxy) maxy = T.hy[i];
        }
        float rx = maxx - minx, ry = maxy - miny;
        bool moving = sqrtf(rx * rx + ry * ry) >= p_.drift_thresh;
        if (p_.merge_area > 0 && T.ma > (float)p_.merge_area) moving = true;   // merged blob: cannot be one static object
        if (moving) {
          T.still = 0; if (T.dyn < 30000) T.dyn++;
          if (T.st != ST_CAND || T.dyn >= p_.hyst_frames) { T.st = ST_DYN; T.moved = true; }
        } else {
          T.dyn = 0; if (T.still < 30000) T.still++;
          if (T.st != ST_CAND && T.still >= p_.persist_frames) T.st = ST_CAND;
        }
        if (T.st == ST_DYN) count++;
        else if (T.st == ST_CAND) { nCand++; if (candCounts(T)) count++; else nStat++; }
      }
      nTr = count + nStat;
    } else if (p_.persistence_mode == 0) {
      // EXTENT (ours): STATIC if the centroid stayed in a tiny box for N frames
      for (int t = 0; t < p_.max_tracks; t++) {
        Track& T = tr_[t];
        if (!T.active || !T.matched || T.filled < p_.window) continue;   // not enough history yet
        float minx = T.hx[0], maxx = T.hx[0], miny = T.hy[0], maxy = T.hy[0];
        for (int i = 1; i < p_.window; i++) {
          if (T.hx[i] < minx) minx = T.hx[i];
          if (T.hx[i] > maxx) maxx = T.hx[i];
          if (T.hy[i] < miny) miny = T.hy[i];
          if (T.hy[i] > maxy) maxy = T.hy[i];
        }
        float rx = maxx - minx, ry = maxy - miny;
        if (sqrtf(rx * rx + ry * ry) >= p_.drift_thresh) count++;        // keeps drifting => HUMAN
        else nStat++;
      }
      nTr = count + nStat;
    } else {
      // Baseline modes: every live track (even one that missed this frame but is kept) is judged
      // each pass, as in their main loop. New tracks count at once (no history gate).
      for (int t = 0; t < p_.max_tracks; t++) {
        Track& T = tr_[t];
        if (!T.active) continue;
        if (p_.persistence_mode == 1) {
          if (T.stat) {
            if (dist(T.lx, T.ly, T.lockx, T.locky) > p_.reset_thresh) { T.stat = false; T.cnt = 0; }
          } else if (T.filled >= p_.window) {
            // oldest ring entry = the oldest of the last N_window positions (their path[-N_window])
            float d = dist(T.lx, T.ly, T.hx[T.head], T.hy[T.head]);
            if (d < p_.drift_thresh) {
              if (++T.cnt >= p_.n_persist) { T.stat = true; T.lockx = T.lx; T.locky = T.ly; T.cnt = 0; }
            } else T.cnt = 0;
          } else T.cnt = 0;
        } else {                                                           // mode 2, firmware rule
          if (T.stat) {
            if (dist(T.lx, T.ly, T.lockx, T.locky) > p_.reset_thresh) T.stat = false;
          } else if (T.pc >= p_.n_persist) {
            if (dist(T.lx, T.ly, T.fx, T.fy) < p_.drift_thresh) { T.stat = true; T.lockx = T.lx; T.locky = T.ly; }
          }
        }
        nTr++;
        if (T.stat) nStat++;
        else count++;
      }
      if (p_.count_static) count = nTr;                                    // firmware as published
    }
    rawCount_ = count; nStatic_ = nStat; nTracks_ = nTr; nCand_ = nCand;

    // --- 6. majority vote over the last W counts
    sm_[smHead_] = count;
    smHead_ = (smHead_ + 1) % p_.smooth_window;
    if (smFilled_ < p_.smooth_window) smFilled_++;
    int hist[MAX_TRACKS + 1];
    for (int i = 0; i <= MAX_TRACKS; i++) hist[i] = 0;
    for (int i = 0; i < smFilled_; i++) { int v = sm_[i]; if (v > MAX_TRACKS) v = MAX_TRACKS; hist[v]++; }
    int bestV = count > MAX_TRACKS ? MAX_TRACKS : count;
    for (int v = 0; v <= MAX_TRACKS; v++) if (hist[v] > hist[bestV]) bestV = v;  // ties favour current
    return bestV;
  }

 private:
  struct Track {
    bool  active = false, matched = false;
    int   filled = 0, head = 0, missed = 0;
    float lx = 0.f, ly = 0.f;
    float hx[MAX_WINDOW] = {}, hy[MAX_WINDOW] = {};
    // v2 baseline state
    bool  stat = false;
    int   cnt = 0, pc = 0;                 // consecutive-static counter (mode 1); path length (mode 2)
    float lockx = 0.f, locky = 0.f;        // locked centroid
    float fx = 0.f, fy = 0.f;              // birth position (mode 2); reset when crossing the mid row
    // v2 (mode 3) state
    uint8_t st = 0;                        // ST_NEW / ST_DYN / ST_CAND
    int   still = 0, dyn = 0;              // consecutive still / moving frames
    bool  moved = false;                   // origin: this track was seen moving at some point (ARRIVED_MOVING)
    float ma = 0.f, mp = 0.f;              // smoothed blob area (upsampled cells) and peak excess over the median (degC)
    float lvx = 0.f, lvy = 0.f, lvv = 0.f; // Ours-v3: slow mean centroid and exponentially weighted variance of the centroid (source px^2)
  };
  static constexpr int   ST_NEW = 0, ST_DYN = 1, ST_CAND = 2;
  static constexpr float STAT_EMA = 0.2f;  // smoothing of the blob area / peak used by the candidate gates

  void blobStats(Track& T, int b) {
    T.ma += STAT_EMA * (ba_[b] - T.ma); T.mp += STAT_EMA * (bp_[b] - T.mp);
    const float a = 1.f / (float)p_.live_frames, dx = bx_[b] - T.lvx, dy = by_[b] - T.lvy;   // exponentially weighted mean / variance of the centroid
    T.lvv = (1.f - a) * (T.lvv + a * (dx * dx + dy * dy)); T.lvx += a * dx; T.lvy += a * dy;
  }
  // does a stationary candidate count as a person under cand_policy?
  bool candCounts(const Track& T) const {
    const int pol = p_.cand_policy;
    if ((pol & 8) && p_.live_thresh > 0.f && T.lvv >= p_.live_thresh * p_.live_thresh) return true;   // living: slow wander says person
    if (pol & 4) return true;
    if ((pol & 3) == 0) return false;
    if ((pol & 1) && !(T.ma >= (float)p_.cand_min_area && (p_.cand_max_peak <= 0.f || T.mp <= p_.cand_max_peak))) return false;
    if ((pol & 2) && !T.moved) return false;
    return true;
  }

  static float dist(float ax, float ay, float bx, float by) {
    float dx = ax - bx, dy = ay - by; return sqrtf(dx * dx + dy * dy);
  }
  bool hot(float v, float thr) const { return geq_ ? (v >= thr) : (v > thr); }
  // mode 2 bookkeeping on every matched update (their HumanObject.update + crossing reset)
  void onUpdate(Track& T) {
    if (p_.persistence_mode != 2) return;
    if (T.pc < p_.n_persist) T.pc++;
    const float mid = (ROWS - 1) * 0.5f;    // their BOUNDARY = row 35 of 71 = 3.5 source px
    if ((T.fy < mid && T.ly >= mid) || (T.fy >= mid && T.ly < mid)) { T.fx = T.lx; T.fy = T.ly; }
  }

  void push(int n, float thr, int& sp) {
    if (!vis_[n] && hot(grid_[n], thr)) { vis_[n] = 1; stk_[sp++] = (int16_t)n; }
  }
  void pushHist(Track& T, float x, float y) {
    T.hx[T.head] = x; T.hy[T.head] = y;
    T.head = (T.head + 1) % p_.window;
    if (T.filled < p_.window) T.filled++;
    T.lx = x; T.ly = y;
  }

  FilterParams p_;
  // All buffers are fixed-size and static in lifetime: no malloc/new anywhere.
  float   grid_[NCELL];
  uint8_t vis_[NCELL];
  int16_t stk_[NCELL];
  float   bx_[MAX_BLOBS], by_[MAX_BLOBS], ba_[MAX_BLOBS], bp_[MAX_BLOBS];
  Track   tr_[MAX_TRACKS];
  int     sm_[MAX_SMOOTH];
  int     smHead_ = 0, smFilled_ = 0, rawCount_ = 0, nBlobs_ = 0, nStatic_ = 0, nTracks_ = 0, nCand_ = 0;
  bool    geq_ = false;
};
