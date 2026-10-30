# Renderer benchmark support

Scripts for measuring the Kiln flavors on a phone. Every script expects exactly one
connected device; set `ANDROID_SERIAL` if more are attached.

## Before measuring

1. Install both profile flavors:

   ```bash
   cd apps/kiln
   flutter build apk --profile --flavor skia
   flutter build apk --profile --flavor impeller
   adb install -r --user 0 build/app/outputs/flutter-apk/app-skia-profile.apk
   adb install -r --user 0 build/app/outputs/flutter-apk/app-impeller-profile.apk
   ```

   `--user 0` matters on phones with a clone or second-space profile; without it the app
   can land in the wrong profile.

2. Charge the phone, turn on Developer options → **Stay awake**, and fix the display
   refresh rate (some phones switch between 120 Hz and 90 Hz on their own).
3. Leave the phone alone while a script runs. The scripts tap the screen for you.

## Shader Storm

| Script | What it does |
|---|---|
| [`storm_bench.sh`](storm_bench.sh) | Cold, repeat and relaunch reveals for both flavors and each grid size, tracing off; writes a CSV and prints medians |
| [`storm_trace.sh`](storm_trace.sh) | One cold reveal with Flutter engine events in a system trace, then a summary |
| [`trace_summary.py`](trace_summary.py) | Summarises a trace: slowest raster frame, Skia programs or Impeller pipelines built, their thread, raster-thread states and CPU clock |

```bash
tool/benchmark/storm_bench.sh 3 "48 96 144" storm.csv
tool/benchmark/storm_trace.sh skia 144 skia-144.txt
tool/benchmark/storm_trace.sh impeller 144 impeller-144.txt
python3 tool/benchmark/trace_summary.py skia-144.txt
```

Numbers come from the app's own `KILN::Storm::result` logcat line, one per reveal. Use
`storm_bench.sh` for numbers and `storm_trace.sh` for explanations: tracing slows every
frame, so traced runs read higher.

### How the scripts find the buttons

At the start, the scripts read the screen once with `uiautomator dump` and find **Shader
Storm**, the **48 / 96 / 144** chips and the **REVEAL** button by their text. They print the
coordinates they found, for example:

```text
buttons: KILN_TAPS="home=600,450 c48=426,2047 c96=602,2047 c144=789,2047 reveal=612,2547"
```

Reading the screen switches on Flutter's accessibility tree, which adds work to every
frame, so measured runs happen in a fresh app process and only replay those coordinates.

If a phone does not expose the text, or to skip the lookup, pass the coordinates yourself.
Find them with Developer options → **Pointer location**:

```bash
KILN_TAPS="home=600,450 c48=426,2047 c96=602,2047 c144=789,2047 reveal=612,2547" \
  tool/benchmark/storm_bench.sh 3
```

## Markets benchmark mode

The Markets screen's benchmark mode uses deterministic fixture data instead of Binance:

```bash
cd apps/kiln
flutter run --profile --trace-systrace \
  --flavor impeller \
  --dart-define=KILN_BENCHMARK=true
```

Use `--flavor skia` for the controlled Skia run. The fixture removes network and changing
prices from the measurement, but it does not make the device's engine or driver caches cold.
For a true cold attempt, force-stop or clear only the selected flavor before launching it.

## Renderer evidence

Capture engine startup evidence separately:

```bash
tool/benchmark/capture_renderer_evidence.sh dev.fluttercon.kiln
tool/benchmark/capture_renderer_evidence.sh dev.fluttercon.kiln.skia
```

The script stores matching log excerpts but does not infer Vulkan from the app flavor. The
presenter must inspect the captured lines and label the run as verified or unverified.
