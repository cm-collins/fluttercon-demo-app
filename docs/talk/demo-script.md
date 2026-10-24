# Demo script

Line by line: what is on screen, what you do, and what you say. Quoted lines are the
intended wording; say them in your own voice, but keep the facts exactly as written (see
[Say it precisely](#say-it-precisely)).

**Before the session:** follow the [Stage runbook](stage-runbook.md) setup checklist.
All pit stops start **off** (broken). Deep-link commands are pasted in a terminal tab.

## How to read this script

- **Screen** is what the audience sees: `Phone` (mirrored), `Slide n`, `DevTools` or `Perfetto`.
- **Do** is your action. Commands run on the laptop.
- **Say** is the line. About 130 words per minute; each segment fits its time box.
- ⏱ marks where you should be. If you are more than a minute late, use the cut noted there.

## Run of show

| Time | Segment | Length |
|---|---|---|
| 00:00 | Lights Out | 1:30 |
| 01:30 | The budget | 1:30 |
| 03:00 | How we got here (history) | 2:30 |
| 05:30 | Paint call to GPU | 2:30 |
| 08:00 | Threads and tools in 2026 | 2:00 |
| 10:00 | Rosetta | 2:00 |
| 12:00 | Lap 1: Telemetry Duel | 6:00 |
| 18:00 | Lap 2: Speed Ribbon | 6:00 |
| 24:00 | Lap 3: Pit Wall | 6:00 |
| 30:00 | Lap 4: Race Control | 3:00 |
| 33:00 | Chequered flag | 2:00 |
| 35:00 | Takeaways | 1:00 |
| 36:00 | Q&A | 4:00 |

## Pit stops used on stage

| Label on the phone | Pit stop ID | What the fix really does |
|---|---|---|
| Decimate telemetry paths | `duel-paths` | At most two samples per pixel column, path built once per size, cursor in its own painter |
| One-draw speed ribbon | `ribbon-vertices` | One `drawVertices` mesh with per-vertex colours instead of ~5,000 `drawPath` calls |
| Fade tower without saveLayer | `tower-fade` | Fade leaf colours, rounded `BoxDecoration` instead of `Opacity` and a save-layer clip |
| Group the glass blur | `glass-group` | `BackdropGroup` with `BackdropFilter.grouped` |
| Separate track layers | `map-layers` | Static circuit behind a `RepaintBoundary`, cars in a light painter |
| Decode off the main thread | `feed-isolate` | `Isolate.run` once, cached results |

---

## 00:00 — Lights Out (1:30)

| # | Screen | Do | Say |
|---|---|---|---|
| 1 | Slide 1 (title) | Walk to centre. | "Hi, I'm … Let's start with a race." |
| 2 | Phone | Launch Kiln. Lights Out runs, then Pit Wall. | *(Silence for about 10 seconds. Let the room watch.)* |
| 3 | Phone | Point at the track map. | "This is a real Formula 1 race, replayed from public telemetry. Twenty cars, live timing, glass cards." |
| 4 | Phone | Pause. | "It looks smooth. It's lying to you." |

## 01:30 — The budget (1:30)

| # | Screen | Do | Say |
|---|---|---|---|
| 5 | Phone | Swipe up the Engine Room. Bars are red and yellow. | "This is the Engine Room. It measures every frame the app draws." |
| 6 | Phone | Point at the renderer badge. | "First, the badge: Impeller on Vulkan, 120 hertz. Keep an eye on that. On some phones Flutter deliberately uses OpenGL ES instead." |
| 7 | Slide 3 | — | "The car data arrives about 3.7 times a second. This screen refreshes 120 times a second. That's about 32 frames between data points, and each frame gets 8.33 milliseconds." |
| 8 | Phone | Point at the three numbers. | "Three numbers. UI is our Dart work. Raster is Impeller. Total is vsync to finished frame. Red means we missed the deadline." |
| 9 | Phone | — | "By the end of this talk, every one of these frames will be on time. First, how we got here." |

## 03:00 — How we got here (2:30)

Source: [History overview](../history/README.md) and [Rendering engine history](../history/01-rendering-engine.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 10 | Slide 4 (timeline) | — | "The title says 'Beyond Skia', so: what are we beyond?" |
| 11 | Slide 4 | Point at 2018. | "Flutter 1.0 shipped in December 2018 on Skia, the same 2D engine behind Chrome and Android's own UI." |
| 12 | Slide 4 | — | "Skia generated GPU shaders while your app was running. The first time a new effect appeared, the driver compiled a shader on the raster thread, and that frame was late." |
| 13 | Slide 5 (Skia clip) | Play the 30-second first-run clip. | "Watch the first transition. That stutter happens once per shader, per install. You never saw it in development." |
| 14 | Slide 4 | Point at 2020. | "In 2020 we got SkSL warm-up: record the shaders on one device, bundle them, and hope they match your user's GPU driver. It helped. It never scaled." |
| 15 | Slide 4 | Point at 2023 to 2025. | "So the team built a new renderer. Impeller became the default on iOS in May 2023, and on Android Vulkan devices in December 2024." |
| 16 | Slide 4 | — | "Since Flutter 3.29, in February 2025, Skia is gone from iOS. On Android, phones without a working Vulkan driver fall back to Impeller's own OpenGL ES backend, not to Skia." |
| 17 | Slide 4 | — | "Skia wasn't slow. It was unpredictable. And at 120 hertz, unpredictable is worse than slow." |

## 05:30 — Paint call to GPU (2:30)

Source: [Impeller internals](../notes/03-impeller-internals.md) and [Vulkan primer](../notes/04-vulkan-primer.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 18 | Slide 6 (pipeline) | — | "Here is what Impeller does with your paint call." |
| 19 | Slide 6 | Point at shaders. | "Every shader is compiled when the engine is built. At runtime Impeller only picks an existing pipeline. That's the stutter, gone." |
| 20 | Slide 6 | Point at DisplayList. | "Your `paint()` method doesn't draw. It records a DisplayList." |
| 21 | Slide 6 | Point at tessellation. | "On the raster thread, Impeller turns every path into triangles on the CPU. Curves are flattened, shapes are triangulated." |
| 22 | Slide 6 | Point at render pass. | "Those triangles go into Vulkan render passes and command buffers, and the queue sends them to the GPU." |
| 23 | Slide 6 | — | "Two things Impeller does not do. It does not keep a raster cache like Skia did. And it does not make work free. If you ask for more triangles, more draws or more passes, you pay for every one, every frame." |

## 08:00 — Threads and tools in 2026 (2:00)

Source: [Profiling tools history](../history/03-profiling-tools.md) and [Graphics APIs history](../history/02-graphics-apis.md).

| # | Screen | Do | Say |
|---|---|---|---|
| 24 | Slide 7 (threads) | — | "Threads changed too. Since 3.29, your Dart code runs on the platform main thread. There is no separate UI thread any more, although DevTools still labels it 'UI'. Impeller runs on the raster thread." |
| 25 | Slide 7 | — | "And Vulkan isn't just Flutter's choice. Since March 2025 it's Android's official graphics API. Impeller already speaks it directly." |
| 26 | Slide 8 (tools) | — | "The tools grew up as well. Systrace became Perfetto in Android 10. Observatory became DevTools, and since 2023 the DevTools timeline *is* Perfetto." |
| 27 | Slide 8 | — | "So a Flutter developer and an Android platform engineer can now read the same trace. That's how we'll work today: DevTools first, Perfetto when we need the whole system." |
| 28 | Slide 9 (method) | — | "One method for every lap: which thread is red, which event, which code. Then one fix, and measure again." |

⏱ **10:00.** If late, shorten the Rosetta segment to lines 29 and 31.

## 10:00 — Rosetta (2:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 29 | Phone | Engine Room → Rosetta tab. | "Kotlin and iOS friends, this tab is for you." |
| 30 | Phone | Point at each row. | "The main thread is the main thread. Our raster thread is your RenderThread on Android, or the render server on iOS. A Flutter `saveLayer` is your offscreen pass." |
| 31 | Phone | — | "Everything you're about to see applies to Compose and SwiftUI too. Only the tool names change." |

## 12:00 — Lap 1: Telemetry Duel (6:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 32 | Slide 10 (lap card) | — | "Lap one. Two drivers, speed and throttle, compared over a lap." |
| 33 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/duel"` | "Smooth? Look at the bars." |
| 34 | DevTools | Performance page. Click one red frame. | "Raster is red. The GPU thread, not our Dart code." |
| 35 | DevTools | Enable Track Paints. Timeline Events → search `KILN::TelemetryDuel`. | "Here's our paint span, and it's long." |
| 36 | DevTools | — | "Every frame we build thousands of curve segments. Impeller flattens every curve and triangulates it on the CPU, on the raster thread. Every single frame." |
| 37 | Phone | Engine Room → **Decimate telemetry paths** on. | "Pit stop." |
| 38 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://replay"` | "Replay the same five seconds." |
| 39 | DevTools | Point at the raster bars dropping. | "Same picture. A trace 400 pixels wide never needed 4,000 curves. We keep at most two points per pixel column." |
| 40 | DevTools | — | "Impeller still tessellates it every frame, because there's no raster cache. But now it's a tenth of the work." |

## 18:00 — Lap 2: Speed Ribbon (6:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 41 | Slide 11 (lap card) | — | "Lap two. The track, coloured by speed." |
| 42 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/ribbon"` | "Beautiful, and red again." |
| 43 | Perfetto | Start `record_android_trace` (10 s). Run the replay deep link. | "This time, the whole system. This is Perfetto, the tool that replaced Systrace in Android 10." |
| 44 | Perfetto | Show the app's main thread and `1.raster`. | "Our Dart work on the main thread, and Impeller on the raster thread. Long slices, every frame." |
| 45 | Perfetto | Show Expected vs Actual timeline. | "And this is SurfaceFlinger's verdict: expected frame, actual frame. Late is late, whatever our own counters say." |
| 46 | Perfetto | — | "About five thousand `drawPath` calls. On Vulkan the cost is volume: binding pipelines, buffers and uniforms, then drawing, thousands of times. The engine team's own issue measured about 1,800 Vulkan calls for 285 draws." |
| 47 | Phone | Engine Room → **One-draw speed ribbon** on. Capture again. | "Pit stop: the whole ribbon as one triangle mesh, colour per vertex, one draw call." |
| 48 | Perfetto | Show both traces side by side. | "Same picture. One draw call. Look at the raster slices." |

⏱ **24:00.** If late, skip line 52 in Lap 3.

## 24:00 — Lap 3: Pit Wall (6:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 49 | Slide 12 (lap card) | — | "Lap three. The main screen, with the most premium design and the most hidden cost." |
| 50 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/pitwall"` | — |
| 51 | DevTools + Phone | Turn on the offscreen-layers checkerboard. Tower and glass cards light up. | "Every checkerboard is an offscreen render target, a `saveLayer`. On a phone's tile-based GPU, that means storing the tile memory, switching pass, and loading it back." |
| 52 | Phone | — | "The tower fades rows with `Opacity` and clips them with an anti-aliased save layer. Two offscreen passes per row." |
| 53 | Phone | **Fade tower without saveLayer** on. | "Fade the colours, not the group. Draw the rounded corners as a decoration, not a clip. The checkerboard is gone." |
| 54 | Phone | **Group the glass blur** on. | "Each glass card blurred the screen behind it separately. `BackdropGroup` shares one backdrop pass. It only works when the blurs are identical and the cards don't overlap." |
| 55 | Phone | **Separate track layers** on. | "The circuit never changes. It shouldn't repaint 120 times a second. Now only the cars repaint." |
| 56 | DevTools | Replay. Point at the bars. | "To be honest about this one: `RepaintBoundary` isolates the repaint, but Impeller has no raster cache. The win is less work per frame, not a cached picture." |

## 30:00 — Lap 4: Race Control (3:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 57 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/control"` | "Last lap. Race control messages." |
| 58 | DevTools | Point at the frames chart. | "Which bar is red?" *(Wait for the room: UI.)* "UI. Raster is fine." |
| 59 | DevTools | Show `KILN::RaceControl::decode` inside the build. | "We decode JSON inside `build()`, on the main thread, on every rebuild. Since 3.29, that's the same thread as the platform UI." |
| 60 | Phone | **Decode off the main thread** on. | "Decode once on a background isolate, cache the result. UI is green again." |
| 61 | Phone | — | "Not every jank is GPU jank. Read the bars before you touch the painter." |

## 33:00 — Chequered flag (2:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 62 | Phone | `adb shell am start -a android.intent.action.VIEW -d "kiln://scenario/pitwall"`, then `kiln://pitstop/all/on`, then `kiln://replay` | "All pit stops on. Same five seconds." |
| 63 | Phone | Engine Room turns green and purple. | "Same app. Same data. Same phone. Every frame on time." |
| 64 | Slide 13 (before / after) | — | "Here's the before and after in Perfetto, if you want the proof without trusting my app." |

## 35:00 — Takeaways (1:00)

| # | Screen | Do | Say |
|---|---|---|---|
| 65 | Slide 15 | — | "One: know the engine. Shaders are compiled ahead of time now; your paths become CPU triangles and Vulkan commands." |
| 66 | Slide 15 | — | "Two: diagnose before you fix. Which thread, which event, which code. DevTools first, Perfetto for the system." |
| 67 | Slide 15 | — | "Three: fix surgically, one change at a time, and prove it with numbers." |
| 68 | Slide 16 | — | "Impeller made performance predictable. It didn't make overdraw free. Thank you." |

## 36:00 — Q&A (4:00)

- Keep DevTools and Perfetto open with the exported traces.
- Short answers to the likely questions are in the [Talk outline](talk-outline.md#questions-to-expect).

---

## Say it precisely

Senior engineers will catch loose wording. These are the statements most likely to be
challenged.

| Say | Don't say | Why |
|---|---|---|
| "Impeller has no raster cache" | "RepaintBoundary caches it" | Impeller re-rasterizes every frame; the boundary only isolates repaints |
| "We decimate the path: at most two points per pixel column" | "We cache the path" | The win is less geometry, not caching |
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
| DevTools disconnects | Import the exported snapshot for that lap |
| Perfetto capture fails | Open the pre-recorded trace tab |
| Fixed state is not green on stage | "Thermals. Here's the rehearsal capture." Open the recorded trace. |
| Running over time | Use the ⏱ cuts; if still late, skip Lap 4 and say line 61 only |
| Skia clip will not play | Describe it in one sentence (line 13) and move on |

## Note on the Skia clip

Record the clip before the event. If your Flutter version no longer accepts
`--no-enable-impeller` on Android, record it with an older Flutter release (for example
3.24) on the same phone, and say so on the slide.
