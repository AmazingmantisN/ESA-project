v25 package (24 Oct 2026): post-hoc count metrics + LINAIGE first look. Nothing here re-tunes anything.

Unzip into ...\thermal_poc\thermal_poc so that python\count_metrics.py and python\linaige_check.py sit next to tune_sweep.py.
linaige_protocol.md goes in the project root (commit it before opening LINAIGE: it is the written plan).

RUN 1 - count metrics (minutes):
  cd ...\thermal_poc\thermal_poc\python
  python count_metrics.py --papanashi "..\..\..\papanashi_csvs"
  -> writes ..\count_metrics.md and ..\acf.png. Paste count_metrics.md back.

RUN 1b - same metrics on the synthetic test suite (optional, ~same time as eval_suite):
  python count_metrics.py --papanashi "..\..\..\papanashi_csvs" --synth "<the Stage 1.1 folder you used for eval_test_v11>" --split test --jobs 18
  (use the same folder/--split you gave eval_suite.py; if your suite has no manifest.csv, point --synth at the test folder only)

RUN 2 - LINAIGE first look (no scoring):
  Download kaggle.com/datasets/francescodaghero/linaige (free Kaggle account), unzip anywhere, then
  python linaige_check.py "C:\path\to\linaige"
  Paste the printout back; I will write the converter and the one-shot transfer run from it.

RUN 3 - energy (needs a USB power meter, about Rs 300-600, e.g. a "USB voltage current tester"):
  Put the meter between the laptop USB port and the ESP32. Note the current with the board idle (firmware running, no frames sent)
  and while stream_to_esp32.py replays a stream. Energy per frame ~= 5 V x (running - idle current) x time per frame.
  Also write down the CPU clock (Arduino IDE: Tools > CPU Frequency) for the paper.
