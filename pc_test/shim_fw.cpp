// shim_fw.cpp - compile the REAL firmware sketch (thermal_poc.ino) on a PC with a fake Arduino Serial.
// It reads protocol lines from stdin and answers on stdout, so check_firmware_protocol.py can test the sketch's
// parameter parsing and reply format without a board:
//   g++ -O2 -std=c++17 -o fw shim_fw.cpp      (Windows: -o fw.exe)
//   python check_firmware_protocol.py --shim ./fw --stream ..\data\streams\dev_single_laptop_weak.csv
// This covers the sketch's own code (line parsing, P/F/D handling, reply format) and the filter header.
// It does NOT cover the ESP32 hardware, floating-point differences of the Xtensa core, or serial timing:
// run check_firmware_protocol.py --port COM7 for that.
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

static uint32_t micros() {
  using namespace std::chrono;
  return (uint32_t)duration_cast<microseconds>(steady_clock::now().time_since_epoch()).count();
}

struct SerialShim {
  void setRxBufferSize(int) {}
  void begin(long) {}
  void setTimeout(int) {}
  int readBytesUntil(char term, char* buf, size_t n) {
    size_t i = 0; int c = 0;
    while (i < n && (c = std::getchar()) != EOF) { if (c == term) break; buf[i++] = (char)c; }
    if (c == EOF && i == 0) std::exit(0);              // stdin closed: leave the "firmware"
    return (int)i;
  }
  void println(const char* s) { std::printf("%s\n", s); std::fflush(stdout); }
  template <class... A> void printf(const char* f, A... a) { std::printf(f, a...); std::fflush(stdout); }
} Serial;

#include "../firmware/thermal_poc/thermal_poc.ino"

int main() { setup(); for (;;) loop(); }
