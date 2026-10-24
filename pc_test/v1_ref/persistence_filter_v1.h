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
constexpr int MAX_TRACKS = 8;
constexpr int MAX_BLOBS  = 8;
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
  }

  void reset() {
    for (int i = 0; i < MAX_TRACKS; i++) tr_[i] = Track();
    for (int i = 0; i < MAX_SMOOTH; i++) sm_[i] = 0;
    smHead_ = 0; smFilled_ = 0; rawCount_ = 0; nBlobs_ = 0;
  }

  int lastRawCount() const { return rawCount_; }   // unsmoothed count of the last frame
  int lastBlobCount() const { return nBlobs_; }    // all hot blobs, static or not

  // raw: ROWS*COLS temperatures in degC, row-major. Returns smoothed human count.
  int process(const float* raw) {
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
    if (p_.robust_stats) {
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
    float floorThr = med + p_.min_contrast;
    if (thr < floorThr) thr = floorThr;

    // --- 4. blob extraction: iterative 4-connected flood fill, weighted centroid
    memset(vis_, 0, sizeof(vis_));
    int nb = 0;
    for (int s = 0; s < NCELL && nb < MAX_BLOBS; s++) {
      if (vis_[s] || grid_[s] <= thr) continue;
      int sp = 0; stk_[sp++] = (int16_t)s; vis_[s] = 1;
      int area = 0; float sw = 0.f, swx = 0.f, swy = 0.f;
      while (sp) {
        int c = stk_[--sp]; int cy = c / OC, cx = c % OC;
        float w = grid_[c] - thr;
        area++; sw += w; swx += w * cx; swy += w * cy;
        if (cy > 0)      push(c - OC, thr, sp);
        if (cy < OR - 1) push(c + OC, thr, sp);
        if (cx > 0)      push(c - 1,  thr, sp);
        if (cx < OC - 1) push(c + 1,  thr, sp);
      }
      if (area >= p_.min_area && sw > 0.f) {
        bx_[nb] = swx / sw / UPSCALE;   // centroid in SOURCE-pixel units
        by_[nb] = swy / sw / UPSCALE;
        nb++;
      }
    }
    nBlobs_ = nb;

    // --- 5a. associate blobs with existing tracks (greedy nearest neighbour)
    bool claimed[MAX_BLOBS];
    for (int b = 0; b < MAX_BLOBS; b++) claimed[b] = false;
    const float r2 = p_.match_radius * p_.match_radius;
    for (int t = 0; t < MAX_TRACKS; t++) {
      Track& T = tr_[t];
      T.matched = false;
      if (!T.active) continue;
      int best = -1; float bd = r2;
      for (int b = 0; b < nb; b++) {
        if (claimed[b]) continue;
        float dx = bx_[b] - T.lx, dy = by_[b] - T.ly, d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = b; }
      }
      if (best >= 0) { claimed[best] = true; T.matched = true; T.missed = 0; pushHist(T, bx_[best], by_[best]); }
      else if (++T.missed > p_.max_missed) T.active = false;
    }
    // --- 5b. unmatched blobs start new tracks
    for (int b = 0; b < nb; b++) {
      if (claimed[b]) continue;
      for (int t = 0; t < MAX_TRACKS; t++) {
        if (!tr_[t].active) {
          tr_[t] = Track(); tr_[t].active = true; tr_[t].matched = true;
          pushHist(tr_[t], bx_[b], by_[b]);
          break;
        }
      }
    }

    // --- 5c. persistence test: STATIC if centroid stayed in a tiny box for N frames
    int count = 0;
    for (int t = 0; t < MAX_TRACKS; t++) {
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
    }
    rawCount_ = count;

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
  };

  void push(int n, float thr, int& sp) {
    if (!vis_[n] && grid_[n] > thr) { vis_[n] = 1; stk_[sp++] = (int16_t)n; }
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
  float   bx_[MAX_BLOBS], by_[MAX_BLOBS];
  Track   tr_[MAX_TRACKS];
  int     sm_[MAX_SMOOTH];
  int     smHead_ = 0, smFilled_ = 0, rawCount_ = 0, nBlobs_ = 0;
};
