ESP32 FINAL CHECK of the frozen methods. Unzip OVER your thermal_poc folder (adds 2 files, changes nothing else).
Prereqs: board flashed with the CURRENT firmware\thermal_poc\thermal_poc.ino (step 5c or newer), Arduino serial monitor CLOSED, pip install pyserial.

1) Memory (PC side, 5 s), in pc_test:
   g++ -O2 -std=c++17 -o sizeof_filter.exe sizeof_filter.cpp && sizeof_filter.exe
   Also copy the line "Global variables use N bytes ..." from the Arduino IDE compile output.

2) Parity + timing on the board, in python (3-6 min):
   python esp32_final_check.py --port COM7
   -> writes ..\esp32_check.md and ..\esp32_check.csv. Expect: all rows "yes" (0 mismatches). Any mismatch: paste the FAIL lines.
   (Quick rehearsal first: python esp32_final_check.py --port COM7 --frames 200)

Paste back: esp32_check.md + the sizeof table + the Arduino "Global variables" line.
Uses dev streams only. Nothing is tuned or written to data\streams.
