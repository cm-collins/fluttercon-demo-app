# Demo script

Line by line: what is on screen, what you do, and what you say. Quoted lines are the
intended wording; say them in your own voice, but keep the facts exactly as written (see
[Say it precisely](#say-it-precisely)). Every promise in the registered abstract is mapped
to a line here in [Abstract alignment](abstract-alignment.md).

**Before the session:** follow the [Stage runbook](stage-runbook.md) setup checklist.
All pit stops start **off** (broken), Thrash is at **1×**. Deep-link commands are pasted in
a terminal tab.

## How to read this script

- **Screen** is what the audience sees: `Phone` (mirrored), `Slide n`, `DevTools` or `Perfetto`.
- **Do** is your action. Commands run on the laptop.
- **Say** is the line. About 130 words per minute; each segment fits its time box.
- ⏱ marks where you should be. If you are more than a minute late, use the cut noted there.

## Run of show

| Time | Segment | Length | Abstract promise it delivers |
|---|---|---|---|
| 00:00 | Lights Out | 1:30 | Real-time graphics canvas |
| 01:30 | The budget | 1:30 | ~4 ms UI / ~4 ms raster |
| 03:00 | How we got here | 2:30 | Skia JIT vs Impeller AOT |
| 05:30 | One frame on Vulkan | 2:30 | Pipelines, tessellation, explicit command buffers |
| 08:00 | Threads and tools in 2026 | 2:00 | DevTools, Systrace and Perfetto |
| 10:00 | Rosetta | 2:00 | Kotlin and iOS audience |
| 12:00 | Lap 1: Telemetry Duel | 5:00 | Tessellation, DevTools Timeline, custom painters |
| 17:00 | Lap 2: Speed Ribbon, thrashed | 7:00 | Thrash the canvas, Perfetto, command volume, precompiled shaders |
| 24:00 | Lap 3: Pit Wall | 6:00 | `saveLayer`, layer complexity, repaint boundary isolation |
| 30:00 | Lap 4: Race Control | 3:00 | UI half of the budget |
| 33:00 | Chequered flag | 2:00 | Proof |
| 35:00 | Takeaways | 1:00 | The three registered takeaways |
| 36:00 | Q&A | 4:00 | |

## Controls used on stage

| Label on the phone | ID | What it really does |
|---|---|---|
| Thrash 1× / 2× / 4× / 8× | `kiln://thrash/<n>` | Multiplies Speed Ribbon segments and adds a speed trail for every car, so the canvas records far more work per frame |
| Decimate telemetry paths | `duel-paths` | At most two samples per pixel column, path built once per size, cursor in its own painter |
| One-draw speed ribbon | `ribbon-vertices` | One `drawVertices` mesh with per-vertex colours instead of thousands of `drawPath` calls |
| Shader-lit ribbon | `ribbon-shader` | Colour and glow computed by a fragment shader compiled at build time, in the same single draw |
| Glow without saveLayer | `car-glow` | Car glows drawn as radial-gradient circles instead of `canvas.saveLayer` with a blur per car |
| Fade tower without saveLayer | `tower-fade` | Fade leaf colours, rounded `BoxDecoration` instead of `Opacity` and a save-layer clip |
| Separate track layers | `map-layers` | Static circuit behind a `RepaintBoundary`, cars in a light painter |
| Group the glass blur | `glass-group` | `BackdropGroup` with `BackdropFilter.grouped` |
| Decode off the main thread | `feed-isolate` | `Isolate.run` once, cached results |

---

## 00:00 — Lights Out (1:30)

| # | Screen | Do | Say |
|---|---|---|---|
| 1 | Slide 1 (title) | Walk to centre. | "Hi, I'm … Let's start with a race." |
| 2 | Phone | Launch Kiln. Lights Out runs, then Pit Wall. | *(Silence for about 10 seconds. Let the room watch.)* |
| 3 | Phone | Point at the track map. | "This is a real Formula 1 race, replayed from public telemetry. Twenty cars, live timing, glass cards, all drawn on a real-time canvas." |
| 4 | Phone | Pause. | "It looks smooth. It's lying to you." |

## 01:30 — The budget (1:30)

| # | Screen | Do | Say |
|---|---|---|---|
| 5 | Phone | Swipe up the Engine Room. Bars are red and yellow. | "This is the Engine Room. It measures every frame the app draws." |
| 6 | Phone | Point at the renderer badge. | "The badge says Impeller on Vulkan, 120 hertz. That matters: on some phones Flutter deliberately uses OpenGL ES instead." |
| 7 | Slide 3 | — | "The car data arrives about 3.7 times a second. The screen refreshes 120 times a second. Each frame gets 8.33 milliseconds." |
| 8 | Slide 3 | Point at the split. | "Flutter spends that frame on two threads. UI is our Dart code. Raster is Impeller. Budget about 4 milliseconds for each, and the whole frame, from vsync to pixels, lands inside one refresh." |
| 9 | Phone | Point at the 4 ms tick on each bar. | "That's the tick on each bar. Strictly, the threads overlap, so each one can stretch to 8.33 and still hit 120 frames per second. But then you add a frame of latency and you have no headroom left. Four and four is the budget I design for." |
| 10 | Phone | — | "By the end of this talk, both bars will be inside their budget. First, how we got here." |

## 03:00 — How we got here (2:30)

Source: [History overview](../history/README.md) and [Rendering engine history](../history/01-rendering-engine.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 11 | Slide 4 (timeline) | — | "The title says 'Beyond Skia', so: what are we beyond?" |
| 12 | Slide 4 | Point at 2018. | "Flutter 1.0 shipped in December 2018 on Skia, the same 2D engine behind Chrome and Android's own UI." |
| 13 | Slide 4 | — | "Skia compiled shaders just in time. The first time a new effect appeared, Skia generated a shader and the GPU driver compiled it on the raster thread, in the middle of a frame. That frame was late." |
| 14 | Slide 5 (Skia clip) | Play the 30-second first-run clip. | "Watch the first transition. That stutter happens once per shader, per install. You never saw it in development." |
| 15 | Slide 4 | Point at 2020. | "In 2020 we got SkSL warm-up: record the shaders on one device, bundle them, and hope they match your user's GPU driver. It helped. It never scaled." |
| 16 | Slide 4 | Point at 2023 to 2025. | "So the team built a renderer that compiles ahead of time. Impeller became the default on iOS in May 2023, and on Android Vulkan devices in December 2024." |
| 17 | Slide 4 | — | "Since Flutter 3.29, in February 2025, Skia is gone from iOS. On Android, phones without a working Vulkan driver fall back to Impeller's own OpenGL ES backend, not to Skia." |
| 18 | Slide 4 | — | "Skia wasn't slow. It was unpredictable. And at 120 hertz, unpredictable is worse than slow." |

## 05:30 — One frame on Vulkan (2:30)

Source: [Impeller internals](../notes/03-impeller-internals.md) and [Vulkan primer](../notes/04-vulkan-primer.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 19 | Slide 6 (pipeline) | — | "Here's what Impeller does with one frame on Vulkan." |
| 20 | Slide 6 | Point at shaders. | "Every shader is compiled when the engine is built. A pipeline is a shader plus fixed GPU state. Impeller builds its pipelines from those precompiled shaders, mostly at startup, and Vulkan's pipeline cache keeps them. During a frame it only picks one. That's ahead-of-time." |
| 21 | Slide 6 | Point at DisplayList. | "Your `paint()` method doesn't touch the GPU. It records a DisplayList." |
| 22 | Slide 6 | Point at tessellation. | "On the raster thread, Impeller tessellates: every path is flattened and broken into triangles on the CPU. Simple convex shapes take a fast path." |
| 23 | Slide 7 (command buffers) | Point at the record, submit, execute lanes. | "Then it records explicit command buffers: begin render pass, bind pipeline, bind buffers, draw, end. It submits them to the Vulkan queue with a fence and moves on. The GPU executes while the raster thread starts the next frame." |
| 24 | Slide 7 | — | "That's GPU scheduling: the CPU records, the GPU executes, fences keep them in step. Under stress, the risk is no longer compilation. It's the volume of what we record, and every extra render pass we ask for." |
| 25 | Slide 7 | — | "And Impeller doesn't keep a raster cache like Skia did. If we ask for work, we pay for it, every frame." |

## 08:00 — Threads and tools in 2026 (2:00)

Source: [Profiling tools history](../history/03-profiling-tools.md) and [Graphics APIs history](../history/02-graphics-apis.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 26 | Slide 8 (threads) | — | "Since 3.29, your Dart code runs on the platform main thread. DevTools still calls it 'UI'. Impeller runs on the raster thread. Those are our two four-millisecond budgets." |
| 27 | Slide 8 | — | "Vulkan isn't just Flutter's choice. Since March 2025 it's Android's official graphics API, and Impeller speaks it directly." |
| 28 | Slide 9 (tools) | — | "The tools grew up too. Systrace became Perfetto in Android 10; Perfetto still opens Systrace files, and `flutter run --trace-systrace` still sends our events there. Observatory became DevTools, and since 2023 the DevTools timeline *is* Perfetto." |
| 29 | Slide 10 (method) | — | "One method for every lap: which thread is over budget, which event, which code. Then one surgical fix, and measure again." |

⏱ **10:00.** If late, shorten the Rosetta segment to lines 30 and 32.

## 10:00 — Rosetta (2:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 30 | Phone | Engine Room → Rosetta tab. | "Kotlin and iOS friends, this tab is for you." |
| 31 | Phone | Point at each row. | "The main thread is the main thread. Our raster thread is your RenderThread on Android, or the render server on iOS. A Flutter `saveLayer` is your offscreen pass." |
| 32 | Phone | — | "Everything you're about to see applies to Compose and SwiftUI too. Only the tool names change." |

## 12:00 — Lap 1: Telemetry Duel (5:00)

Promise: tessellation, parsing the DevTools Timeline, custom painter patterns.

| # | Screen | Do | Say |
|---|---|---|---|
| 33 | Slide 11 (lap card) | — | "Lap one. Two drivers, speed and throttle, compared over a lap. One custom painter." |
| 34 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/duel"` | "Smooth? Look at the bars." |
| 35 | DevTools | Performance page. Click one red frame. | "Raster is far past its four milliseconds. UI is fine. So it's Impeller's work, not our Dart." |
| 36 | DevTools | Enable Track Paints. Timeline Events → search `KILN::TelemetryDuel`. | "Here's how to read the timeline: the frame, the raster slice, and inside it our named paint span. It's long." |
| 37 | DevTools | — | "Every frame this painter builds thousands of curve segments. Impeller tessellates every one on the CPU, on the raster thread. Every single frame." |
| 38 | Phone | Engine Room → **Decimate telemetry paths** on. | "Pit stop. Three custom-painter rules: draw at screen resolution, build the path once per size, and put the moving cursor in its own painter driven by `repaint:`." |
| 39 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://replay"` | "Replay the same five seconds." |
| 40 | DevTools | Point at the raster bars dropping. | "Same picture. A trace 400 pixels wide never needed 4,000 curves. We keep at most two points per pixel column." |
| 41 | DevTools | — | "Impeller still tessellates it every frame, because there's no raster cache. But now it's a tenth of the triangles." |

## 17:00 — Lap 2: Speed Ribbon, thrashed (7:00)

Promise: intentionally thrash a real-time canvas, read Systrace/Perfetto, command-buffer volume, precompiled pathways.

| # | Screen | Do | Say |
|---|---|---|---|
| 42 | Slide 12 (lap card) | — | "Lap two. The track, coloured by speed. And this time, we thrash it on purpose." |
| 43 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/ribbon"` | "At 1× this is about a thousand segments. Raster is already near its budget." |
| 44 | Phone | Thrash 2×, then 4×, then 8× (or `kiln://thrash/8`). Pause on each step. | "2×… 4×… 8×. Speed trails for all twenty cars. Watch the raster bar climb past four, past eight, into red. That's a stressed canvas." |
| 45 | Perfetto | Start `record_android_trace` (10 s). Run the replay deep link. | "Now the whole system. Perfetto, the successor to Systrace." |
| 46 | Perfetto | Show the app's main thread and `1.raster`. | "Main thread, short slices: UI is inside its four milliseconds. Raster thread: long slices, back to back. It never rests." |
| 47 | Perfetto | Show Expected vs Actual timeline. | "This is SurfaceFlinger's verdict: expected frame, actual frame. Every red one is a dropped frame the user saw." |
| 48 | Perfetto | — | "Thousands of `drawPath` calls means thousands of tessellations, pipeline binds, buffer binds and draws recorded into the command buffer, every frame. On Vulkan the cost is volume. The engine team's own issue measured about 1,800 Vulkan calls for 285 draws." |
| 49 | Phone | Engine Room → **One-draw speed ribbon** on. Keep Thrash at 8×. | "Pit stop: the whole ribbon as one triangle mesh, a colour per vertex, one draw call. Still at 8×." |
| 50 | Phone + Perfetto | Capture again. Show both traces side by side. | "Same picture, same stress. One draw. The raster thread has room to breathe again." |
| 51 | Phone | **Shader-lit ribbon** on. | "Now make it more beautiful, not slower. This glow is a fragment shader, compiled at build time with the engine's own compiler. Still one draw, and nothing compiled at runtime. That's Impeller's precompiled pathway working for us." |
| 52 | Phone | Thrash back to 1×. | "Rule: let the GPU do per-pixel work in one draw, instead of asking the CPU for thousands of draws." |

⏱ **24:00.** If late, skip line 59 (glass) in Lap 3.

## 24:00 — Lap 3: Pit Wall (6:00)

Promise: avoid `saveLayer()`, reduce layer complexity, precise repaint boundary isolation.

| # | Screen | Do | Say |
|---|---|---|---|
| 53 | Slide 13 (lap card) | — | "Lap three. The main screen: the most premium design, and the most hidden cost." |
| 54 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/pitwall"` | — |
| 55 | DevTools + Phone | Turn on the offscreen-layers checkerboard. Car dots, tower and glass cards light up. | "Every checkerboard is a `saveLayer`: an offscreen render target. On a phone's tile-based GPU that means storing tile memory, switching render pass, and loading it back." |
| 56 | Phone | **Glow without saveLayer** on. | "This one is inside a custom painter. Each car's glow called `canvas.saveLayer` with a blur. Twenty cars, twenty offscreen passes. Now each glow is a circle with a radial gradient: same look, no layer." |
| 57 | Phone | **Fade tower without saveLayer** on. | "The tower faded whole rows with `Opacity` and clipped them with an anti-aliased save layer. Fade the colours, not the group. Draw rounded corners as a decoration, not a clip. Checkerboard gone." |
| 58 | DevTools | Track Paints on. **Separate track layers** on. Replay. | "Now repaint isolation. Before: the circuit painted 120 times a second, because it shared a painter with the cars. After: look at the paint events. Only the cars repaint. The circuit sits behind its own `RepaintBoundary`." |
| 59 | Phone | **Group the glass blur** on. | "Last: each glass card blurred the screen separately. `BackdropGroup` shares one backdrop pass, as long as the blurs are identical and the cards don't overlap." |
| 60 | DevTools | Point at the raster bar. | "To be precise about boundaries: `RepaintBoundary` limits *what* repaints. Impeller still rasterizes the frame. The win is fewer layers and less work, not a cached picture." |

## 30:00 — Lap 4: Race Control (3:00)

Promise: the UI half of the ~4 ms / ~4 ms budget.

| # | Screen | Do | Say |
|---|---|---|---|
| 61 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/control"` | "Last lap. Race control messages." |
| 62 | DevTools | Point at the frames chart. | "Which bar is over budget?" *(Wait for the room: UI.)* "UI. Raster is fine." |
| 63 | DevTools | Show `KILN::RaceControl::decode` inside the build. | "We decode JSON inside `build()`, on the main thread, on every rebuild. Since 3.29, that's the same thread as the platform UI." |
| 64 | Phone | **Decode off the main thread** on. | "Decode once on a background isolate, cache the result. UI is back under four milliseconds." |
| 65 | Phone | — | "Not every jank is GPU jank. Read the bars before you touch the painter." |

## 33:00 — Chequered flag (2:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 66 | Phone | `kiln://scenario/pitwall`, then `kiln://pitstop/all/on`, then `kiln://thrash/4`, then `kiln://replay` | "Every pit stop on. And let's leave the stress at 4×." |
| 67 | Phone | Engine Room: both bars inside their ticks, green and purple. | "Same app. Same data. Same phone. Under stress, both threads inside their budget. Every frame on time." |
| 68 | Slide 14 (before / after) | — | "Here's the before and after in Perfetto, if you want the proof without trusting my app." |

## 35:00 — Takeaways (1:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 69 | Slide 16 | — | "One: demystify the engine. Skia compiled shaders just in time; Impeller compiles ahead of time and turns your paths into triangles and explicit Vulkan command buffers." |
| 70 | Slide 16 | — | "Two: profile low-level. Read the budget as about four milliseconds UI and four raster. DevTools for the frame, Systrace and Perfetto for the system." |
| 71 | Slide 16 | — | "Three: tame your custom painters. Use the precompiled pathways, cut draw calls, isolate repaints precisely, and avoid `saveLayer`." |
| 72 | Slide 17 | — | "Impeller made performance predictable. It didn't make overdraw free. Thank you." |

## 36:00 — Q&A (4:00)

- Keep DevTools and Perfetto open with the exported traces.
- Short answers to the likely questions are in the [Talk outline](talk-outline.md#questions-to-expect).

---

## Say it precisely

Senior engineers will catch loose wording. These are the statements most likely to be
challenged.

| Say | Don't say | Why |
|---|---|---|
| "Budget about 4 ms UI and 4 ms raster for single-frame latency" | "Each thread must be under 4 ms or the frame drops" | Threads pipeline; each can reach 8.33 ms at 120 Hz without dropping, at the cost of latency and headroom |
| "Impeller has no raster cache" | "RepaintBoundary caches it" | Impeller rasterizes every frame; the boundary only isolates repaints |
| "We decimate the path: at most two points per pixel column" | "We cache the path" | The win is less geometry, not caching |
| "Impeller builds pipelines from precompiled shaders, mostly at startup" | "Impeller never compiles anything at runtime" | The Vulkan driver still turns pipelines into GPU code when they are created; no new shaders are generated mid-frame |
| "Command buffers are recorded on the raster thread and executed by the GPU asynchronously" | "Impeller renders on the GPU thread" | Flutter has no GPU thread; the raster thread records and submits |
| "Without working Vulkan, Flutter uses Impeller's OpenGL ES backend" | "It falls back to Skia" | Skia is no longer the Android fallback since 3.29 |
| "Dart runs on the platform main thread since 3.29; DevTools calls it UI" | "The UI thread" as a separate thread | The threads were merged in 3.29 |
| "BackdropGroup works when blurs are identical and cards don't overlap" | "BackdropGroup makes blur cheap" | Grouping has strict conditions |
| "Impeller is more predictable" | "Impeller is always faster" | Some effects measured slower than on Skia |
| "Vulkan cost is the volume of calls" | "Vulkan is slow" | Vulkan removes hidden driver work and exposes your call count instead |
| "SkSL warm-up helped but didn't scale" | "Warm-up never worked" | It gave real 2 to 5 times improvements in 2020 |

## Fallback cues

| If… | Then… |
|---|---|
| Badge shows **Impeller · OpenGL ES** | Switch to the spare phone. If both do, present the Vulkan parts from recordings and say why: "Flutter keeps some chips on OpenGL ES on purpose." |
| Thrash 8× freezes the phone | Drop to 4×; the point is the climb, not the maximum |
| DevTools disconnects | Import the exported snapshot for that lap |
| Perfetto capture fails | Open the pre-recorded trace tab |
| Fixed state is not inside budget on stage | "Thermals. Here's the rehearsal capture." Open the recorded trace. |
| Running over time | Use the ⏱ cuts; if still late, skip Lap 4 and say line 65 only |
| Skia clip will not play | Describe it in one sentence (line 14) and move on |

## Note on the Skia clip

Record the clip before the event. If your Flutter version no longer accepts
`--no-enable-impeller` on Android, record it with an older Flutter release (for example
3.24) on the same phone, and say so on the slide.
