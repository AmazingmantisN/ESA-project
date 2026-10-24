// test_modes.cpp - unit tests for the v2 persistence/threshold modes (plan Step 5).
// Build + run:  g++ -O2 -std=c++17 -o test_modes test_modes.cpp && ./test_modes       (Windows: test_modes.exe)
// Every scenario is synthetic and deterministic (fixed seed). Exit code 0 = all passed.
// These tests check that each rule does what baseline_spec.md says it does; they do not claim anything
// about real data. "DEMO" tests show a property of a rule rather than assert a pass/fail design goal.
#include "../firmware/thermal_poc/persistence_filter.h"
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <vector>

static int g_fail = 0, g_n = 0;
static void check(const char* name, bool ok, const char* detail = "") {
  g_n++; if (!ok) g_fail++;
  std::printf("[%s] %s %s\n", ok ? "PASS" : "FAIL", name, detail);
}

struct Rng {  // xorshift64* + Box-Muller, deterministic
  uint64_t s; explicit Rng(uint64_t seed) : s(seed ? seed : 88172645463325252ULL) {}
  double u() { s ^= s >> 12; s ^= s << 25; s ^= s >> 27; return ((s * 2685821657736338717ULL) >> 11) * (1.0 / 9007199254740992.0) + 1e-12; }
  double n() { return std::sqrt(-2.0 * std::log(u())) * std::cos(6.283185307179586 * u()); }
};

static const float AMB = 26.5f, DHT = AMB + 0.4f;   // DHT + 0.1 = AMB + 0.5 degC threshold in baseline modes

struct Blob { double cx, cy, amp, sigma; };
static void makeFrame(float* f, const std::vector<Blob>& bl, Rng& r, double noise) {
  for (int y = 0; y < 8; y++) for (int x = 0; x < 8; x++) {
    double v = AMB;
    for (auto& b : bl) v += b.amp * std::exp(-((x - b.cx) * (x - b.cx) + (y - b.cy) * (y - b.cy)) / (2 * b.sigma * b.sigma));
    if (noise > 0) v += noise * r.n();
    f[y * 8 + x] = (float)v;
  }
}

static FilterParams bpaper(int window, int npersist, float drift) {
  FilterParams p; p.threshold_mode = 1; p.persistence_mode = 1; p.centroid_mode = 1; p.match_metric = 1; p.match_radius = 2.5f;
  p.connectivity = 8; p.smooth_window = 1; p.max_missed = 1; p.max_tracks = 10; p.max_blobs = 16;
  p.window = window; p.n_persist = npersist; p.drift_thresh = drift; p.reset_thresh = 0.2f; return p;
}
static FilterParams bcode(int npersist, float drift, int countStatic) {
  FilterParams p; p.threshold_mode = 1; p.persistence_mode = 2; p.centroid_mode = 1; p.match_metric = 1; p.match_radius = 2.5f;
  p.connectivity = 4; p.smooth_window = 1; p.max_missed = 2; p.max_tracks = 10; p.max_blobs = 16;
  p.n_persist = npersist; p.drift_thresh = drift; p.reset_thresh = 0.2f; p.count_static = countStatic; return p;
}
static FilterParams ours(int window, float drift) {
  FilterParams p; p.min_contrast = 1.0f; p.k_sigma = 1.0f; p.window = window; p.drift_thresh = drift; p.smooth_window = 1; return p;
}

struct Trace { std::vector<int> raw, stat; };
// run nFrames of a scenario; pos(n) gives the blob list for frame n (1-based n)
static Trace run(const FilterParams& p, int nFrames, const std::function<std::vector<Blob>(int)>& pos, double noise = 0.0, uint64_t seed = 1) {
  PersistenceFilter<8, 8> f(p); Rng r(seed); Trace t; float fr[64];
  for (int n = 1; n <= nFrames; n++) { makeFrame(fr, pos(n), r, noise); f.process(fr, DHT); t.raw.push_back(f.lastRawCount()); t.stat.push_back(f.lastStaticCount()); }
  return t;
}
static int firstStatic(const Trace& t) { for (size_t i = 0; i < t.stat.size(); i++) if (t.stat[i] > 0) return (int)i + 1; return -1; }
static bool allEq(const Trace& t, int from, int to, int v) { for (int i = from - 1; i < to; i++) if (t.raw[i] != v) return false; return true; }

int main() {
  char buf[200];
  auto still = [](int) { return std::vector<Blob>{{3.2, 3.6, 6.0, 1.0}}; };

  // T1 - B-paper: a perfectly still blob becomes static exactly at update window + n_persist - 1
  { int W = 6, N = 20; auto t = run(bpaper(W, N, 0.05f), 60, still);
    int fs = firstStatic(t); std::snprintf(buf, sizeof buf, "(locked at frame %d, expected %d)", fs, W + N - 1);
    check("T1 B-paper locks a still blob after window+n_persist-1 frames", fs == W + N - 1, buf);
    check("T1 count is 1 until it locks, 0 after", allEq(t, 1, fs - 1, 1) && allEq(t, fs, 60, 0)); }

  // T2 - a blob moving steadily (never returns) is never called static by any rule
  { auto line = [](int n) { return std::vector<Blob>{{1.0 + 0.04 * n, 3.5, 6.0, 1.0}}; };   // 0.04 px/frame, 4.8 px in 120 frames
    auto a = run(ours(8, 0.2f), 120, line), b = run(bpaper(6, 20, 0.05f), 120, line), c = run(bcode(20, 0.08f, 0), 120, line);
    check("T2 ours: moving blob stays human", firstStatic(a) < 0 && allEq(a, 9, 120, 1));
    check("T2 B-paper: moving blob stays human", firstStatic(b) < 0 && allEq(b, 1, 120, 1));
    check("T2 B-code: moving blob stays human", firstStatic(c) < 0 && allEq(c, 1, 120, 1)); }

  // T3 - back-and-forth motion whose period equals the window: endpoint displacement is ~0, extent is large
  { int W = 6; auto osc = [W](int n) { return std::vector<Blob>{{3.5 + 0.6 * std::sin(6.283185307 * n / (W - 1)), 3.5, 6.0, 1.0}}; };
    auto b = run(bpaper(W, 20, 0.05f), 80, osc), a = run(ours(W, 0.3f), 80, osc);
    int fs = firstStatic(b); std::snprintf(buf, sizeof buf, "(B-paper locked at frame %d)", fs);
    check("T3 B-paper wrongly locks an oscillating (living) blob as static", fs > 0 && fs <= 40, buf);
    check("T3 ours (extent) keeps the same blob human", firstStatic(a) < 0 && allEq(a, W, 80, 1)); }

  // T4 - DEMO: a static blob under sensor noise. The endpoint distance of a noisy centroid is about half the pixel
  // noise (degC) in pixels, so a very tight Delta_static is rarely satisfied for n_persist frames in a row.
  { double noise = 0.15; auto still6 = [](int) { return std::vector<Blob>{{3.2, 3.6, 6.0, 1.0}}; };
    auto tight = run(bpaper(6, 20, 0.05f), 400, still6, noise, 5);
    auto loose = run(bpaper(6, 20, 0.30f), 400, still6, noise, 5);
    auto ext   = run(ours(6, 0.40f), 400, still6, noise, 5);
    std::snprintf(buf, sizeof buf, "(B-paper 0.05 px: first static %d | B-paper 0.30 px: %d | ours extent 0.40 px: %d)", firstStatic(tight), firstStatic(loose), firstStatic(ext));
    check("T4 DEMO noise 0.15 degC, Delta_static 0.05 px: counter keeps resetting, blob never locks in 400 frames", firstStatic(tight) < 0, buf);
    check("T4 DEMO same blob, Delta_static 0.30 px: B-paper locks it (frame 25 = window + n_persist - 1)", firstStatic(loose) == 25);
    check("T4 DEMO same blob, ours with extent threshold 0.40 px: static as soon as the window is full", firstStatic(ext) == 6); }

  // T5 - DHT threshold: all-hot when DHT is far below the room, nothing hot when far above, and >= semantics
  { Rng r(1); float fr[64]; auto cnt = [&](float dht, float level, float off) {
      FilterParams p = bpaper(6, 20, 0.05f); p.dht_offset = off; PersistenceFilter<8, 8> f(p);
      for (int i = 0; i < 64; i++) fr[i] = level;
      f.process(fr, dht);
      return f.lastBlobCount(); };
    check("T5 DHT far below the room: whole frame is one blob", cnt(10.f, 26.5f, 0.1f) == 1);
    check("T5 DHT above every pixel: no blob", cnt(40.f, 26.5f, 0.1f) == 0);
    check("T5 mask is >= (pixel exactly at DHT+offset counts)", cnt(26.0f, 26.5f, 0.5f) == 1);
    check("T5 just below the threshold: no blob", cnt(26.0f, 26.49f, 0.5f) == 0);
    check("T5 dht_offset 0.2 flips a case that +0.1 accepts", cnt(26.4f, 26.6f, 0.1f) == 1 && cnt(26.4f, 26.6f, 0.3f) == 0); }

  // T6 - firmware as published (count_static=1) keeps counting static tracks; intended behaviour drops them
  { auto asis = run(bcode(20, 0.08f, 1), 60, still), intended = run(bcode(20, 0.08f, 0), 60, still);
    int fs = firstStatic(intended); std::snprintf(buf, sizeof buf, "(B-code locked at frame %d, expected 20)", fs);
    check("T6 B-code locks a still blob when the path reaches n_persist", fs == 20, buf);
    check("T6 intended: count drops to 0 once static", allEq(intended, 21, 60, 0));
    check("T6 as published: static track still counted, static count still reported", allEq(asis, 1, 60, 1) && asis.stat[59] == 1); }

  // T7 - B-code compares with the BIRTH position: a blob that walks away and returns is flagged
  { auto tri = [](int n) { double x = (n <= 15) ? 1.0 + 0.2 * n : 1.0 + 0.2 * (30 - n); if (n > 30) x = 1.0; return std::vector<Blob>{{x, 3.5, 6.0, 1.0}}; };
    auto b = run(bcode(20, 0.08f, 0), 31, tri), a = run(ours(10, 0.3f), 31, tri);
    std::snprintf(buf, sizeof buf, "(B-code first static at frame %d)", firstStatic(b));
    check("T7 B-code flags a moving blob as static when it returns to its start", firstStatic(b) >= 29 && firstStatic(b) <= 31, buf);
    check("T7 ours does not (extent over the last N frames is large)", firstStatic(a) < 0); }

  // T8 - lock / reset: after locking, a move of more than reset_thresh un-locks the track
  { auto step = [](int n) { return std::vector<Blob>{{n <= 40 ? 3.0 : 3.5, 3.6, 6.0, 1.0}}; };
    auto b = run(bpaper(6, 20, 0.05f), 45, step);
    check("T8 locked (count 0) at frame 40", b.raw[39] == 0 && b.stat[39] == 1);
    check("T8 moving 0.5 px (> reset 0.2) un-locks at frame 41: counted again", b.raw[40] == 1 && b.stat[40] == 0); }

  // T9 - 8-connectivity never gives more blobs than 4-connectivity, and merges some random frames
  { Rng r(3); float fr[64]; int fewer = 0, more = 0, N = 400;
    for (int n = 0; n < N; n++) {
      for (int i = 0; i < 64; i++) fr[i] = 26.0f + (float)(1.5 * r.u());
      FilterParams p4 = bpaper(6, 20, 0.05f), p8 = p4; p4.connectivity = 4; p8.connectivity = 8; p4.min_area = p8.min_area = 1;
      PersistenceFilter<8, 8> f4(p4), f8(p8); f4.process(fr, 26.0f + 0.9f); f8.process(fr, 26.0f + 0.9f);
      if (f8.lastBlobCount() < f4.lastBlobCount()) fewer++;
      if (f8.lastBlobCount() > f4.lastBlobCount()) more++;
    }
    std::snprintf(buf, sizeof buf, "(8-conn fewer in %d frames, more in %d)", fewer, more);
    check("T9 8-connectivity merges some frames and never splits more", more == 0 && fewer > 0, buf); }

  // T10 - defaults are the v1 filter: threshold_mode 0, persistence_mode 0, count_static 0
  { FilterParams p; check("T10 default params select v1 behaviour", p.threshold_mode == 0 && p.persistence_mode == 0 && p.count_static == 0 && p.max_tracks == 8 && p.max_blobs == 8 && p.connectivity == 4 && p.centroid_mode == 0 && p.match_metric == 0); }

  // ---- Ours-v2 (persistence_mode 3, Step 5c) ----------------------------------------------------------------
  auto v2 = [](int window, float drift, int persist, int hyst, int policy) {
    FilterParams p = ours(window, drift); p.persistence_mode = 3; p.persist_frames = persist; p.hyst_frames = hyst; p.cand_policy = policy; return p; };
  // walk for 40 frames at 0.08 px/frame (extent over a 6-frame window 0.4 px > drift 0.3), stand still for 60, walk on
  auto pause = [](int n) { double x = n <= 40 ? 0.5 + 0.08 * n : (n <= 100 ? 0.5 + 0.08 * 40 : 0.5 + 0.08 * 40 + 0.08 * (n - 100)); return std::vector<Blob>{{x, 3.5, 6.0, 1.0}}; };
  auto fromStill = [](int) { return std::vector<Blob>{{3.2, 3.6, 6.0, 1.0}}; };   // appears and never moves
  auto sumRaw = [](const Trace& t, int a, int b) { int s = 0; for (int i = a - 1; i < b; i++) s += t.raw[i]; return s; };

  // T11 - nested equivalence: mode 3 with persist 1, hyst 1, policy 0, merge 0 is EXACTLY mode 0 (several scenarios, noise)
  { bool same = true; Rng sr(9);
    std::vector<std::function<std::vector<Blob>(int)>> sc = {still, pause,
      [](int n) { return std::vector<Blob>{{1.0 + 0.04 * n, 3.5, 6.0, 1.0}}; },
      [](int n) { return std::vector<Blob>{{3.5 + 0.6 * std::sin(6.283185307 * n / 5.0), 3.5, 6.0, 1.0}}; },
      [](int n) { return std::vector<Blob>{{2.0 + 0.03 * n, 2.5, 5.0, 1.0}, {5.5, 5.5, 4.0, 0.8}}; }};
    for (size_t i = 0; i < sc.size(); i++) for (double noise : {0.0, 0.2}) for (float dr : {0.15f, 0.4f}) {
      auto a = run(ours(6, dr), 150, sc[i], noise, 7 + i), b = run(v2(6, dr, 1, 1, 0), 150, sc[i], noise, 7 + i);
      if (a.raw != b.raw || a.stat != b.stat) same = false; }
    (void)sr; check("T11 mode 3 with default sub-parameters == mode 0 (raw and static, 5 scenarios x noise x drift)", same); }

  // T12 - a person who pauses: v1 drops them while still; policy 4 (count candidates) keeps them
  { auto v1 = run(ours(6, 0.3f), 140, pause), c4 = run(v2(6, 0.3f, 1, 1, 4), 140, pause);
    std::snprintf(buf, sizeof buf, "(v1 counted %d of 60 still frames, policy 4 counted %d)", sumRaw(v1, 60, 99), sumRaw(c4, 60, 99));
    check("T12 v1 loses the paused person (count 0 while still)", sumRaw(v1, 60, 99) == 0, buf);
    check("T12 policy 4 keeps counting the paused person and resumes counting when they walk", sumRaw(c4, 60, 99) == 40 && c4.raw[139] == 1); }

  // T13 - origin gate (policy 2): a blob that WAS moving and stopped counts; one that appeared still does not
  { auto moved = run(v2(6, 0.3f, 1, 1, 2), 140, pause), appeared = run(v2(6, 0.3f, 1, 1, 2), 140, fromStill);
    check("T13 policy 2: moved-then-stopped blob stays counted", sumRaw(moved, 60, 99) == 40);
    check("T13 policy 2: blob that appeared still is never counted (laptop-like)", sumRaw(appeared, 1, 140) == 0); }

  // T14 - persist grace: a paused DYN track stays counted for persist_frames of stillness before becoming a candidate
  { auto g1 = run(v2(6, 0.3f, 1, 1, 0), 140, pause), g12 = run(v2(6, 0.3f, 12, 1, 0), 140, pause);
    int d1 = 0, d12 = 0; for (int i = 40; i < 140; i++) { if (!d1 && g1.raw[i] == 0) d1 = i + 1; if (!d12 && g12.raw[i] == 0) d12 = i + 1; }
    std::snprintf(buf, sizeof buf, "(count hits 0 at frame %d with persist 1, %d with persist 12)", d1, d12);
    check("T14 persist_frames=12 delays the drop by 11 frames", d1 > 0 && d12 == d1 + 11, buf); }

  // T15 - hysteresis: one sudden hop makes the track 'moving' for about a window; hyst longer than that ignores it
  { auto hop = [](int n) { return std::vector<Blob>{{n <= 50 ? 3.0 : 3.8, 3.6, 6.0, 1.0}}; };
    auto h1 = run(v2(6, 0.3f, 1, 1, 0), 120, hop), h20 = run(v2(6, 0.3f, 1, 20, 0), 120, hop);
    check("T15 hyst 1: the hop re-releases the candidate to counted for a while", sumRaw(h1, 51, 70) > 0);
    check("T15 hyst 20: the same hop is ignored, candidate stays suppressed", sumRaw(h20, 51, 120) == 0); }

  // T16 - size gate (policy 1): a big blob counts as a candidate, a small one does not
  { auto big = [](int) { return std::vector<Blob>{{3.2, 3.6, 6.0, 1.6}}; }; auto small = [](int) { return std::vector<Blob>{{3.2, 3.6, 3.0, 0.5}}; };
    FilterParams p = v2(6, 0.3f, 1, 1, 1); p.cand_min_area = 1500;
    auto b = run(p, 80, big), s = run(p, 80, small);
    std::snprintf(buf, sizeof buf, "(big counted %d, small counted %d of 74 frames)", sumRaw(b, 7, 80), sumRaw(s, 7, 80));
    check("T16 policy 1 min area: big still blob counted, small one not", sumRaw(b, 7, 80) == 74 && sumRaw(s, 7, 80) == 0, buf); }

  // T17 - global assignment: two blobs swapping sides keep one-to-one matches (no track used twice)
  { auto cross = [](int n) { double d = 0.05 * n; return std::vector<Blob>{{1.5 + d, 3.5, 6.0, 0.9}, {5.5 - d, 3.5, 6.0, 0.9}}; };
    FilterParams p = v2(6, 0.2f, 1, 1, 0); p.assign_mode = 1; p.match_radius = 2.5f; auto t = run(p, 60, cross);
    bool ok = true; for (int i = 6; i < 60; i++) if (t.raw[i] > 2) ok = false;
    check("T17 assign_mode 1 never counts more tracks than blobs on crossing blobs", ok); }

  // T18 - merge_area: an oversize blob (people merged) is forced to count even when still
  { auto fat = [](int) { return std::vector<Blob>{{3.5, 3.5, 6.0, 2.2}}; };
    FilterParams p = v2(6, 0.3f, 1, 1, 0); auto off = run(p, 60, fat); p.merge_area = 500; auto on = run(p, 60, fat);
    check("T18 merge_area keeps an oversize still blob counted; without it the blob is a suppressed candidate", sumRaw(off, 10, 60) == 0 && sumRaw(on, 10, 60) == 51); }

  // T19 - liveness (Ours-v3, cand_policy bit 8): a still-but-slowly-wandering blob counts, a perfectly still one never does
  { auto wander = [](int n) { return std::vector<Blob>{{3.2 + 0.7 * std::sin(6.283185307179586 * n / 80.0), 3.6, 6.0, 1.0}}; };
    auto stillb = [](int) { return std::vector<Blob>{{3.2, 3.6, 6.0, 1.0}}; };
    FilterParams p8 = v2(6, 0.5f, 1, 1, 8); p8.live_frames = 20; p8.live_thresh = 0.25f;
    auto w = run(p8, 140, wander), st = run(p8, 140, stillb);
    FilterParams p2 = v2(6, 0.5f, 1, 1, 2); auto o = run(p2, 140, wander);
    FilterParams p10 = v2(6, 0.5f, 1, 1, 10); p10.live_frames = 20; p10.live_thresh = 0.25f; auto b = run(p10, 140, wander);
    std::snprintf(buf, sizeof buf, "(wanderer counted %d of 61 late frames, still blob %d; origin gate alone %d; policy 10 %d)", sumRaw(w, 80, 140), sumRaw(st, 1, 140), sumRaw(o, 80, 140), sumRaw(b, 80, 140));
    check("T19 policy 8: wandering blob counted once the slow estimate rises, still blob never", sumRaw(w, 80, 140) == 61 && sumRaw(st, 1, 140) == 0, buf);
    check("T19 the same wanderer is invisible to the origin gate alone; policy 10 (liveness OR origin) counts it", sumRaw(o, 80, 140) == 0 && sumRaw(b, 80, 140) == 61); }

  // T20 - liveness off by default: live_thresh 0 with bit 8 set behaves like policy 0 (nothing counts)
  { auto wander = [](int n) { return std::vector<Blob>{{3.2 + 0.7 * std::sin(6.283185307179586 * n / 80.0), 3.6, 6.0, 1.0}}; };
    FilterParams p = v2(6, 0.5f, 1, 1, 8); auto t = run(p, 140, wander); FilterParams z = v2(6, 0.5f, 1, 1, 0); auto zz = run(z, 140, wander);
    bool same = true; for (size_t i = 0; i < t.raw.size(); i++) if (t.raw[i] != zz.raw[i]) same = false;
    check("T20 bit 8 with live_thresh 0 == policy 0", same); }

  std::printf("\n%d tests, %d failed\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
