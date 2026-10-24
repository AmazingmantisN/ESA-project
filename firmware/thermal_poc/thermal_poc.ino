// thermal_poc.ino  -  ESP32 firmware for the offline-replay proof of concept.
// The PC streams thermal frames over USB-serial; the ESP32 runs the REAL persistence
// filter and reports the count plus how many microseconds the filter itself took.
//
// Board: any ESP32 dev board.  Arduino IDE: "ESP32 Dev Module", 921600 baud in the script.
// To emulate a smaller sensor, build with -DGRID=4 or -DGRID=2 (PlatformIO: build_flags),
// or just edit the #define below, and feed a matching stream_4x4.csv / stream_2x2.csv.
//
// Protocol (text, '\n' terminated):
//   "R"                       -> reset filter, replies "OK"
//   "F,<id>,<v0>,...,<vN>"    -> one frame (GRID*GRID values, degC), DHT taken as 0, replies
//                                "R,<id>,<raw_count>,<smoothed_count>,<filter_microseconds>,<static_count>"
//   "D,<id>,<dht>,<v0>,...,<vN>" -> same, but with the DHT ambient reading (needed by threshold_mode 1)
//   "P,<k>,<contrast>,<minarea>,<match>,<window>,<drift>,<maxmissed>,<smooth>,<robust>"
//       optionally continued with the v2 fields
//   ",<thr_mode>,<pers_mode>,<dht_offset>,<n_persist>,<reset>,<centroid>,<metric>,<conn>,<count_static>,<max_tracks>,<max_blobs>"
//       optionally continued with the Ours-v2 fields (step 5c; sent only when one of them is non-default)
//   ",<persist_frames>,<hyst_frames>,<cand_policy>,<cand_min_area>,<cand_max_peak>,<assign_mode>,<merge_area>"
//       optionally continued with the Ours-v3 fields (step 5d; sent only when liveness is used)
//   ",<live_frames>,<live_thresh>"
//                             -> set parameters (also resets), replies "OK"
// NOTE: a sketch older than step 5c silently ignores the last 7 fields, so Ours-v2 settings would run as v1.
//       check_firmware_protocol.py catches this (mismatching counts): reflash this sketch after updating.
#include "persistence_filter.h"

#ifndef GRID
#define GRID 8
#endif
constexpr int NVAL = GRID * GRID;

static PersistenceFilter<GRID, GRID> filt;   // all buffers inside are fixed-size, no malloc
static char  line[1400];                      // static receive buffer (no Arduino String)
static float frame[NVAL];

void setup() {
  Serial.setRxBufferSize(4096);
  Serial.begin(921600);
  Serial.setTimeout(500);
}

void loop() {
  int n = Serial.readBytesUntil('\n', line, sizeof(line) - 1);
  if (n <= 0) return;
  line[n] = 0;
  if (n && line[n - 1] == '\r') line[--n] = 0;

  if (line[0] == 'R' && line[1] == 0) {                  // reset
    filt.reset();
    Serial.println("OK");
    return;
  }

  if (line[0] == 'P') {                                  // parameters
    FilterParams p; char* s = line + 1;
    p.k_sigma       = strtof(s + 1, &s);
    p.min_contrast  = strtof(s + 1, &s);
    p.min_area      = (int)strtol(s + 1, &s, 10);
    p.match_radius  = strtof(s + 1, &s);
    p.window        = (int)strtol(s + 1, &s, 10);
    p.drift_thresh  = strtof(s + 1, &s);
    p.max_missed    = (int)strtol(s + 1, &s, 10);
    p.smooth_window = (int)strtol(s + 1, &s, 10);
    p.robust_stats  = (int)strtol(s + 1, &s, 10);
    if (*s == ',') {                                     // v2 fields (baseline modes); absent => v1 behaviour
      p.threshold_mode   = (int)strtol(s + 1, &s, 10);
      p.persistence_mode = (int)strtol(s + 1, &s, 10);
      p.dht_offset       = strtof(s + 1, &s);
      p.n_persist        = (int)strtol(s + 1, &s, 10);
      p.reset_thresh     = strtof(s + 1, &s);
      p.centroid_mode    = (int)strtol(s + 1, &s, 10);
      p.match_metric     = (int)strtol(s + 1, &s, 10);
      p.connectivity     = (int)strtol(s + 1, &s, 10);
      p.count_static     = (int)strtol(s + 1, &s, 10);
      p.max_tracks       = (int)strtol(s + 1, &s, 10);
      p.max_blobs        = (int)strtol(s + 1, &s, 10);
      if (*s == ',') {                                   // Ours-v2 fields (step 5c); absent => v1 / baseline behaviour
        p.persist_frames = (int)strtol(s + 1, &s, 10);
        p.hyst_frames    = (int)strtol(s + 1, &s, 10);
        p.cand_policy    = (int)strtol(s + 1, &s, 10);
        p.cand_min_area  = (int)strtol(s + 1, &s, 10);
        p.cand_max_peak  = strtof(s + 1, &s);
        p.assign_mode    = (int)strtol(s + 1, &s, 10);
        p.merge_area     = (int)strtol(s + 1, &s, 10);
        if (*s == ',') {                                 // Ours-v3 fields (step 5d); absent => no liveness
          p.live_frames  = (int)strtol(s + 1, &s, 10);
          p.live_thresh  = strtof(s + 1, &s);
        }
      }
    }
    filt.setParams(p); filt.reset();
    Serial.println("OK");
    return;
  }

  if (line[0] == 'F' || line[0] == 'D') {                // frame ('D' also carries the DHT reading)
    char* s = line + 2;
    long id = strtol(s, &s, 10);
    float dht = 0.f;
    if (line[0] == 'D') { if (*s == ',') s++; dht = strtof(s, &s); }
    for (int i = 0; i < NVAL; i++) {
      if (*s == ',') s++;
      frame[i] = strtof(s, &s);
    }
    uint32_t t0 = micros();
    int smoothed = filt.process(frame, dht);             // <-- the thing we are timing
    uint32_t dt = micros() - t0;
    Serial.printf("R,%ld,%d,%d,%lu,%d\n", id, filt.lastRawCount(), smoothed, (unsigned long)dt, filt.lastStaticCount());
  }
}
