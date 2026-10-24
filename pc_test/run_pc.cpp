// run_pc.cpp - run the exact firmware algorithm on a stream CSV, on your laptop.
// Fast way to tune parameters and to get results before touching the ESP32.
//
// Build:  g++ -O2 -std=c++17 -o run_pc.exe run_pc.cpp          (Linux/Mac: -o run_pc)
// Use:    run_pc.exe --stream ..\data\streams\dev_single_clean.csv --fps 3.8 --window_s 4 > results.csv
//
// Stream CSV columns: frame,humans,injected[,dht],p0..p{G*G-1}   (G = 8, 4 or 2, auto-detected;
// the dht column is optional and only needed by the DHT-threshold baseline).
// Output columns:     frame,humans,injected,raw,smooth,us,static
//
// TIME PARAMETERS can be given in FRAMES (--window, --maxmissed, --smooth, --npersist) or SECONDS
// (--window_s, --maxmissed_s, --smooth_s, --npersist_s) together with --fps. Seconds override frames.
//
// BASELINES (Papanashi et al., re-implemented from baseline_spec.md; see that file for sources):
//   --preset bpaper       their main.py rule (persistence_mode 1): DHT+0.1 threshold, Manhattan matching radius
//                         2.5 source px, 8-connectivity, plain-mean centroid, endpoint displacement over N_window
//                         + consecutive counter + lock/reset, no smoothing.
//        --timebase paper   N_persist 10 s,  N_window 1.5 s  (the paper's claim, needs --fps)
//        --timebase loop    N_persist 13 s,  N_window 2 s    (their logged loop rate, needs --fps)
//        --timebase frames  N_persist 100,   N_window 15     (literal counts of unique frames; default)
//   --preset bcode        their ESP32 firmware/README rule (persistence_mode 2), INTENDED behaviour
//                         (static tracks excluded from the people count).
//   --preset bcode_asis   same, but static tracks are still counted, as the published firmware does.
// OURS-V2 (Plan Step 5c; persistence_mode 3, see persistence_filter.h):
//   --pers_mode 3 --assign_mode 1 --persist_s 4 --hyst_s 1 --cand_policy 1 --cand_min_area 500 --cand_max_peak 4
//        --persist_frames/--persist_s   still time before a track becomes a stationary CANDIDATE (default 1 frame)
//        --hyst_frames/--hyst_s         consecutive moving time that releases a candidate (default 1 frame)
//        --cand_policy N                0 never count candidates (v1 rule) | 1 size/warmth gate | 2 origin gate | 4 always (bit mask)
//        --cand_min_area N, --cand_max_peak T   the size/warmth gate (area in upsampled cells; peak excess in degC, 0 = no limit)
//        --assign_mode 1                global one-to-one assignment (any mode)      --merge_area N   merged-blob flag (0 = off)
//   persist/hyst/cand/assign/merge at their defaults with --pers_mode 3 reproduce v1 exactly.
// Explicit flags after --preset override the preset. --dht_offset 0.2 tests the possible double offset (D7).
// ASSUMPTIONS made in the presets (not in the spec): min blob area 1 (step 5b: their scripts filter nothing by size); DHT offset 0.0 as logged; max_missed 1 (bpaper) / 2 (bcode).
#include "../firmware/thermal_poc/persistence_filter.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

template <int G>
static int run(std::istream& in, const FilterParams& p, int labelCols, int dhtCol) {
  PersistenceFilter<G, G> f(p);
  std::string line;
  std::getline(in, line);  // header
  std::printf("frame,humans,injected,raw,smooth,us,static\n");
  float frame[G * G];
  std::vector<std::string> tok;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    tok.clear();
    { std::stringstream ss(line); std::string t; while (std::getline(ss, t, ',')) tok.push_back(t); }
    if ((int)tok.size() < labelCols + G * G) continue;
    long id = std::atol(tok[0].c_str());
    int humans = std::atoi(tok[1].c_str());
    int injected = std::atoi(tok[2].c_str());
    float dht = dhtCol >= 0 ? (float)std::atof(tok[dhtCol].c_str()) : 0.f;
    for (int i = 0; i < G * G; i++) frame[i] = (float)std::atof(tok[labelCols + i].c_str());
    int c = f.process(frame, dht);
    std::printf("%ld,%d,%d,%d,%d,0,%d\n", id, humans, injected, f.lastRawCount(), c, f.lastStaticCount());
  }
  return 0;
}

static void applyPreset(FilterParams& p, const std::string& preset, const std::string& tb, double fps) {
  p.threshold_mode = 1; p.dht_offset = 0.0f; p.min_area = 1;   // step 5b: recorded DHT used as is; neither of their scripts filters blobs by size
  p.centroid_mode = 1; p.match_metric = 1; p.match_radius = 2.5f;        // 25 cells Manhattan = 2.5 source px
  p.reset_thresh = 0.2f;                                                // 2.0 cells
  p.max_tracks = 10; p.max_blobs = 16; p.smooth_window = 1;
  if (preset == "bpaper") {
    p.persistence_mode = 1; p.connectivity = 8; p.drift_thresh = 0.05f; p.count_static = 0; p.max_missed = 1;
    if (tb == "frames")      { p.n_persist = 100; p.window = 15; }
    else if (tb == "paper")  { p.n_persist = secondsToFrames(10.0, fps); p.window = secondsToFrames(1.5, fps); }
    else if (tb == "loop")   { p.n_persist = secondsToFrames(13.0, fps); p.window = secondsToFrames(2.0, fps); }
  } else {                                                              // bcode / bcode_asis
    p.persistence_mode = 2; p.connectivity = 4; p.drift_thresh = 0.08f; p.n_persist = 20; p.max_missed = 2;
    p.count_static = (preset == "bcode_asis") ? 1 : 0;
  }
}

int main(int argc, char** argv) {
  FilterParams p;
  std::string path, preset, timebase = "frames";
  double fps = 0, window_s = -1, maxmissed_s = -1, smooth_s = -1, npersist_s = -1, persist_s = -1, hyst_s = -1, live_s = -1;
  bool printP = false;
  // pass 1: preset / timebase / fps (so explicit flags can override the preset in pass 2)
  for (int i = 1; i + 1 < argc; i += 2) {
    std::string a = argv[i];
    if (a == "--preset") preset = argv[i + 1];
    else if (a == "--timebase") timebase = argv[i + 1];
    else if (a == "--fps") fps = atof(argv[i + 1]);
  }
  if (!preset.empty()) {
    if (preset != "bpaper" && preset != "bcode" && preset != "bcode_asis") { std::fprintf(stderr, "unknown preset %s\n", preset.c_str()); return 1; }
    if (timebase != "frames" && timebase != "paper" && timebase != "loop") { std::fprintf(stderr, "unknown timebase %s\n", timebase.c_str()); return 1; }
    if (preset == "bpaper" && timebase != "frames" && fps <= 0) { std::fprintf(stderr, "--timebase %s needs --fps\n", timebase.c_str()); return 1; }
    applyPreset(p, preset, timebase, fps);
  }
  for (int i = 1; i + 1 < argc; i += 2) {
    std::string a = argv[i]; const char* v = argv[i + 1];
    if      (a == "--stream")    path = v;
    else if (a == "--preset" || a == "--timebase" || a == "--fps") {}
    else if (a == "--print_pline") printP = true;       // value ignored (write 1)
    else if (a == "--k")         p.k_sigma = (float)atof(v);
    else if (a == "--robust")    p.robust_stats = atoi(v);
    else if (a == "--contrast")  p.min_contrast = (float)atof(v);
    else if (a == "--minarea")   p.min_area = atoi(v);
    else if (a == "--match")     p.match_radius = (float)atof(v);
    else if (a == "--window")    p.window = atoi(v);
    else if (a == "--drift")     p.drift_thresh = (float)atof(v);
    else if (a == "--maxmissed") p.max_missed = atoi(v);
    else if (a == "--smooth")    p.smooth_window = atoi(v);
    else if (a == "--thr_mode")  p.threshold_mode = atoi(v);
    else if (a == "--pers_mode") p.persistence_mode = atoi(v);
    else if (a == "--dht_offset") p.dht_offset = (float)atof(v);
    else if (a == "--npersist")  p.n_persist = atoi(v);
    else if (a == "--reset")     p.reset_thresh = (float)atof(v);
    else if (a == "--centroid")  p.centroid_mode = atoi(v);
    else if (a == "--metric")    p.match_metric = atoi(v);
    else if (a == "--conn")      p.connectivity = atoi(v);
    else if (a == "--count_static") p.count_static = atoi(v);
    else if (a == "--maxtracks") p.max_tracks = atoi(v);
    else if (a == "--maxblobs")  p.max_blobs = atoi(v);
    else if (a == "--persist_frames") p.persist_frames = atoi(v);
    else if (a == "--hyst_frames")    p.hyst_frames = atoi(v);
    else if (a == "--cand_policy")    p.cand_policy = atoi(v);
    else if (a == "--cand_min_area")  p.cand_min_area = atoi(v);
    else if (a == "--cand_max_peak")  p.cand_max_peak = (float)atof(v);
    else if (a == "--assign_mode")    p.assign_mode = atoi(v);
    else if (a == "--merge_area")     p.merge_area = atoi(v);
    else if (a == "--live_frames")    p.live_frames = atoi(v);
    else if (a == "--live_s")         live_s = atof(v);
    else if (a == "--live_thresh")    p.live_thresh = (float)atof(v);
    else if (a == "--persist_s")      persist_s = atof(v);
    else if (a == "--hyst_s")         hyst_s = atof(v);
    else if (a == "--window_s")    window_s = atof(v);
    else if (a == "--maxmissed_s") maxmissed_s = atof(v);
    else if (a == "--smooth_s")    smooth_s = atof(v);
    else if (a == "--npersist_s")  npersist_s = atof(v);
    else { std::fprintf(stderr, "unknown arg %s\n", a.c_str()); return 1; }
  }
  if (window_s >= 0 || maxmissed_s >= 0 || smooth_s >= 0 || npersist_s >= 0 || persist_s >= 0 || hyst_s >= 0 || live_s >= 0) {
    if (fps <= 0) { std::fprintf(stderr, "seconds-based flags need --fps\n"); return 1; }
    if (window_s    >= 0) p.window        = secondsToFrames(window_s, fps);
    if (maxmissed_s >= 0) p.max_missed    = secondsToFrames(maxmissed_s, fps);
    if (smooth_s    >= 0) p.smooth_window = secondsToFrames(smooth_s, fps);
    if (npersist_s  >= 0) p.n_persist     = secondsToFrames(npersist_s, fps);
    if (persist_s   >= 0) p.persist_frames = secondsToFrames(persist_s, fps);
    if (hyst_s      >= 0) p.hyst_frames    = secondsToFrames(hyst_s, fps);
    if (live_s      >= 0) p.live_frames    = secondsToFrames(live_s, fps);
  }
  if (p.window > MAX_WINDOW)        { std::fprintf(stderr, "WARNING: window %d frames > MAX_WINDOW %d, clamped\n", p.window, MAX_WINDOW); }
  if (p.smooth_window > MAX_SMOOTH) { std::fprintf(stderr, "WARNING: smooth %d frames > MAX_SMOOTH %d, clamped\n", p.smooth_window, MAX_SMOOTH); }
  if (printP) {   // the exact parameter line the ESP32 firmware expects (frames, fully resolved) - then exit
    std::printf("P,%.6g,%.6g,%d,%.6g,%d,%.6g,%d,%d,%d,%d,%d,%.6g,%d,%.6g,%d,%d,%d,%d,%d,%d",
                p.k_sigma, p.min_contrast, p.min_area, p.match_radius, p.window, p.drift_thresh, p.max_missed, p.smooth_window,
                p.robust_stats, p.threshold_mode, p.persistence_mode, p.dht_offset, p.n_persist, p.reset_thresh,
                p.centroid_mode, p.match_metric, p.connectivity, p.count_static, p.max_tracks, p.max_blobs);
    if (p.persistence_mode == 3 || p.assign_mode != 0)   // Ours-v2 fields (sketch step5c or later); omitted otherwise so the older sketch still matches
      std::printf(",%d,%d,%d,%d,%.6g,%d,%d", p.persist_frames, p.hyst_frames, p.cand_policy, p.cand_min_area, p.cand_max_peak, p.assign_mode, p.merge_area);
    if (p.live_thresh > 0.f || p.live_frames != 1 || (p.cand_policy & 8))   // Ours-v3 fields (sketch step 5d or later); omitted otherwise
      std::printf(",%d,%.6g", p.live_frames, p.live_thresh);
    std::printf("\n");
    return 0;
  }
  std::fprintf(stderr, "params: window=%d maxmissed=%d smooth=%d frames | k=%.2f contrast=%.2f drift=%.3f minarea=%d match=%.2f robust=%d%s\n",
               p.window, p.max_missed, p.smooth_window, p.k_sigma, p.min_contrast, p.drift_thresh, p.min_area, p.match_radius, p.robust_stats,
               fps > 0 ? " (fps given)" : "");
  if (p.threshold_mode == 1 || p.persistence_mode != 0 || !preset.empty())
    std::fprintf(stderr, "baseline: preset=%s thr_mode=%d pers_mode=%d dht_offset=%.2f n_persist=%d reset=%.2f centroid=%d metric=%d conn=%d count_static=%d tracks=%d blobs=%d\n",
                 preset.empty() ? "none" : preset.c_str(), p.threshold_mode, p.persistence_mode, p.dht_offset, p.n_persist, p.reset_thresh,
                 p.centroid_mode, p.match_metric, p.connectivity, p.count_static, p.max_tracks, p.max_blobs);
  if (p.persistence_mode == 3 || p.assign_mode != 0)
    std::fprintf(stderr, "ours-v2: pers_mode=%d persist=%d hyst=%d policy=%d min_area=%d max_peak=%.2f assign=%d merge_area=%d (frames)\n",
                 p.persistence_mode, p.persist_frames, p.hyst_frames, p.cand_policy, p.cand_min_area, p.cand_max_peak, p.assign_mode, p.merge_area);
  if (path.empty()) { std::fprintf(stderr, "need --stream file.csv\n"); return 1; }
  std::ifstream in(path);
  if (!in) { std::fprintf(stderr, "cannot open %s\n", path.c_str()); return 1; }

  // header: leading label columns (frame,humans,injected[,dht]) then p0..p{N-1}
  std::string header; std::getline(in, header);
  std::vector<std::string> names; { std::stringstream ss(header); std::string t; while (std::getline(ss, t, ',')) names.push_back(t); }
  int labelCols = 0, dhtCol = -1;
  while (labelCols < (int)names.size() && !(names[labelCols].size() > 1 && names[labelCols][0] == 'p' && isdigit((unsigned char)names[labelCols][1]))) {
    if (names[labelCols] == "dht") dhtCol = labelCols;
    labelCols++;
  }
  int npix = (int)names.size() - labelCols;
  if (p.threshold_mode == 1 && dhtCol < 0) { std::fprintf(stderr, "threshold_mode 1 (DHT) needs a 'dht' column in the stream: rebuild streams with the v2 make_stream.py\n"); return 1; }
  in.clear(); in.seekg(0);
  if (npix == 64) return run<8>(in, p, labelCols, dhtCol);
  if (npix == 16) return run<4>(in, p, labelCols, dhtCol);
  if (npix == 4)  return run<2>(in, p, labelCols, dhtCol);
  std::fprintf(stderr, "unsupported pixel count %d (expected 64, 16 or 4)\n", npix);
  return 1;
}
