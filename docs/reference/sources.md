# Sources

Primary sources used in the research. Checked October 2026 against Flutter 3.47.

## Impeller and rendering

- [Impeller rendering engine — Flutter docs](https://docs.flutter.dev/perf/impeller)
- [Impeller README — engine source tree](https://github.com/flutter/flutter/blob/main/engine/src/flutter/impeller/README.md)
- [Impeller on Android — backend selection](https://github.com/flutter/engine/blob/main/impeller/docs/android.md)
- [Impeller `Tessellator` API reference](https://api.flutter.dev/impeller/classimpeller_1_1_tessellator.html)
- [Impeller `path_tessellator.cc`](https://api.flutter.dev/impeller/path__tessellator_8cc_source.html)
- [Remove EntityPass and recombine canvas implementations — engine PR 55019](https://github.com/flutter/engine/pull/55019)
- [Vulkan encode and submit path lacks trace events — flutter#193399](https://github.com/flutter/flutter/issues/193399)
- [Impeller: overlaid CustomPainters and no raster cache — flutter#142550](https://github.com/flutter/flutter/issues/142550)
- [Android Impeller backdrop filter slower than Skia — flutter#174984](https://github.com/flutter/flutter/issues/174984)
- [BackdropFilter class](https://api.flutter.dev/flutter/widgets/BackdropFilter-class.html) and [BackdropGroup class](https://api.flutter.dev/flutter/widgets/BackdropGroup-class.html)
- [Backdrop blur cost and grouping caveats — flutter#191207](https://github.com/flutter/flutter/issues/191207)
- [SnapshotWidget class](https://api.flutter.dev/flutter/widgets/SnapshotWidget-class.html)
- [RepaintBoundary class](https://api.flutter.dev/flutter/widgets/RepaintBoundary-class.html)

## Flutter architecture and the Skia era

- [Flutter architectural overview](https://docs.flutter.dev/resources/architectural-overview)
- [Remove SkSL bundling from the tool — flutter#162849](https://github.com/flutter/flutter/pull/162849)
- [Perform no shader warm-up by default — flutter#87126](https://github.com/flutter/flutter/pull/87126)
- [cache-sksl cannot be used with Impeller — flutter#140310](https://github.com/flutter/flutter/issues/140310)
- [Why triangulation over stencil-then-cover — flutter#123671](https://github.com/flutter/flutter/issues/123671)
- [Storing the MSAA stencil on Vulkan — flutter#137302](https://github.com/flutter/flutter/issues/137302)
- [Impeller swapchain transients (MSAA, depth/stencil)](https://api.flutter.dev/impeller/classimpeller_1_1_swapchain_transients_v_k.html)
- [Impeller AHB swapchain](https://api.flutter.dev/impeller/classimpeller_1_1_a_h_b_swapchain_v_k.html) and [swapchain selection](https://api.flutter.dev/impeller/swapchain__vk_8cc_source.html)

## Vulkan and mobile GPUs

- [Vulkan: tile-based rendering best practices](https://docs.vulkan.org/guide/latest/tile_based_rendering_best_practices.html)
- [Vulkan: command buffer usage and multi-threaded recording](https://docs.vulkan.org/samples/latest/samples/performance/command_buffer_usage/README.html)
- [Vulkan tutorial: mobile rendering approaches](https://docs.vulkan.org/tutorial/latest/Building_a_Simple_Engine/Mobile_Development/04_rendering_approaches.html)
- [Arm: picking the most efficient load/store operations](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/picking-the-most-efficient-load-store-operations)

## Threads

- [What's new in Flutter 3.29 — Dart on the main thread](https://flutter.dev/blog/whats-new-in-flutter-3-29)
- [Merge the platform and UI threads — flutter#150525](https://github.com/flutter/flutter/issues/150525)

## Profiling

- [Use the Performance view — DevTools](https://docs.flutter.dev/tools/devtools/performance)
- [Flutter performance profiling](https://docs.flutter.dev/perf/ui-performance)
- [Performance best practices (saveLayer)](https://docs.flutter.dev/perf/best-practices)
- [FrameTiming class](https://api.flutter.dev/flutter/dart-ui/FrameTiming-class.html)
- [Android CPU profiling for Impeller](https://github.com/flutter/engine/blob/main/impeller/docs/android_cpu_profile.md)
- [Overview of system tracing — Android](https://developer.android.com/topic/performance/tracing)
- [Perfetto GPU data sources](https://perfetto.dev/docs/data-sources/gpu)
- [Android GPU Inspector quickstart](https://developer.android.com/agi/start)
- [AGI frame profiling](https://developer.android.com/agi/frame-trace/frame-profiler)

## History and milestones

- [Flutter 1.0 announcement (Dec 2018)](https://developers.googleblog.com/en/flutter-10-googles-portable-ui-toolkit/)
- [Announcing Flutter 1.20 — SkSL warm-up (Aug 2020)](https://flutter.dev/blog/announcing-flutter-1-20)
- [Flutter performance updates, first half of 2020](https://flutter.dev/blog/flutter-performance-updates-in-the-first-half-of-2020)
- [Automatic/scalable shader warm-up — flutter#32170](https://github.com/flutter/flutter/issues/32170) and [SkSL-based shader warm-up — flutter#53607](https://github.com/flutter/flutter/issues/53607)
- [What's new in Flutter 3.7 — Impeller iOS preview](https://flutter.dev/blog/whats-new-in-flutter-3-7)
- [What's new in Flutter 3.10 — Impeller default on iOS](https://flutter.dev/blog/whats-new-in-flutter-3-10)
- [What's new in Flutter 3.16 — Impeller Android preview](https://flutter.dev/blog/whats-new-in-flutter-3-16)
- [What's new in Flutter 3.29 — Skia removed on iOS, Impeller GLES fallback, BackdropGroup](https://flutter.dev/blog/whats-new-in-flutter-3-29)
- [Use Vulkan for graphics — Android (Vulkan since API 24, 1.1 on 64-bit Android 10+, ANGLE)](https://developer.android.com/games/develop/vulkan/overview)
- [Android 15 beta 2 — ANGLE on Vulkan roadmap](https://android-developers.googleblog.com/2024/05/the-second-beta-of-android-15.html)
- [Vulkan as Android's official graphics API (Mar 2025)](https://android-developers.googleblog.com/2025/03/building-excellent-games-with-better-graphics-and-performance.html)
- [Vulkan on Android — Vulkanised 2025 (ANGLE plans for Android 16 and 17)](https://www.vulkan.org/user/pages/09.events/vulkanised-2025/T15-Ian-Elliott-Google-Vulkan-on-Android.pdf)
- [Android GPU Inspector open beta (Sep 2020)](https://android-developers.googleblog.com/2020/09/android-gpu-inspector-open-beta.html)
- [DevTools 2.21.1 — embedded Perfetto trace viewer](https://docs.flutter.dev/tools/devtools/release-notes/release-notes-2.21.1) and [2.34.1 — legacy viewer removed](https://docs.flutter.dev/tools/devtools/release-notes/release-notes-2.34.1)
- [Bring Observatory timeline features into DevTools — devtools#2210](https://github.com/flutter/devtools/issues/2210)

## Data

- [OpenF1 documentation](https://openf1.org/docs/)
- [OpenF1 licence (CC BY-NC-SA 4.0)](https://github.com/br-g/openf1/blob/main/LICENSE)
