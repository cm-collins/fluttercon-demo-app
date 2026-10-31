# Demo script

The run of show for the 40-minute talk: what is on screen, what you do, and what you say.
Quoted lines are the intended wording; say them in your own voice, but keep the facts exactly
as written (see [Say it precisely](#say-it-precisely)). The two demo segments have their own
line-by-line scripts:

- [Shader Storm script](shader-storm-script.md): Skia JIT vs Impeller AOT, first use.
- [Canvas Thrash script](canvas-thrash-script.md): drawing cost on Impeller, four fixes.

Every promise in the registered abstract is mapped to a moment here in
[Abstract alignment](abstract-alignment.md). Term definitions: [Talk vocabulary](vocabulary.md).

**Stage setup: no phone.** Both demos play from recordings made on the stage phone, and the
trace walkthrough opens the traces captured in the same session. Everything lives in
`~/fluttercon-captures/2026-10-31-infinix-x6873/` (see its README). Before the session, follow
the [Stage runbook](stage-runbook.md). If a phone becomes available, run the demo segments
live from their scripts and keep the recordings as fallback.

**Measured on:** Infinix X6873 · Mali-G615 MC6 · Vulkan 1.3 · Android 16 · 120 Hz · Flutter
3.47.8, profile builds. Say this once, early, and put it on the evidence slides.

## How to read this script

- **Screen** is what the audience sees: `Slide`, `Video` (a file from `videos/`) or
  `Perfetto` (a trace open in ui.perfetto.dev).
- **Do** is your action on the laptop.
- **Say** is the line. About 130 words per minute; each segment fits its time box.
- ⏱ marks where you should be. If you are more than a minute late, use the cut noted there.

## Run of show

| Time | Segment | Length | Abstract promise it delivers |
|---|---|---|---|
| 00:00 | Cold open | 1:00 | Real-time graphics canvas, under stress |
| 01:00 | The budget | 1:30 | 120 fps; ~4 ms UI / ~4 ms raster |
| 02:30 | How we got here | 2:00 | Definitive transition to Impeller |
| 04:30 | Shader Storm | 6:00 | Skia JIT vs Impeller AOT; how Impeller schedules pipelines |
| 10:30 | One frame on Vulkan | 2:30 | Pipelines, tessellation, explicit command buffers |
| 13:00 | Threads and tools | 2:00 | DevTools Timeline, Systrace / Perfetto |
| 15:00 | Canvas Thrash | 7:00 | Thrash a real-time canvas; repaint isolation; layer reduction; custom painters |
| 22:00 | Your own pre-compiled pathway | 1:00 | Maximize Impeller's pre-compiled rendering pathways |
| 23:00 | Into the traces | 6:00 | Parse timeline traces; read Perfetto; command buffers in a real trace |
| 29:00 | What Impeller didn't fix | 1:30 | Honest limits |
| 30:30 | Takeaways | 1:30 | The three registered takeaways |
| 32:00 | Q&A | 8:00 | |

The schedule leaves 8 minutes for questions. If you run long, Q&A absorbs it.

---

## 00:00 — Cold open (1:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 1 | Slide: title | Walk to centre. | "Hi, I'm … Let me show you a chart." |
| 2 | Video: `thrash-impeller-stage.mp4`, start at **0:19** (8×, broken) | Play about 10 s. Pause on red lanes. | "This is a live market chart in Flutter, on Impeller, on Vulkan, on a 120 hertz phone. Every red bar is a frame that missed its deadline. It's running at about a third of the frame rate the screen can show." |
| 3 | Same, paused | — | "Impeller was supposed to fix jank. It did fix one kind. In the next 30 minutes I'll show you which one, and how to find and fix the kind it didn't." |

## 01:00 — The budget (1:30)

| # | Screen | Do | Say |
|---|---|---|---|
| 4 | Slide: the budget | — | "The screen refreshes 120 times a second. Each frame gets 8.3 milliseconds." |
| 5 | Slide: the budget | Point at the split. | "Flutter spends that frame on two threads. UI is our Dart code. Raster is Impeller. Budget about 4 milliseconds for each, and the whole frame, from vsync to pixels, lands inside one refresh." |
| 6 | Slide: the budget | — | "Strictly, the threads overlap, so each can stretch to 8.3 and still hit 120. But then you add a frame of latency and have no headroom left. Four and four is the budget I design for." |
| 7 | Slide: the budget | Point at the two lanes in the screenshot. | "Both demo screens show those two lanes. One bar per frame, green under budget, red over." |

## 02:30 — How we got here (2:00)

Source: [History overview](../history/README.md), [Rendering engine history](../history/01-rendering-engine.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 8 | Video: [`skia-to-impeller-concept.mp4`](media/skia-to-impeller-concept.mp4) | Full screen, ~15 s. | *(Mostly silence.)* Then: "That's the idea. Skia forged parts mid-race. Impeller fires them in the kiln first." |
| 9 | Slide: timeline | Point at 2018. | "Flutter 1.0 shipped in 2018 on Skia, the same 2D engine behind Chrome and Android's own UI. Skia compiled shaders just in time: the first time a new effect appeared, it generated a shader and the driver compiled it on the raster thread, in the middle of a frame." |
| 10 | Slide: timeline | Point at 2020. | "In 2020 we got SkSL warm-up: record shaders on one device, bundle them, hope they match your user's driver. It helped. It never scaled." |
| 11 | Slide: timeline | Point at 2023 to 2025. | "So the team built a renderer that compiles ahead of time. Impeller became the default on iOS in 2023 and on Android Vulkan devices in December 2024. Since 3.29, phones without working Vulkan fall back to Impeller's OpenGL ES backend, not to Skia." |
| 12 | Slide: timeline | — | "Skia wasn't slow. It was unpredictable. At 120 hertz, unpredictable is worse than slow. Let's measure it." |

## 04:30 — Shader Storm (6:00)

Run [Shader Storm script](shader-storm-script.md) sections 1 to 10, with these screens:

| Script section | Screen |
|---|---|
| 1–2 (the phone, the screen) | Slide: renderer evidence (the two log lines), then `storm-skia-144.mp4` paused at 0:00–0:08 |
| 4 (Skia, cold) | `storm-skia-144.mp4` from the reveal (~0:10): **1,954 ms** in the recording, 1,863 ms median |
| 5–6 (Skia repeat, trace) | Same video to the repeat (**21 ms**), then the Skia trace slide |
| 7–8 (Impeller) | `storm-impeller-144.mp4`: reveal **148 ms**, repeat **39 ms**; then the Impeller trace slide |
| 9 (scoreboard) | Slide: Storm medians |

Say once, at the first video: *"These are recordings from the stage phone; the numbers on
the scoreboard are medians of three clean runs without recording."*

⏱ **10:30.**

## 10:30 — One frame on Vulkan (2:30)

Source: [Impeller internals](../notes/03-impeller-internals.md), [Vulkan primer](../notes/04-vulkan-primer.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 13 | Slide: shaders → pipelines → triangles | — | "Here's what Impeller does with one frame on Vulkan." |
| 14 | Same | Point at shaders. | "Every shader is compiled when the engine is built. A pipeline is a shader plus fixed GPU state. Impeller builds pipelines from those precompiled shaders, mostly at startup; the ones it meets later it builds on first use, two milliseconds each, as you just saw." |
| 15 | Same | Point at DisplayList. | "Your `paint()` method doesn't touch the GPU. It records a DisplayList." |
| 16 | Same | Point at tessellation. | "On the raster thread, Impeller tessellates: every path is broken into triangles on the CPU. Simple convex shapes take a fast path." |
| 17 | Slide: command buffers | Point at record, submit, execute. | "Then it records explicit command buffers: begin a render pass, bind a pipeline, bind buffers, draw, end. It submits them to the Vulkan queue and moves on. The GPU executes while the raster thread starts the next frame." |
| 18 | Same | — | "That's GPU scheduling: the CPU records, the GPU executes, fences keep them in step. Under stress the risk is no longer compilation. It's the volume of what we record, and every extra render pass we ask for." |
| 19 | Same | — | "And Impeller has no raster cache. Whatever we ask it to draw, it draws every frame." |

## 13:00 — Threads and tools (2:00)

Source: [How Flutter runs](../notes/01-how-flutter-runs.md), [Frame scheduling](../notes/05-frame-scheduling.md), [Profiling tools history](../history/03-profiling-tools.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 20 | Slide: threads | — | "Three names, two CPU threads. Since 3.29, Dart animation, build, layout and paint run on the platform main thread; DevTools labels that work 'UI'. Impeller prepares GPU work on the raster thread, `1.raster` in Perfetto. The GPU is hardware downstream, not a third Flutter thread." |
| 21 | Slide: tools | — | "Perfetto replaced Systrace in Android 10, and still opens Systrace files. DevTools' Performance page shows the Dart timeline, and embeds a Perfetto viewer for it." |
| 22 | Slide: method | — | "One method for everything that follows: which thread is over budget, which event, which code. One surgical fix. Measure again." |

⏱ **15:00.**

## 15:00 — Canvas Thrash (7:00)

Run [Canvas Thrash script](canvas-thrash-script.md) sections 1 to 8 over
`thrash-impeller-stage.mp4`. Pause the video at each step while you talk; the timestamps
below are where each step begins.

| Script section | Video position |
|---|---|
| 1–2 (calm, 1×) | 0:00 |
| 3 (break it) | 0:08 2×, 0:14 4×, **0:19 8×** |
| 4 (Simplify paths, X-ray) | 0:32 X-ray on, 0:43 off, **0:48** Simplify paths |
| 5 (Batch draws) | 0:59 |
| 6 (Glow without layers) | 1:08 |
| 7 (Isolate repaints) | 1:20 |
| 8 (the point) | 1:20 onward, then Slide: Canvas Thrash medians |

Skip the script's hand-off line (section 9); the next segment is the hand-off.

⏱ **22:00.**

## 22:00 — Your own pre-compiled pathway (1:00)

Source: [07 · Optimisation patterns, §6](../notes/07-optimization-patterns.md#6--use-precompiled-fragment-shaders).
Code: [`depth_fill.frag`](../../packages/shader_lab/shaders/depth_fill.frag),
[`pubspec.yaml`](../../packages/shader_lab/pubspec.yaml),
[`depth_chart.dart`](../../packages/shader_lab/lib/src/widgets/depth_chart.dart).

| # | Screen | Do | Say |
|---|---|---|---|
| P1 | Slide: your own pre-compiled pathway | — | "One more pattern, for the 'pre-compiled' part. Everything Impeller drew in both demos, gradients, blurs, blend modes, ran on shaders compiled when the engine was built. Your own effects can join that path." |
| P2 | Same | Point at the three code panels, left to right. | "Write a fragment shader. List it under `shaders:` in pubspec. Load it once with `FragmentProgram.fromAsset`, keep the `FragmentShader`, and only set uniforms in `paint()`. One draw call, any procedural effect, no layer." |
| P3 | Same | Point at the bundle strip at the bottom. | "And here's what the build did with this 500-byte file: a 4-kilobyte bundle. SPIR-V for Vulkan. GLSL for Impeller's OpenGL backend. And SkSL for Skia, as source text, which Skia still compiles on the phone the first time it's drawn. That's the Shader Storm problem again. Impeller uses the compiled form and only builds a pipeline. Same file, two engines: the whole talk in one asset." |

**Slide content** (condensed from the real files; keep the uniform order):

```glsl
// shaders/depth_fill.frag
#include <flutter/runtime_effect.glsl>
uniform vec2 uSize;
uniform float uBid;
out vec4 fragColor;
void main() {
  vec2 uv = FlutterFragCoord().xy / uSize;
  fragColor = vec4(mix(ask, bid, uBid) * (0.35 + 0.65 * uv.x), 1.0);
}
```

```yaml
# pubspec.yaml
flutter:
  shaders:
    - shaders/depth_fill.frag
```

```dart
// Once, before it is needed
final program = await FragmentProgram.fromAsset(
    'packages/shader_lab/shaders/depth_fill.frag');
final shader = program.fragmentShader();

// Every paint: uniforms only, one draw
shader..setFloat(0, size.width)..setFloat(1, size.height)..setFloat(2, 1);
canvas.drawPath(depth, Paint()..shader = shader);
```

Bottom strip: **503 B of GLSL → 4,008 B in the APK: SPIR-V (Impeller · Vulkan) · GLSL ES
(Impeller · OpenGL ES) · SkSL (Skia: compiled on the device, at first use)**.

⏱ **23:00.** If late, cut line 27 below.

## 23:00 — Into the traces (6:00)

Open these in ui.perfetto.dev **before** the talk, one tab each (see the runbook). All from
`traces/` in the captures folder.

| # | Screen | Do | Say |
|---|---|---|---|
| 23 | Perfetto: `perfetto-system/thrash-trace-none.txt` | Pin the app's main thread and `1.raster`. Zoom to 3–4 frames. | "This is the broken chart at 8×, as the system sees it. Here's the main thread, the work DevTools calls UI. And here's `1.raster`: long slices, back to back. It never rests." |
| 24 | Same | Click one `GPURasterizer::Draw` slice, expand to `SurfaceFrame::Encode`. | "Each raster frame is 28 milliseconds, and 27 of them are this: `Encode`. That's Impeller turning our DisplayList into triangles and command buffers, on the CPU." |
| 25 | Same | Search `Canvas::saveLayer`, then `QueueSubmit`. | "Sixty-four `saveLayer` per frame, our glowing dots. And two queue submissions per frame. Those are the explicit command buffers going to the GPU." |
| 26 | Same | Select a frame on `1.raster`; show the thread-state track (Running vs Sleeping). | "And the thread state: running. Not sleeping, not waiting for the GPU. On this phone, the cost is the CPU preparing the frame." |
| 27 | Perfetto: `perfetto-system/thrash-trace-all.txt` | Same zoom. | "All four fixes. Four point eight milliseconds a frame, zero layers, one submission, and 604 frames in five seconds: 120 frames a second." |
| 28 | Perfetto: `dart-timeline/devtools-timeline-8x-broken.perfetto-trace` | Search `KILN::Thrash`. | "This is the Dart timeline, the same events DevTools' Performance page reads, with paint tracking on. Our painters are named: `grid`, `strip`, `lines`, `dots`. The grid paints every frame." |
| 29 | Perfetto: `dart-timeline/devtools-timeline-8x-isolate.perfetto-trace` | Search `KILN::Thrash::grid`. | "Isolate repaints on. Search for the grid: nothing. That's what a precise repaint boundary looks like in a trace: the event that shouldn't be there is gone." |
| 30 | Slide: before / after | — | "So the method: the frame chart says which thread. The trace says which event. Your own named spans say which code." |

## 29:00 — What Impeller didn't fix (1:30)

| # | Screen | Do | Say |
|---|---|---|---|
| 31 | Slide: honest limits | — | "Three honest notes. First: not every fix helped on its own. Isolate repaints did nothing while 130,000 points were the problem. Fix the big cost first." |
| 32 | Same | — | "Second: I can show you the CPU side of the GPU, the encoding and the submissions. What the Mali GPU did with them, this phone's driver doesn't expose to Perfetto. The render-pass cost on the GPU is the model, not my trace." |
| 33 | Same | — | "Third: if you're wondering whether Skia would cope better. Same phone, same chart: 188 milliseconds a frame broken, 58 with every fix. Impeller made this workload possible. It didn't make it free." |

## 30:30 — Takeaways (1:30)

| # | Screen | Do | Say |
|---|---|---|---|
| 34 | Slide: takeaways | — | "One: demystify the engine. Skia compiled shaders just in time, in the frame. Impeller compiles them ahead of time, builds pipelines from them, tessellates your paths into triangles on the CPU and records explicit Vulkan command buffers." |
| 35 | Same | — | "Two: profile low-level. Read the budget as about four milliseconds UI and four raster. DevTools for the frame, Perfetto for the system." |
| 36 | Same | — | "Three: tame your custom painters. Fewer points, fewer draws, no `saveLayer` you don't need, repaint boundaries where they save real work, and your own effects as build-time shaders. Prove every fix with numbers." |
| 37 | Slide: closing | — | "Impeller made performance predictable. It didn't make expensive work free. Thread, event, code, fix, measure. Thank you." |

## 32:00 — Q&A (8:00)

- Keep the Perfetto tabs and the evidence slides ready.
- Answers to likely questions: [Shader Storm script](shader-storm-script.md),
  [Canvas Thrash script](canvas-thrash-script.md#questions-to-expect),
  [Talk outline](talk-outline.md#questions-to-expect).
- Kotlin and iOS questions: [Rosetta](../reference/rosetta.md).

---

## Say it precisely

Senior engineers will catch loose wording. These are the statements most likely to be
challenged.

| Say | Don't say | Why |
|---|---|---|
| "Budget about 4 ms UI and 4 ms raster for single-frame latency" | "Each thread must be under 4 ms or the frame drops" | Threads pipeline; each can reach 8.3 ms at 120 Hz without dropping, at the cost of latency and headroom |
| "Impeller has no raster cache" | "RepaintBoundary caches it" | Impeller draws every layer every frame; the boundary saves Dart re-recording |
| "We keep at most two points per pixel column" | "We cache the path" | The win is less geometry |
| "Impeller builds pipelines from precompiled shaders, mostly at startup, the rest on first use" | "Impeller never does anything at runtime" | Storm measured 40 pipelines built in the reveal frame, about 2 ms each |
| "A custom `.frag` is precompiled for Impeller; Skia gets SkSL text and compiles it on the device" | "A custom shader means no runtime compilation on any engine" | The APK bundle contains SPIR-V, GLSL ES and SkSL; Skia compiles the SkSL at first use |
| "This is the pattern; we didn't time a custom shader on the phone" | Any millisecond figure for the custom shader | No on-device measurement exists for it |
| "Command buffers are recorded on the raster thread and executed by the GPU asynchronously" | "Impeller renders on the GPU thread" | Flutter has no GPU thread |
| "On this phone the raster thread was CPU-bound" | "The GPU was the bottleneck" | `1.raster` was running 90–98% of every traced frame |
| "The layers cost raster-thread time; the GPU-side cost is the model" | "We measured 64 extra render passes on the GPU" | GPU render stages are not available on this phone |
| "Without working Vulkan, Flutter uses Impeller's OpenGL ES backend" | "It falls back to Skia" | Skia is no longer the Android fallback since 3.29 |
| "Dart runs on the platform main thread since 3.29; DevTools calls it UI" | "The UI thread" as a separate thread | The threads were merged in 3.29 |
| "Impeller is more predictable" | "Impeller is always faster" | In-session repeats were faster on Skia (18 vs 45 ms) |
| "Vulkan cost is the volume of what we record" | "Vulkan is slow" | Vulkan removes hidden driver work and exposes your call count instead |
| "Both APKs use the same Flutter SDK; the Skia flavor opts out of Impeller" | "The Skia app is an old Flutter version" | One SDK removes the biggest confounder |
| "These are recordings from the stage phone; the scoreboard numbers are medians without recording" | "This is live" | No phone on stage; recording adds a little load |

## Fallback cues

| If… | Then… |
|---|---|
| A video won't play | Show the matching slide screenshot and narrate from the script; the numbers are on the slide |
| ui.perfetto.dev won't load (no network) | Use the trace slides (screenshots of lines 23–29). Open the tabs before the talk: once loaded, the page works offline |
| Running over time | Use the ⏱ cuts; then shorten Q&A |
| Someone asks to see it live | "The recordings are from the stage phone; the repo has the scripts to reproduce every number on yours" |
