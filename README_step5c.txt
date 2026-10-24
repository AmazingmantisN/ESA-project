STEP 5c - Ours-v2 Layer 1. Unzip OVER your thermal_poc folder (same layout; overwrites 7 files).
Windows, in thermal_poc\pc_test:
  g++ -O2 -std=c++17 -o run_pc.exe run_pc.cpp
  g++ -O2 -std=c++17 -o test_modes.exe test_modes.cpp && test_modes.exe        (expect: 35 tests, 0 failed)
  g++ -O2 -std=c++17 -o fw.exe shim_fw.cpp
  python check_firmware_protocol.py --shim fw.exe --stream ..\data\streams\dev_single_laptop_weak.csv   (13 sets OK)
  python check_v1_equiv.py                                   (expect mismatches: 0)
  python check_v2_nested.py                                  (expect mismatches: 0)
Optional regression vs your OLD build: copy old run_pc.exe to run_pc_prev.exe first, then
  python check_v2_nested.py --ref run_pc_prev.exe
REFLASH thermal_poc.ino in Arduino IDE (old sketches silently ignore the 7 new P fields), then
  python check_firmware_protocol.py --port COM7 --stream ..\data\streams\dev_single_laptop_weak.csv
