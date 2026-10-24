// run_pc.cpp - run the exact firmware algorithm on a stream CSV, on your laptop.
// Fast way to tune parameters and to get results before touching the ESP32.
//
// Build:  g++ -O2 -std=c++17 -o run_pc run_pc.cpp
// Use:    ./run_pc --stream ../data/stream_8x8.csv [--window 30 --drift 0.08 ...] > results.csv
//
// Time parameters can be given in FRAMES (--window, --maxmissed, --smooth) or in SECONDS
// (--window_s, --maxmissed_s, --smooth_s) together with --fps. Seconds override frames.
//   ./run_pc --stream s.csv --fps 3.8 --window_s 3 --maxmissed_s 2.5 --smooth_s 1.3
// The frame values actually used are printed to stderr (so results.csv stays clean).
//
// Stream CSV columns: frame,humans,injected,p0..p{G*G-1}   (G = 8, 4 or 2, auto-detected)
#include "persistence_filter_v1.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

template <int G>
static int run(std::istream& in, const FilterParams& p) {
  PersistenceFilter<G, G> f(p);
  std::string line;
  std::getline(in, line);  // header
  std::printf("frame,humans,injected,raw,smooth,us\n");
  float frame[G * G];
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    std::stringstream ss(line);
    std::string tok;
    std::getline(ss, tok, ','); long id = std::atol(tok.c_str());
    std::getline(ss, tok, ','); int humans = std::atoi(tok.c_str());
    std::getline(ss, tok, ','); int injected = std::atoi(tok.c_str());
    for (int i = 0; i < G * G; i++) { std::getline(ss, tok, ','); frame[i] = (float)std::atof(tok.c_str()); }
    int c = f.process(frame);
    std::printf("%ld,%d,%d,%d,%d,0\n", id, humans, injected, f.lastRawCount(), c);
  }
  return 0;
}

int main(int argc, char** argv) {
  FilterParams p;
  std::string path;
  double fps = 0, window_s = -1, maxmissed_s = -1, smooth_s = -1;
  for (int i = 1; i + 1 < argc; i += 2) {
    std::string a = argv[i]; const char* v = argv[i + 1];
    if      (a == "--stream")    path = v;
    else if (a == "--k")         p.k_sigma = (float)atof(v);
    else if (a == "--robust")    p.robust_stats = atoi(v);
    else if (a == "--contrast")  p.min_contrast = (float)atof(v);
    else if (a == "--minarea")   p.min_area = atoi(v);
    else if (a == "--match")     p.match_radius = (float)atof(v);
    else if (a == "--window")    p.window = atoi(v);
    else if (a == "--drift")     p.drift_thresh = (float)atof(v);
    else if (a == "--maxmissed") p.max_missed = atoi(v);
    else if (a == "--smooth")    p.smooth_window = atoi(v);
    else if (a == "--fps")         fps = atof(v);
    else if (a == "--window_s")    window_s = atof(v);
    else if (a == "--maxmissed_s") maxmissed_s = atof(v);
    else if (a == "--smooth_s")    smooth_s = atof(v);
    else { std::fprintf(stderr, "unknown arg %s\n", a.c_str()); return 1; }
  }
  if (window_s >= 0 || maxmissed_s >= 0 || smooth_s >= 0) {
    if (fps <= 0) { std::fprintf(stderr, "seconds-based flags need --fps\n"); return 1; }
    if (window_s    >= 0) p.window        = secondsToFrames(window_s, fps);
    if (maxmissed_s >= 0) p.max_missed    = secondsToFrames(maxmissed_s, fps);
    if (smooth_s    >= 0) p.smooth_window = secondsToFrames(smooth_s, fps);
  }
  if (p.window > MAX_WINDOW)        { std::fprintf(stderr, "WARNING: window %d frames > MAX_WINDOW %d, clamped\n", p.window, MAX_WINDOW); }
  if (p.smooth_window > MAX_SMOOTH) { std::fprintf(stderr, "WARNING: smooth %d frames > MAX_SMOOTH %d, clamped\n", p.smooth_window, MAX_SMOOTH); }
  std::fprintf(stderr, "params: window=%d maxmissed=%d smooth=%d frames | k=%.2f contrast=%.2f drift=%.3f minarea=%d match=%.2f robust=%d%s\n",
               p.window, p.max_missed, p.smooth_window, p.k_sigma, p.min_contrast, p.drift_thresh, p.min_area, p.match_radius, p.robust_stats,
               fps > 0 ? " (fps given)" : "");
  if (path.empty()) { std::fprintf(stderr, "need --stream file.csv\n"); return 1; }
  std::ifstream in(path);
  if (!in) { std::fprintf(stderr, "cannot open %s\n", path.c_str()); return 1; }

  // detect grid size from header: 3 label columns + G*G pixel columns
  std::string header; std::getline(in, header);
  int cols = 1; for (char ch : header) if (ch == ',') cols++;
  int npix = cols - 3;
  in.clear(); in.seekg(0);
  if (npix == 64) return run<8>(in, p);
  if (npix == 16) return run<4>(in, p);
  if (npix == 4)  return run<2>(in, p);
  std::fprintf(stderr, "unsupported pixel count %d (expected 64, 16 or 4)\n", npix);
  return 1;
}
