# Renderer benchmark support

The app's benchmark mode uses deterministic fixture data instead of Binance:

```bash
cd apps/kiln
flutter run --profile --trace-systrace \
  --flavor impeller \
  --dart-define=KILN_BENCHMARK=true
```

Use `--flavor skia` for the controlled Skia run. The fixture removes network and changing
prices from the measurement, but it does not make the device's engine or driver caches cold.
For a true cold attempt, force-stop or clear only the selected flavor before launching it.

Capture engine startup evidence separately:

```bash
tool/benchmark/capture_renderer_evidence.sh dev.fluttercon.kiln
tool/benchmark/capture_renderer_evidence.sh dev.fluttercon.kiln.skia
```

The script stores matching log excerpts but does not infer Vulkan from the app flavor. The
presenter must inspect the captured lines and label the run as verified or unverified.
