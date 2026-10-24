// sizeof_filter.cpp - static RAM of the filter object for several grid sizes (the firmware keeps it as a global, no malloc).
//   g++ -O2 -std=c++17 -o sizeof_filter.exe sizeof_filter.cpp && sizeof_filter.exe
// PC sizes (64-bit) can differ a little from the ESP32 (32-bit) if the struct holds pointers/size_t; the Arduino IDE compile report
// ("Global variables use N bytes") is the authoritative number for the whole sketch - paste that line next to this table.
#include <cstdio>
#include <cstring>
#include <cmath>
#include <cstdlib>
#include <cstdint>
#include "../firmware/thermal_poc/persistence_filter.h"
int main() {
  std::printf("grid,filter_bytes,upsampled_cells\n");
  std::printf("2x2,%zu,%d\n", sizeof(PersistenceFilter<2, 2>), PersistenceFilter<2, 2>::NCELL);
  std::printf("4x4,%zu,%d\n", sizeof(PersistenceFilter<4, 4>), PersistenceFilter<4, 4>::NCELL);
  std::printf("8x8,%zu,%d\n", sizeof(PersistenceFilter<8, 8>), PersistenceFilter<8, 8>::NCELL);
  std::printf("16x16,%zu,%d\n", sizeof(PersistenceFilter<16, 16>), PersistenceFilter<16, 16>::NCELL);
  return 0;
}
