# Rosetta — Flutter, Android and iOS

A translation table for Kotlin and iOS engineers. This content also appears in the
Engine Room's Rosetta tab.

## Threads and pipeline

| Flutter | Android (Views / Compose) | iOS (UIKit / SwiftUI) |
|---|---|---|
| Dart code (DevTools "UI"), on the platform **main thread** since Flutter 3.29 | Main thread | Main thread |
| Raster thread (Impeller) | RenderThread (HWUI) | Core Animation commit + render server |
| Vsync-driven frame | `Choreographer` frame callback | `CADisplayLink` |
| DisplayList / layer tree | RenderNode display lists | CALayer tree |
| Impeller on Vulkan / OpenGL ES | HWUI on Skia (Vulkan / OpenGL ES) | Core Animation on Metal |
| Background isolate (`Isolate.run`) | Coroutine on `Dispatchers.Default` | Task off the main actor / background queue |

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
