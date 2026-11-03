# Abstract alignment

The registered abstract is a promise to the audience. Terminology is aligned in
[Talk vocabulary](vocabulary.md). This page maps every promise to the
exact moment in the demo where it is delivered, and to the evidence on screen. If a row
has no line number, the talk does not deliver it.

## The registered abstract

> **Beyond Skia: Deep-Dive GPU Scheduling and Profiling with Impeller on Android 10+**
>
> With Flutter's definitive transition to the Impeller rendering engine, the ecosystem has
> achieved a predictable, ahead-of-time (AOT) shader-compiled execution model. However,
> hitting a rock-solid, fluid 120fps on modern high-refresh-rate Android devices requires
> engineers to shift how they diagnose, isolate, and fix rendering bottlenecks.
>
> This session bypasses high-level UI paradigms to dissect exactly how Impeller interacts
> with the modern Vulkan graphics API on Android 10+ (API 29+). We will dive into how
> Impeller schedules GPU pipelines, uses modern tessellation to break vector paths into
> fast-rendering triangles, and manages explicit command buffers to prevent frame drops
> under heavy stress loads.
>
> We will intentionally thrash a real-time graphics canvas and step through deep-dive
> profiling.
>
> Attendees will learn how to parse advanced Flutter DevTools Timeline traces, interpret
> Android Systrace/Perfetto metrics, and engineer surgical UI optimizations—such as precise
> repaint boundary isolation and layer complexity reduction—to confidently ship
> enterprise-grade mobile experiences.
>
> **Key takeaways**
>
> - **Demystifying the Engine:** Understand the architectural differences between Skia's
>   JIT shader compilation and Impeller's AOT pipeline mechanics on Vulkan.
> - **Low-Level Profiling:** Master advanced Flutter DevTools and Android Systrace to read
>   frame-budget allocations (~4ms UI / ~4ms Raster thread).
> - **Taming Custom Painters:** Learn code patterns that maximize Impeller's pre-compiled
>   rendering pathways, avoiding expensive canvas operations like saveLayer().

## Promise → delivery map

Slide numbers refer to the [deck](slides/beyond-skia.pptx) and the [Demo script](demo-script.md); segment scripts
are linked where the detail lives. Evidence files are in `~/fluttercon-captures/2026-10-31-infinix-x6873/`.

| # | Promise in the abstract | Delivered at | What the audience sees | Evidence file | Status |
|---|---|---|---|---|---|
| P1 | Definitive transition to Impeller, AOT shader compilation | Slides 5–10 | Concept video, engine before and now, compilation jank, rollout timeline, Skia 1,863 ms vs Impeller 145 ms first reveal | `bench/storm.csv`, `videos/storm-*.mp4` | ✅ measured |
| P2 | Rock-solid 120 fps on high-refresh Android | Slides 4, 21, 24 | 8.3 ms budget; broken ~36 fps → fixed 604 frames in 5 s (120 fps) | `traces/perfetto-system/thrash-trace-all.txt` | ✅ measured |
| P3 | Shift how engineers diagnose, isolate, fix | Slides 2, 15–24 | Thread → event → code → fix → measure, applied to every fix | Canvas Thrash script | ✅ |
| P4 | How Impeller interacts with Vulkan on Android 10+ | Slides 6–9, 12 | Architecture, pipeline and command-buffer slides; log line "Using the Impeller rendering backend (Vulkan)"; Mali-G615, Vulkan 1.3 | `evidence/` | ✅ |
| P5 | How Impeller schedules GPU pipelines | Slides 7, 10 | 40 `PipelineVK::Create` in the reveal frame, 2.2 ms each, on `1.raster`; 30 → 40 as effects triple | `traces/perfetto-system/impeller-144.txt` | ✅ measured |
| P6 | Tessellation of vector paths into triangles | Slides 11, 16, 17 | Tessellation built step by step; X-ray triangle lens; path points 129,920 → 12,032; `Encode` 27 → 13 ms | video 0:32–0:59; `thrash-trace-*.txt` | ✅ modelled + measured indirectly |
| P7 | Explicit command buffers under heavy stress | Slides 12, 14, 24 | `SurfaceFrame::Encode` dominates the raster frame; `QueueSubmit` 2 → 1 per frame when layers go | `thrash-trace-none.txt`, `thrash-trace-all.txt` | ⚠️ CPU side measured; GPU execution explained, not traced |
| P8 | Intentionally thrash a real-time canvas | Slides 1, 15 | Dial 1× → 8×, both lanes red | `videos/thrash-impeller-stage.mp4` 0:00–0:32 | ✅ |
| P9 | Parse advanced DevTools Timeline traces | Slide 23; Perfetto section of the demo script | Frames chart from an emulator, named `KILN::Thrash::*` spans; Dart timeline opened in Perfetto for Q&A | `traces/dart-timeline/*.perfetto-trace` | ⚠️ same data, shown in Perfetto, not the DevTools UI. Closed by the [10-minute capture](../notes/06-profiling-playbook.md#devtools-capture-for-the-talk-10-minutes-any-android-phone) |
| P10 | Interpret Systrace / Perfetto metrics | Slide 24 | Main and `1.raster` slices, thread state (running vs sleeping), `saveLayer` and `QueueSubmit` counts, budget shares and frame rate; recorded with `atrace`, the tool behind Systrace | `traces/perfetto-system/`, `summaries.txt` | ✅ measured. No Expected / Actual Timeline in these captures |
| P11 | Precise repaint boundary isolation | Slide 20 | Grid repaints → 0/s; `KILN::Thrash::grid` absent from the timeline; UI 4.4 → 3.4 ms | `devtools-timeline-8x-isolate.perfetto-trace` | ✅ measured |
| P12 | Layer complexity reduction | Slides 14, 18, 19 | Layers 64 → 0; raster 13.7 → 6.6 ms; `saveLayer` 64 → 0 per frame in the trace | `thrash-trace-simplifyPaths+batchDraws.txt` vs `-all.txt` | ✅ measured |
| P13 | Confidence to ship | Slides 21, 24, 25 | Medians with ranges, honest limits, scripts to reproduce | `bench/`, `tool/benchmark/` | ✅ |
| T1 | Skia JIT vs Impeller AOT pipeline mechanics on Vulkan | Slides 7, 9, 10 | 118 Skia programs vs 40 Impeller pipelines in one reveal frame | `skia-144.txt`, `impeller-144.txt` | ✅ measured |
| T2 | Read ~4 ms UI / ~4 ms raster allocations | Slides 4, 24 | Bench, fixed: UI 3.4 ms (under 4), raster 6.5 ms (under 8.3, over 4). Traces: budget shares for three states; 1000 ÷ raster = frame rate; 120 fps with UI + raster over 8.3 ms on 28% of frames | `bench/thrash-impeller.csv`, `summaries.txt` | ✅ measured; raster ends between the target and the limit, and the talk says so |
| T3 | Custom painter patterns, precompiled pathways, avoid `saveLayer()` | Slides 17–20, 22, 25 | Decimated cached paths, one `drawVertices`, gradient glow instead of `saveLayer` + blur (measured); your own `.frag` → `pubspec` → `FragmentProgram`, and the APK bundle with SPIR-V, GLSL ES and SkSL | `thrash_canvas.dart`; bench; `depth_fill.frag` and its built asset | ✅ patterns measured; custom shader shown as code and build output, not timed |

## Gaps, said out loud

| Gap | Why | What the talk does instead |
|---|---|---|
| GPU execution (render passes on the Mali GPU) | The phone's driver exposes only GPU memory to Perfetto | Slides 14, 24, 25 say so; render-pass cost is explained from the Vulkan model |
| DevTools UI walkthrough ("Master advanced Flutter DevTools") | The Infinix was returned before this was captured, so the deck only has a frames chart from an emulator. Frame analysis and Timeline Events have not been captured on a phone | **Open: the biggest gap left.** Needs the [10-minute capture](../notes/06-profiling-playbook.md#devtools-capture-for-the-talk-10-minutes-any-android-phone) on any Android phone. Until then, the same Dart timeline events open in Perfetto (see the Perfetto section of the demo script) |
| Expected / Actual Timeline | The captures used `atrace` text, which has no frame timeline | Not claimed. Frame rate comes from the raster slices instead |
| Raster at 6.5 ms is over the 4 ms raster target | Measured | Say it: inside the 8.3 ms frame, at 120 fps, with less headroom than four and four |
| Batch draws is a small win | Measured: 18.6 → 13.7 ms, overlapping ranges | The script calls it a smaller win. Alone, it is within run-to-run noise |

## Wording guardrails for the abstract's claims

The abstract uses some shorthand. These are the precise versions to say on stage.

| Abstract says | Say on stage | Why |
|---|---|---|
| "~4ms UI / ~4ms Raster" | "UI means Dart frame work on the platform main thread; Raster means Impeller work on `1.raster`. Target about 4 ms each so the frame lands within one refresh. Each can stretch to 8.33 ms without dropping, but you lose latency and headroom." | DevTools labels phases as UI/Raster; main and raster are the actual CPU threads, and consecutive frames pipeline ([Frame scheduling](../notes/05-frame-scheduling.md)) |
| "Skia's JIT shader compilation" | "Skia generated and compiled shaders just in time, during frames" | Skia generated SkSL at runtime; the driver compiled it on first use |
| "Impeller's AOT pipeline mechanics" | "Shaders compiled at engine build time; pipelines built from them mostly at startup, and the rest on first use, when the Vulkan driver finishes the compile" | Storm measured 40 `PipelineVK::Create` inside the 144-tile reveal frame, about 2 ms each: cheap, not zero |
| "On Android 10+ (API 29+)" | "Android 10 is the minimum. The engine then checks the device and picks Vulkan or OpenGL ES" | Emulators, older Adreno, some MediaTek and Exynos chips and others stay on OpenGL ES: [Fact check](fact-check.md#which-backend-an-android-phone-gets) |
| "Skia JIT versus Impeller AOT on Vulkan" | "The Skia comparison demonstrates first-use generation on OpenGL ES; the following segment explains Impeller's AOT pipeline mechanics on Vulkan" | Do not imply that both comparison APKs use the same graphics backend |
| "Prevent frame drops under heavy stress" | "Keep the recorded work small enough that the raster thread finishes inside its budget" | Command buffers don't prevent drops by themselves; less recorded work does |
| "Android Systrace" | "Systrace, now Perfetto" | Perfetto replaced Systrace in Android 10 and opens Systrace files |
| "Precise repaint boundary isolation" | "Isolate what repaints; Impeller still rasterizes the frame" | Impeller has no raster cache |
| "Maximize pre-compiled rendering pathways" | "Prefer draws Impeller already has a precompiled path for, like one `drawVertices` or a gradient fill, over offscreen layers; then measure" | Precompiled shaders remove runtime shader generation; they do not make expensive canvas work free |
| "Manages explicit command buffers" (GPU side) | "This trace shows the CPU side of the GPU: encoding and submissions" | This phone exposes no GPU render stages to Perfetto |
