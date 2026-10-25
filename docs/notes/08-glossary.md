# 08 · Glossary

Short definitions for lookup. For **aligned talk wording** (what to say on stage, what not
to confuse), use [Talk vocabulary](../talk/vocabulary.md).

| Term | Meaning |
|---|---|
| **AGI** | Android GPU Inspector: Google's GPU profiler for Android, including a Vulkan frame profiler. |
| **AHardwareBuffer (AHB)** | Android's shareable GPU/CPU buffer type; basis of the optional SurfaceControl swapchain. |
| **AOT** | Ahead-of-time compilation. Dart in profile/release builds; Impeller shaders at engine build time. |
| **Backdrop filter** | A filter (usually blur) applied to what is already drawn behind a widget. |
| **`BackdropGroup`** | Widget that lets several `BackdropFilter.grouped` children share one backdrop pass (identical filter, non-overlapping layout). |
| **Build (frame phase)** | Dart widget rebuild and layout; part of `buildDuration` in `FrameTiming`. |
| **Composite (frame phase)** | Building the layer tree after paint; layers are sent toward the engine. |
| **Compilation jank (shader)** | Frame stutter when a new GPU shader is compiled during rasterization (Skia era); distinct from general "jank". |
| **Decimation (paths)** | Reducing path point count (e.g. min/max per pixel column) before tessellation. |
| **Draw (overload)** | Either recording ops in `paint()`, issuing GPU draw commands on the raster thread, or colloquial "drawing the UI". Prefer the specific term. |
| **Paint (frame phase)** | Recording draw operations into a `DisplayList` on the main thread; does not execute on the GPU yet. |
| **Path** | Vector geometry (`Path` class); Impeller tessellates paths to triangles on the CPU when rasterized. |
| **Pit stop** | Kiln toggle that swaps broken vs fixed code for one anti-pattern. |
| **Rasterize** | Raster-thread replay of DisplayLists through Impeller into GPU command buffers; `rasterDuration` in `FrameTiming`. |
| **Command buffer** | A recorded list of GPU commands submitted to a queue. |
| **Descriptor set** | Vulkan bindings of uniforms and textures used by a draw. |
| **DisplayList** | Flutter's recorded list of drawing operations, produced by `paint()` and replayed by the engine. |
| **Draw call** | One instruction to the GPU to draw geometry with the current pipeline and bindings. |
| **Embedder** | Platform code that hosts the Flutter engine (on Android: `FlutterActivity`, `FlutterView`, JNI). |
| **Entity** | Impeller's unit of drawing: transform + blend mode + contents + geometry. |
| **Frame budget** | Time available per frame: 8.33 ms at 120 Hz; talk also uses ~4 ms UI + ~4 ms raster as a single-frame latency target. |
| **Thrash** | Kiln demo control that multiplies Speed Ribbon (and related) workload to stress the raster path (1×–8×). |
| **FrameTiming** | Per-frame timings from the engine: build, raster, total span. |
| **impellerc** | Impeller's shader compiler: GLSL → SPIR-V → backend formats, at build time. |
| **Jank** | A frame that misses its display deadline, visible as a stutter. |
| **JIT** | Just-in-time compilation. Dart in debug mode; Skia's shaders at runtime. |
| **Load / store op** | Vulkan render-pass settings that decide whether attachments are read from or written to main memory. |
| **Main thread** | The Android/iOS UI thread. Runs Flutter's Dart code since Flutter 3.29 (DevTools "UI"). |
| **MSAA** | Multisample antialiasing. Impeller uses 4× on mobile, resolved in tile memory. |
| **Opacity peephole** | Engine optimisation that applies group opacity per draw when children don't overlap, avoiding `saveLayer`. |
| **Perfetto** | Android's system tracing tool and trace viewer (successor to Systrace on Android 10+). |
| **Pipeline (PSO)** | Compiled shaders plus fixed GPU state. Impeller builds them ahead of time. |
| **Profile mode** | AOT-compiled build with tracing hooks. The only mode for performance measurement. |
| **Raster cache** | Skia-era cache of complex layers as images. Impeller has none. |
| **Raster thread** | Engine thread (`1.raster`) where Impeller turns layer trees into GPU commands. Runs on the CPU. |
| **Render pass** | A block of drawing into a fixed set of attachments. Boundaries are expensive on tile-based GPUs. |
| **Render target cache** | Impeller's reuse of offscreen textures across frames. |
| **`RepaintBoundary`** | Widget that gives its subtree its own layer so repaints don't spread. Not a cache on Impeller. |
| **`saveLayer`** | Canvas call that draws a group into an offscreen texture, then composites it. Triggers a render-pass switch. |
| **Shader Lab** | Kiln screen built twice (Skia on pinned Flutter 3.24, Impeller on current Flutter) to compare first-use shader compilation live. |
| **SkSL** | Skia's shading language; source of runtime shader compilation in the Skia era. |
| **SnapshotWidget** | Widget that replaces its child with a cached image while snapshotting is enabled. |
| **SPIR-V** | Vulkan's intermediate shader format. |
| **Stencil-then-cover** | GPU path-filling technique using the stencil buffer; Impeller chose CPU triangulation instead. |
| **SurfaceFlinger** | Android's system compositor; records the Expected/Actual frame timeline. |
| **Swapchain** | The set of images an app renders into and presents to the display. |
| **Tessellation (Impeller)** | CPU conversion of paths into triangles (curve flattening + triangulation). Not GPU tessellation shaders. |
| **Tile-based GPU** | Mobile GPU architecture rendering small screen tiles in on-chip memory. |
| **totalSpan** | `FrameTiming` field: vsync start to raster finish. |
| **Vsync** | Display refresh signal that starts each frame (from `Choreographer` on Android). |
| **Vulkan** | Explicit, low-level graphics API; Impeller's preferred backend on Android API 29+. |
