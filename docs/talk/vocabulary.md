# Talk vocabulary — aligned meanings

One shared language for the talk, the docs and the demo. Each term below matches how we
use it in the [Demo script](demo-script.md) and [Abstract alignment](abstract-alignment.md).
For a short A–Z index, see the [Glossary](../notes/08-glossary.md). For Kotlin and iOS
equivalents, see [Rosetta](../reference/rosetta.md).

```mermaid
flowchart TB
    subgraph dart["Main thread (Dart)"]
        build["build / layout"]
        paint["paint: record DisplayList"]
    end
    subgraph raster["Raster thread (Impeller)"]
        dispatch["replay DisplayList"]
        tess["tessellate paths to triangles"]
        record["record command buffers"]
    end
    subgraph gpu["GPU"]
        exec["execute draws in render passes"]
    end
    build --> paint
    paint --> dispatch
    dispatch --> tess
    tess --> record
    record --> exec
```

---

## One naming rule for the whole talk

> **UI = the Dart frame phase shown by DevTools. Main = the actual platform thread that
> runs that phase in current Flutter. Raster = the separate `1.raster` engine CPU thread.
> GPU = hardware, not a Flutter thread.**

Use **“Dart UI work on the main thread”** when both viewpoints matter. Never introduce a
current “UI thread” as a third thread beside main and raster. A separate `1.ui` thread is
historical, before Flutter 3.29.

## Frame pipeline (say these in order)

| Term | Aligned meaning | In Kiln / on stage |
|---|---|---|
| **Vsync** | The display's refresh tick (every 8.33 ms at 120 Hz). Each tick is a chance to show one new frame. | "Every vsync, we get one shot at 8.33 milliseconds." |
| **Build** | Dart runs your widgets: `build()`, then **layout** (sizes and positions). Measured as `buildDuration` in `FrameTiming`. | Canvas Thrash at 8× broken: building 8,000-point paths in `paint()` puts UI at 15.9 ms. |
| **Paint** | Dart **records** what to draw into a **DisplayList**. It does **not** touch the GPU yet. | "Paint is a shopping list, not the cooking." |
| **Composite** | Flutter builds the **layer tree** (which pieces go on top of which). Still mostly on the main thread. | Offscreen layers and `RepaintBoundary` show up here as separate layers. |
| **Rasterize / raster** | On the **raster thread**, Impeller **replays** the DisplayList, tessellates paths, records **command buffers**, and submits to the GPU. Measured as `rasterDuration`. | Red **Raster** bar = Impeller/GPU-side work, not Dart slowness. |
| **Present** | The finished buffer is handed to **SurfaceFlinger** for the next vsync. | Perfetto **Expected vs Actual** shows if we made it. |
| **Frame budget** | 8.33 ms at 120 Hz for the whole frame. We also talk about **~4 ms UI** and **~4 ms raster** as a single-frame latency target (threads can pipeline; see [Frame scheduling](../notes/05-frame-scheduling.md)). | The UI and RASTER lanes on both demo screens. |
| **Jank** | A frame that **missed the deadline** the user expected. Visible stutter, not just a high number in DevTools. | "Red frame in DevTools; Actual late in Perfetto." |

---

## Draw, path, and custom painters

| Term | Aligned meaning | In Kiln / on stage |
|---|---|---|
| **Draw** (colloquial) | Often overloaded. Be explicit: **record** in Dart (`paint()`), **tessellate + draw** on the raster thread, or **GPU draw** (one entry in a command buffer). | Canvas Thrash: 624 draw calls at 8× broken, 161 fixed. |
| **`Canvas` / `paint()`** | API on the main thread that **appends** operations to the current DisplayList (paths, text, images, layers). | The Canvas Thrash painters: grid, strip, lines, dots. |
| **Path** | A vector shape (lines, curves, fills). Stored as geometry; Impeller **flattens curves** and **triangulates** it on the **CPU** each time that path is rasterized. | Broken duel: huge paths every frame. Fix: **decimate** to screen resolution. |
| **Custom painter** | A widget (`CustomPainter`) whose `paint(Canvas, Size)` runs during the paint phase. Can be driven by `repaint:` so only the painter repaints, not the whole subtree. | Canvas Thrash: the grid in its own painter behind a `RepaintBoundary`. |
| **`drawPath`** | One DisplayList op that becomes tessellation + at least one GPU **draw** (often more internal work). Hundreds of them per frame add up. | Canvas Thrash broken heat strip: one `drawPath` per segment, 480 at 8×. |
| **`drawVertices`** | One DisplayList op: draw a pre-built triangle mesh (positions + colours). One logical **draw call** on the GPU side. | Canvas Thrash, Batch draws: the whole heat strip in one call. |
| **Decimation** | Reducing path complexity (e.g. min/max **two points per pixel column**) before tessellation. | Canvas Thrash, Simplify paths: 129,920 → 12,032 points. Not the same as caching. |

---

## Shaders and compilation

| Term | Aligned meaning | In Kiln / on stage |
|---|---|---|
| **Shader** | A small program that runs on the GPU (vertex + fragment stages). Defines how pixels are coloured, lit, blurred, etc. | Shader Storm: each tile is a different combination of built-in effects. |
| **Shader compilation jank** | Stutter when a **new** shader is **compiled during a frame** (Skia era: generate SkSL, driver compiles GLSL/SPIR-V). Happens on first use, often once per install. | Device Skia clip + concept video metaphor. **Not** "compilation junk." |
| **JIT (shaders)** | Skia: shaders created and compiled **when the app runs**, on first encounter. | "Just in time, mid-race." |
| **AOT (shaders)** | Impeller: shaders compiled by **`impellerc` at engine build time**; app ships SPIR-V/Metal/GLSL ES archives. | Concept video kiln; pipeline slide. |
| **`impellerc`** | Offline compiler: GLSL 4.60 → SPIR-V and backend formats. Same path for engine and app `.frag` files in `pubspec.yaml`. | Impeller's built-in shaders, compiled when the engine is built (Shader Storm). |
| **Pipeline (PSO)** | **Pipeline state object**: shader + fixed GPU state (blend, depth, formats). Impeller selects a **pre-built** pipeline per draw type. Vulkan may still **create** the PSO on first use, but **no new shader source** mid-frame. | Slide 7; say "pick a pipeline," not "compile a shader in the frame." |
| **Runtime compilation (careful)** | Do **not** claim zero driver work. Do claim: **no Skia-style shader generation during `paint()`**. | See [Say it precisely](demo-script.md#say-it-precisely). |
| **Custom fragment shader lifecycle** | Flutter compiles a declared `.frag` asset during the app build. Retain its `FragmentShader` and change only uniforms per frame. Skia can still compile the platform shader while loading, so preload before animation. | Precompiled removes shader generation; it does **not** make extra draws, geometry, layers, blur or asset loading free. |

---

## Layers, `saveLayer`, and repaint isolation

| Term | Aligned meaning | In Kiln / on stage |
|---|---|---|
| **Layer (compositing)** | A slice of the scene tree with its own transform and opacity. Flutter composites layers into the final picture. | Layer tree sent to the raster thread each frame. |
| **`saveLayer()`** | Canvas API: render a group of operations into an **offscreen texture** (new **render pass**), then composite the result. Used internally by `Opacity`, blurs, masks, and explicit painter code. | Canvas Thrash broken glow: one `saveLayer` with a blur per dot, 64 at 8×. |
| **Offscreen pass / render target** | Drawing into memory that is **not** the screen. On tile-based GPUs: **store** tile memory, **switch** pass, **reload** — expensive. | "Every checkerboard is an offscreen target." |
| **Layer complexity** | How many layers, passes, and fullscreen effects (blur, group opacity) the frame needs. Abstract takeaway: **reduce** it. | Canvas Thrash, Glow without layers: 64 layers → 0. |
| **`RepaintBoundary`** | Widget that gives its subtree a **separate layer** so when something repaints, Flutter can limit **which** DisplayLists are rebuilt and sent to raster. | `map-layers`: circuit vs cars. |
| **Repaint isolation** | **Precise** use: only the moving part repaints; static content does not. | Track Paints: circuit events disappear after fix. |
| **Not a cache** | On Impeller, `RepaintBoundary` does **not** skip rasterizing that layer forever. It limits **invalidation**. No **raster cache** like Skia. | Line 60 demo script; Q&A. |
| **`Opacity` widget** | Often creates an **opacity layer** (`saveLayer`). Fading a **group** is expensive. | Not in this talk's demos; explicit `saveLayer` in Canvas Thrash shows the same cost. |
| **Opacity peephole** | Engine optimisation: apply opacity **per draw** when children do not overlap, avoiding a layer. Kiln tower fix goes further: **fade leaf colours** instead. | Not in this talk's demos. |
| **`BackdropFilter`** | Blurs (or filters) **what is already drawn behind** the widget. Each one can trigger reading back the scene and a blur pass. | Broken KPI cards. |
| **`BackdropGroup` / `BackdropFilter.grouped`** | Share **one** backdrop sampling pass for several filters. Requires **identical** filter and **non-overlapping** regions. | Not in this talk's demos. |

---

## Impeller and Vulkan (GPU scheduling)

| Term | Aligned meaning | In Kiln / on stage |
|---|---|---|
| **DisplayList** | Serialized list of draw ops from Dart `paint()`. Replayed on the raster thread. | Between paint and tessellation on the diagram above. |
| **Tessellation (Impeller)** | **CPU** work: paths → triangles. **Not** GPU tessellation shaders. | Canvas Thrash X-ray lens; `SurfaceFrame::Encode` in the traces. |
| **Command buffer** | Recorded list of Vulkan commands (begin pass, bind pipeline, bind buffers, draw, end). Built on the **raster thread**, submitted to the **queue**. | Command-buffer slide; `QueueSubmit` in the Canvas Thrash trace. |
| **Render pass** | A bounded stretch of drawing to specific attachments (colour, depth, MSAA). Each `saveLayer` and backdrop blur tends to add passes. | Canvas Thrash glow: one offscreen pass per `saveLayer` (explained from the model; not traced on the GPU). |
| **Draw call** | One `draw` command with current pipeline and geometry. **Volume** matters on Vulkan. | Canvas Thrash: 624 broken, 161 fixed. |
| **Raster thread** | Engine thread `1.raster`. Runs Impeller on the **CPU**; submits work to the **GPU**. DevTools label **Raster**. | Red bar = here. |
| **Main thread** | Actual platform main thread (the OS UI thread); Dart runs here since 3.29. DevTools labels its Dart frame work **UI**. | Canvas Thrash UI lane: 15.9 ms broken, 3.4 ms fixed. |
| **Thrash** | Demo control: multiply canvas workload (lines, points, dots, strip segments) to **stress** the raster path under Impeller. | Canvas Thrash dial 1× → 8×. |
| **Pit stop** | Toggle one broken → fixed implementation for a scenario. One change, then replay 5 s. | Historical: the F1 concept's fix switches. This talk calls them fixes. |

---

## Profiling vocabulary

| Term | Aligned meaning | In Kiln / on stage |
|---|---|---|
| **DevTools Timeline** | Frame-scoped events; embedded **Perfetto** viewer for deep zoom. Search `KILN::` spans. | Every lap. |
| **Systrace** | Legacy Android trace format. **Perfetto** supersedes it on Android 10+; still opens old files. | "Systrace became Perfetto." |
| **Perfetto** | System trace: threads, scheduling, **frame timeline**, GPU stages when available. | Into the traces: the Canvas Thrash and Shader Storm system traces. |
| **`KILN::<Scenario>::<phase>`** | Custom timeline spans from `dart:developer` `Timeline`. | e.g. `KILN::Thrash::grid`, `KILN::Thrash::lines`. |
| **Expected / Actual timeline** | SurfaceFlinger's view of whether the app frame landed on time. | Not captured in this talk's traces (needs Perfetto's frame timeline data source). |
| **UI bar / Raster bar** | DevTools frame chart metrics, not two generic OS names. UI = `buildDuration` for Dart work on main; Raster = `rasterDuration` on `1.raster`. | "Read the bars first." |
| **Recovery time** | From the trigger frame until the last over-budget frame finished; 0 if nothing went over. Measured from engine `FrameTiming` timestamps, not an on-screen stopwatch. | Historical: the earlier Markets screen. Shader Storm reports the worst frame instead. |
| **Accumulated overrun** | Total time frames spent beyond the display budget in that window. | Historical: the earlier Markets screen. |
| **Slowest frame** | Longest single UI or raster duration in the measured window. | Shader Storm FIRST REVEAL / REPEAT worst frame. |
| **First − repeat** | First recovery time minus the latest repeat recovery time. A large positive gap indicates first-use shader work. | Historical: the earlier Markets screen. |

---

## Say it this way (aligned phrases)

| Prefer | Avoid | Why |
|---|---|---|
| Shader **compilation jank** | "Compilation junk", "compile lag" | Standard Flutter/engine wording |
| **Record** in `paint()`, **rasterize** on the raster thread | "The GPU paints in Dart" | Dart never runs on the GPU |
| **Tessellate on the CPU** | "GPU tessellation" | Impeller's path → triangles is CPU-side |
| **Repaint isolation** | "RepaintBoundary caches the layer" | No raster cache on Impeller |
| **Offscreen pass / `saveLayer`** | "Extra layer" (vague) | Ties to render-pass cost |
| **Ahead-of-time shaders** | "Zero compilation ever" | Driver still builds PSOs from shipped SPIR-V |
| **~4 ms UI and ~4 ms raster** (target) | "Must be under 4 ms or you drop frames" | Threads pipeline; see frame scheduling note |
| **Impeller on Vulkan** / **OpenGL ES backend** | "Fallback to Skia" | Skia is not the Android fallback since 3.29 |
| **Main thread** (Dart since 3.29) | "UI thread" as a second thread | Threads merged; DevTools keeps the label "UI" |

---

## Where each term appears in the demo

| Term | Best moment |
|---|---|
| Shader compilation jank | Concept video, then Shader Storm: Skia 1,863 ms vs Impeller 145 ms first reveal |
| AOT / pipeline | Shader Storm traces (40 pipelines) and One frame on Vulkan (lines 13–14) |
| Tessellation / path | Canvas Thrash, Simplify paths and X-ray; `Encode` in the traces (line 24) |
| Command buffer / draw volume | One frame on Vulkan (lines 17–18); `QueueSubmit` in the traces (line 25) |
| `saveLayer` / layer complexity | Canvas Thrash, Glow without layers; `Canvas::saveLayer` in the trace (line 25) |
| Repaint isolation | Canvas Thrash, Isolate repaints; `KILN::Thrash::grid` gone from the timeline (line 29) |
| UI budget / main thread | Canvas Thrash UI lane; Simplify paths and Isolate repaints |

When you add a new term to the talk, add a row here and a line in the [Glossary](../notes/08-glossary.md) so docs stay aligned.
