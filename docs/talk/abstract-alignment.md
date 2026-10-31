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

Line numbers refer to the [Demo script](demo-script.md); segment scripts are linked where the
detail lives. Evidence files are in `~/fluttercon-captures/2026-10-31-infinix-x6873/`.

| # | Promise in the abstract | Delivered at | What the audience sees | Evidence file | Status |
|---|---|---|---|---|---|
| P1 | Definitive transition to Impeller, AOT shader compilation | 02:30 lines 8–12; 04:30 Shader Storm | Concept video, timeline, Skia 1,863 ms vs Impeller 145 ms first reveal | `bench/storm.csv`, `videos/storm-*.mp4` | ✅ measured |
| P2 | Rock-solid 120 fps on high-refresh Android | 01:00 lines 4–7; Canvas Thrash §8 | 8.3 ms budget; broken ~36 fps → fixed 604 frames in 5 s (120 fps) | `traces/perfetto-system/thrash-trace-all.txt` | ✅ measured |
| P3 | Shift how engineers diagnose, isolate, fix | line 22; lines 23–30 | Thread → event → code → fix → measure, applied to every fix | Canvas Thrash script | ✅ |
| P4 | How Impeller interacts with Vulkan on Android 10+ | 10:30 lines 13–19; Storm §1 | Pipeline and command-buffer slides; log line "Using the Impeller rendering backend (Vulkan)"; Mali-G615, Vulkan 1.3 | `evidence/` | ✅ |
| P5 | How Impeller schedules GPU pipelines | Storm §7–8; line 14 | 40 `PipelineVK::Create` in the reveal frame, 2.2 ms each, on `1.raster`; 30 → 40 as effects triple | `traces/perfetto-system/impeller-144.txt` | ✅ measured |
| P6 | Tessellation of vector paths into triangles | line 16; Canvas Thrash §4 | X-ray triangle lens; path points 129,920 → 12,032; `Encode` 27 → 13 ms | video 0:32–0:59; `thrash-trace-*.txt` | ✅ modelled + measured indirectly |
| P7 | Explicit command buffers under heavy stress | lines 17–18, 25–27 | `SurfaceFrame::Encode` dominates the raster frame; `QueueSubmit` 2 → 1 per frame when layers go | `thrash-trace-none.txt`, `thrash-trace-all.txt` | ⚠️ CPU side measured; GPU execution explained, not traced |
| P8 | Intentionally thrash a real-time canvas | 00:00 line 2; Canvas Thrash §3 | Dial 1× → 8×, both lanes red | `videos/thrash-impeller-stage.mp4` 0:00–0:32 | ✅ |
| P9 | Parse advanced DevTools Timeline traces | 13:00 line 21; lines 28–29 | Dart timeline (the events DevTools' Performance page reads) with named `KILN::Thrash::*` spans, opened in Perfetto | `traces/dart-timeline/*.perfetto-trace` | ⚠️ same data, shown in Perfetto, not the DevTools UI |
| P10 | Interpret Systrace / Perfetto metrics | lines 23–27 | Main and `1.raster` slices, thread state (running vs sleeping), `saveLayer` and `QueueSubmit` counts | `traces/perfetto-system/` | ✅ |
| P11 | Precise repaint boundary isolation | Canvas Thrash §7; line 29 | Grid repaints → 0/s; `KILN::Thrash::grid` absent from the timeline; UI 4.4 → 3.4 ms | `devtools-timeline-8x-isolate.perfetto-trace` | ✅ measured |
| P12 | Layer complexity reduction | Canvas Thrash §6; line 25 | Layers 64 → 0; raster 13.7 → 6.6 ms; `saveLayer` 64 → 0 per frame in the trace | `thrash-trace-simplifyPaths+batchDraws.txt` vs `-all.txt` | ✅ measured |
| P13 | Confidence to ship | lines 30–33 | Medians with ranges, honest limits, scripts to reproduce | `bench/`, `tool/benchmark/` | ✅ |
| T1 | Skia JIT vs Impeller AOT pipeline mechanics on Vulkan | Storm; lines 13–14 | 118 Skia programs vs 40 Impeller pipelines in one reveal frame | `skia-144.txt`, `impeller-144.txt` | ✅ measured |
| T2 | Read ~4 ms UI / ~4 ms raster allocations | lines 4–7; Canvas Thrash §8 | Fixed: UI 3.4 ms (under 4), raster 6.5 ms (under 8.3, over 4) | `bench/thrash-impeller.csv` | ✅ honest: raster ends between the target and the limit |
| T3 | Custom painter patterns, precompiled pathways, avoid `saveLayer()` | Canvas Thrash §4–7; line 36 | Decimated cached paths, one `drawVertices`, gradient glow instead of `saveLayer` + blur | `thrash_canvas.dart`; bench | ✅ (no custom fragment shader in this talk) |

## Gaps, said out loud

| Gap | Why | What the talk does instead |
|---|---|---|
| GPU execution (render passes on the Mali GPU) | The phone's driver exposes only GPU memory to Perfetto | Line 32 says so; render-pass cost is explained from the Vulkan model |
| DevTools UI walkthrough | No phone on stage to attach DevTools to | The same Dart timeline events, opened in Perfetto (lines 28–29). A live DevTools demo needs any device or emulator attached |
| Raster at 6.5 ms is over the 4 ms raster target | Measured | Say it: inside the 8.3 ms frame, at 120 fps, with less headroom than four and four |
| Batch draws is a small win | Measured: 18.6 → 13.7 ms, overlapping ranges | The script calls it the smallest win of the four |

## Wording guardrails for the abstract's claims

The abstract uses some shorthand. These are the precise versions to say on stage.

| Abstract says | Say on stage | Why |
|---|---|---|
| "~4ms UI / ~4ms Raster" | "UI means Dart frame work on the platform main thread; Raster means Impeller work on `1.raster`. Target about 4 ms each so the frame lands within one refresh. Each can stretch to 8.33 ms without dropping, but you lose latency and headroom." | DevTools labels phases as UI/Raster; main and raster are the actual CPU threads, and consecutive frames pipeline ([Frame scheduling](../notes/05-frame-scheduling.md)) |
| "Skia's JIT shader compilation" | "Skia generated and compiled shaders just in time, during frames" | Skia generated SkSL at runtime; the driver compiled it on first use |
| "Impeller's AOT pipeline mechanics" | "Shaders compiled at engine build time; pipelines built from them mostly at startup, and the rest on first use" | Storm measured 40 `PipelineVK::Create` inside the 144-tile reveal frame, about 2 ms each: cheap, not zero |
| "Skia JIT versus Impeller AOT on Vulkan" | "The Skia comparison demonstrates first-use generation on OpenGL ES; the following segment explains Impeller's AOT pipeline mechanics on Vulkan" | Do not imply that both comparison APKs use the same graphics backend |
| "Prevent frame drops under heavy stress" | "Keep the recorded work small enough that the raster thread finishes inside its budget" | Command buffers don't prevent drops by themselves; less recorded work does |
| "Android Systrace" | "Systrace, now Perfetto" | Perfetto replaced Systrace in Android 10 and opens Systrace files |
| "Precise repaint boundary isolation" | "Isolate what repaints; Impeller still rasterizes the frame" | Impeller has no raster cache |
| "Maximize pre-compiled rendering pathways" | "Prefer draws Impeller already has a precompiled path for, like one `drawVertices` or a gradient fill, over offscreen layers; then measure" | Precompiled shaders remove runtime shader generation; they do not make expensive canvas work free |
| "Manages explicit command buffers" (GPU side) | "This trace shows the CPU side of the GPU: encoding and submissions" | This phone exposes no GPU render stages to Perfetto |
