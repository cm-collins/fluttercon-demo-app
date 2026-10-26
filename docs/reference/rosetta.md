# Rosetta — Flutter, Android and iOS

A translation table for Kotlin and iOS engineers. This content also appears in the
Engine Room's Rosetta tab. Shared definitions for Flutter terms (paint vs raster,
`saveLayer`, shaders) live in [Talk vocabulary](../talk/vocabulary.md).

## Threads and pipeline

| Flutter | Android (Views / Compose) | iOS (UIKit / SwiftUI) |
|---|---|---|
| Dart animation/build/layout/paint (DevTools **UI** metric), on the platform **main thread** since Flutter 3.29 | Main thread UI work | Main actor / main thread UI work |
| Raster thread `1.raster` (Impeller CPU work; separate from the GPU) | Closest analogue: RenderThread / HWUI recording and submission | Closest analogue: Core Animation render preparation / render server |
| Vsync-driven frame | `Choreographer` frame callback | `CADisplayLink` |
| DisplayList / layer tree | RenderNode display lists | CALayer tree |
| Impeller on Vulkan / OpenGL ES | HWUI on Skia (Vulkan / OpenGL ES) | Core Animation on Metal |
| Background isolate (`Isolate.run`) | Coroutine on `Dispatchers.Default` | Task off the main actor / background queue |

The rows are conceptual equivalents, not identical implementations. In particular,
Flutter's raster thread is not Android's HWUI `RenderThread`; both occupy a similar
“prepare and submit rendering work off the main thread” role.

## Expensive operations

| Flutter | Android | iOS |
|---|---|---|
| `saveLayer` (via `Opacity`, `ShaderMask`, `ColorFilter`, save-layer clips) | `graphicsLayer { compositingStrategy = Offscreen }`, `View.setLayerType` | Offscreen rendering: masks, `shouldRasterize`, shadows without `shadowPath` |
| `BackdropFilter` blur | `RenderEffect` blur | `UIVisualEffectView` |
| `RepaintBoundary` | `graphicsLayer` isolation / separate RenderNode | Separate `CALayer` |
| `SnapshotWidget` | Draw to bitmap and reuse | `shouldRasterize = true` |
| Impeller shaders compiled at build time | HWUI/Skia shaders compiled at runtime (with caching) | Metal libraries compiled ahead of time |

## Tools

| Flutter | Android | iOS |
|---|---|---|
| DevTools Performance view | Android Studio profiler | Instruments: Time Profiler, Core Animation |
| `--trace-systrace` → Perfetto | Perfetto / System Tracing | Instruments (signposts) |
| Offscreen-layer checkerboard | "Debug GPU overdraw" / layer updates | "Color offscreen-rendered" (Simulator) |
| `FrameTiming` | `JankStats`, `FrameMetrics` | `MetricKit` hitch metrics |
| AGI (Vulkan frame capture) | AGI | Xcode GPU frame capture |
