# Fact check

Every factual claim in the deck, where it comes from, and how it was checked on 2026-11-03. Use this
to answer a challenge from the audience. When a Flutter version changes, check the engine rows again.

**Order of trust:** the engine source for the Flutter version the app runs (3.47.8, engine `cf636b1dfb`,
under `engine/src/flutter/` in the SDK), then the Flutter docs and release notes, then these captures.

## Which backend an Android phone gets

From `shell/platform/android/flutter_main.cc`, `android_context_dynamic_impeller.cc`,
`android_context_vk_impeller.cc` and `impeller/renderer/backend/vulkan/driver_info_vk.cc`:

| Device | Result |
|---|---|
| Below API 29, or a Vivante GPU | Skia on OpenGL ES |
| API 29+, and any check below fails | Impeller on OpenGL ES |
| API 29+, and every check passes | Impeller on Vulkan |

The checks that send a phone to OpenGL ES:

- It's an emulator.
- It's a Huawei device, or has a Huawei Maleoon GPU.
- It's a MediaTek chip whose **vendor** API (`ro.vendor.build.version.sdk`) is below 32. Updating the OS doesn't change this number.
- Its board is on the known-bad list, which is mostly older Exynos chips (`ro.product.board`).
- It has an Adreno 650 or older, a first-generation Samsung Xclipse, or a PowerVR GPU older than the CXT series. A Pixel 10 with an old driver also fails.
- Vulkan 1.1 can't start with the extensions Impeller needs.

**Find out why a phone uses OpenGL ES:**

```text
adb logcat -d | grep -E "Impeller rendering backend|Known bad Vulkan"
adb shell getprop ro.build.version.sdk
adb shell getprop ro.vendor.build.version.sdk
adb shell getprop ro.vendor.mediatek.platform
adb shell getprop ro.product.board
adb shell getprop ro.hardware.egl
adb shell dumpsys SurfaceFlinger | grep -i "GLES:"
```

**The docs and the source differ here.** The [Impeller page](https://docs.flutter.dev/perf/impeller)
says devices without Vulkan fall back to "the legacy OpenGL renderer". The engine source and the
[3.29 release post](https://flutter.dev/blog/whats-new-in-flutter-3-29) say API 29+ falls back to Impeller
on OpenGL ES. The deck follows the source.

## Claims from Flutter and Vulkan sources

| Slide | Claim | Source |
|---|---|---|
| 3 | Framework in Dart, engine mostly C++, embedder Java and C++ on Android, `dart:ui` between them | [Architectural overview](https://docs.flutter.dev/resources/architectural-overview) |
| 5 | About 4 + 4 ms at 120 Hz, and each thread can use a whole refresh | [Performance best practices](https://docs.flutter.dev/perf/best-practices): at 60 Hz, 16 ms each for building and rendering, 8 + 8 ms if latency matters; at 120 fps, under 8 ms in total |
| 7 | Issue quote "requires 0 extra effort from developers"; opened 6 May 2019, closed 11 Aug 2023, then a team comment pointed to Impeller | [flutter/flutter#32170](https://github.com/flutter/flutter/issues/32170). Said in the notes only. The issue body has been edited, so don't say the quote dates from 2019 |
| 8, 26 | `impellerc` produces SPIR-V for Vulkan, Metal for Apple and GLSL ES for OpenGL ES | `impeller/README.md`; the built `depth_fill.frag` also holds SkSL |
| 8, 10 | iOS runs Impeller on Metal only; macOS also uses Metal | `shell/platform/darwin/ios/`; [Impeller page](https://docs.flutter.dev/perf/impeller) |
| 8, 12 | Dart on the main thread since 3.29, on Android and iOS, and not because of Impeller | [3.29 release post](https://flutter.dev/blog/whats-new-in-flutter-3-29); the Skia trace shows the same thread |
| 9 | Pipelines are built up front by design, and some are still built in the frame | `impeller/README.md`; 40 `PipelineVK::Create` in `impeller-144.txt` |
| 9 | On Vulkan, the driver still compiles when a pipeline is built | [Vulkan pipeline cache sample](https://docs.vulkan.org/samples/latest/samples/performance/pipeline_cache/README.html). Impeller keeps a disk pipeline cache: `pipeline_cache_vk.cc` |
| 10 | iOS default in 3.10, May 2023; Android in 3.27, December 2024; desktop in 3.47; Skia removed from iOS in 3.29 | [What's new archive](https://docs.flutter.dev/release/archive-whats-new); [Impeller page](https://docs.flutter.dev/perf/impeller) |
| 12, 24 | Impeller has no raster cache | `EnableRasterCache()` returns false in the three Impeller surfaces under `shell/gpu/` |
| 13 | The two log lines | `shell/common/shell.cc`; `android_context_vk_impeller.cc`; `evidence/*.log` |
| 16 | Stroke: two vertices per point, a join only above a threshold, triangle strip | `impeller/entity/geometry/stroke_path_geometry.cc` |
| 17 | Submit with a fence | `impeller/renderer/backend/vulkan/command_queue_vk.cc` |
| 18 | saveLayer and the firehose comparison; ShaderMask and ColorFilter as triggers | [Performance best practices](https://docs.flutter.dev/perf/best-practices) |
| 28 | Perfetto recommended from Android 10 | [Android system tracing](https://developer.android.com/topic/performance/tracing) |

## Where the demo's numbers come from

They come from the demo app's own settings in `packages/shader_lab/lib/src/logic/thrash_scene.dart`, not from Flutter.

| Number | How it's made |
|---|---|
| 16 lines at 8× | `lineCount = 2 × level` |
| 8,000 points a line | `pointsPerLine = 1000 × level` |
| 480 heat strip segments | `stripSegments = 60 × level` |
| 64 glowing dots and layers | `dotCount = lines × 4` |
| 129,920 path points | 16 × 8,000 + 480 × 4 |
| 624 draws | 16 lines + 480 segments + 64 dots × 2 |
| 640 draws after Fix 1 | Each line draws twice, to cover the scroll: 32 + 480 + 128 |
| 161 draws after Fix 2 | 32 + 1 + 128 |
| 12,032 path points after Fix 1 | 16 × 632 + 1,920. 632 points is 2 × 316 pixel columns |
| 10,112 path points after Fix 2 | 16 × 632 |
| 25 points per pixel column | 8,000 ÷ 316 |
| At least 256,000 vertices | 16 × 8,000 × 2. **Worked out from the stroke rule, not measured** |

## Measured numbers

All from `~/fluttercon-captures/2026-10-31-infinix-x6873/`. The medians were recomputed from the raw
CSV files, and the thread state from the raw trace. All match the slides except the corrections below.

| Slide | Numbers | File |
|---|---|---|
| 13, 14, 33 | Worst frames, every engine, tile count and scenario | `bench/storm.csv` |
| 20–25, 30, 34 | UI and raster p90, every fix combination, both engines | `bench/thrash-*.csv` |
| 7, 15 | 118 programs, 1,714 ms, 1,820 ms frame; 40 pipelines, 87 ms, 2.2 ms each | `traces/perfetto-system/summaries.txt` |
| 28 | Raster 27.9 → 4.8, Encode 27.1 → 3.7, saveLayer 64 → 0, QueueSubmit 2 → 1, frames 179 → 604 | `summaries.txt` |
| 28 | Running 24.0 of 27.9 ms on the median frame (70–99% across frames) | Recomputed from `sched_switch` in `thrash-trace-none.txt` |
| 29 | Frame rates and budget shares | `summaries.txt` |
| 26 | 503 B → 4,008 B | `depth_fill.frag` and its built asset |

## Corrected in this check

| Slide | It said | Now | Why |
|---|---|---|---|
| 8–10, 12 | Vulkan on Android 10+, as if guaranteed | New slide 11 shows the three outcomes and the checks | The engine checks the device too |
| 6, 8, 12 | Engine titles and table with no platform | Marked as Android, with Metal named for iOS and macOS | iOS doesn't use Vulkan |
| 10 | "No shader compilation while the app runs" | Removed; notes explain the driver step | On Vulkan, the driver compiles at pipeline creation |
| 2 | "Fixed" compilation jank | "Tamed" | 145 ms still misses the 8.3 ms budget |
| 12 | Columns "Skia" and "Impeller", including the Dart row | Columns "Before" and "Now" | The Skia build also runs Dart on the main thread |
| 16, 20, 22 | 8,000 with no explanation | Labelled as the demo's own setting | It is a stress setting, not a Flutter number |
| 7, 9 | 14.6 ms a program | 14.5 ms | 1,714 ÷ 118; 14.61 is the average over all 139 in the trace |
| 18 | "About 9 ms" for layers | Raster 13.7 → 6.6 ms | Same source as slide 23, with tracing off |
| 21 | Bars with no caveat | Batch and Isolate marked as within noise | Their run ranges overlap the no-fix run |
| 22 | "About 330 pixels wide" | About 316 | 632 points ÷ 2 |
| 23 | Glow is "the biggest win", Batch "the smallest" | "It halves", "a smaller win" | Simplify saves 11.1 ms, Glow 7.1 ms, and Isolate only 0.1 ms |
| 29 | 1000 ÷ raster: 72 and 208 | 73 and 207 | From the unrounded trace values |
| Demo script | "Running 90–98% of every traced frame" | 24 of 28 ms; 70–99% across frames | Recomputed from the trace |

## Removed, because it couldn't be confirmed

The Sky 2015 date and the dates of the 2019–2021 workarounds are off the slides and out of the notes.

## Still not verified

- **GPU-side render passes.** This phone's driver doesn't expose them, and the slides say so. Slide 18 is the Vulkan model.
- **Your Android 13 phone.** The cause depends on the commands above. Keep the bracketed line in the notes for slide 11 unless you've confirmed it.
- **Live numbers on another phone.** They will differ from the Infinix numbers on the slides.
