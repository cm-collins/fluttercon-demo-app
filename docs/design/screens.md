# Screens

Every screen, what it shows, the anti-pattern it hides, and the fix. Requirement IDs refer
to the [PRD](../product/PRD.md); pit stop IDs refer to the [TRD](../technical/TRD.md).

## Navigation

```mermaid
flowchart LR
    lights["0 · Lights Out"] --> pitwall["1 · Pit Wall"]
    pitwall --> duel["2 · Telemetry Duel"]
    pitwall --> ribbon["3 · Speed Ribbon"]
    pitwall --> control["4 · Race Control"]
    pitwall -.-> room["5 · Engine Room<br/>(bottom sheet, from any screen)"]
    duel -.-> room
    ribbon -.-> room
    control -.-> room
    room --> rosetta["6 · Rosetta tab"]
```

Every screen can also be opened with a `kiln://scenario/<id>` deep link.

---

## 0 · Lights Out

**Purpose:** a dramatic, clean start and a clear "frame zero" in the trace.

- Five red lights switch on one per second, then all go out; the replay starts.
- Emits a `KILN::LightsOut` span so the start is easy to find in Perfetto.
- No anti-pattern.

## 1 · Pit Wall (home)

**Purpose:** the "beautiful but lying" dashboard. Hosts three anti-patterns.

| Area | Shows | Anti-pattern (broken) | Fix (pit stop) |
|---|---|---|---|
| Track map | Circuit outline, speed-coloured ribbon, 20 car dots | Circuit and cars in one painter; `shouldRepaint` always true, so the static circuit repaints every frame | `map-layers`: static circuit behind a `RepaintBoundary`, cars in a separate light painter |
| Tower | P1–P20, gaps, tyre rings | Position changes animated with group `Opacity`; rows clipped with `Clip.antiAliasWithSaveLayer` | `tower-fade`: fade leaf colours instead of the group, rounded decoration instead of a clip |
| KPI cards | Fastest lap, top speed, DRS | One `BackdropFilter` per frosted card | `glass-group`: `BackdropGroup` + `BackdropFilter.grouped` with identical filters |

**What the audience sees in traces:** raster thread over budget; offscreen-layer
checkerboard lights up the tower and cards; the map span appears every frame.

## 2 · Telemetry Duel

**Purpose:** the path tessellation lesson.

- Two drivers' speed, throttle and brake traces for the current lap, overlaid, with a moving cursor and a delta line.
- **Broken:** every frame builds new `Path` objects with thousands of segments for every trace.
- **Fix (`duel-paths`):** each trace is reduced to at most two samples per pixel column, built once per size, and the cursor moves in its own painter.
- **Talk point:** every path is flattened and triangulated on the CPU on the raster thread, every frame — Impeller has no raster cache. Drawing ~400 segments instead of 4,000 curves is the raster win; skipping the rebuild is the UI win.
- **Code:** [`samples/lib/src/telemetry_duel`](../../samples/lib/src/telemetry_duel)

## 3 · Speed Ribbon

**Purpose:** the draw-call volume lesson (Vulkan).

- Full-screen circuit, coloured segment by segment by the selected driver's speed.
- **Broken:** about 5,000 separate `drawPath` calls, one per segment, each with its own paint.
- **Fix (`ribbon-vertices`):** one `drawVertices` call with a colour per vertex.
- **Optional fix (`ribbon-shader`):** one mesh coloured by a fragment shader compiled at build time.
- **Talk point:** on Vulkan, cost is often volume — pipeline binds and draws per frame
  ([flutter#193399](https://github.com/flutter/flutter/issues/193399)).

## 4 · Race Control

**Purpose:** prove that not every jank is GPU jank.

- Feed of flags, penalties and messages, with new batches arriving during the replay.
- **Broken:** each batch's JSON is decoded inside `build()`; the UI bar turns red while raster stays green.
- **Fix (`feed-isolate`):** `Isolate.run` decodes off the main thread; the list reads cached results.
- **Talk point:** since Flutter 3.29 Dart runs on the platform main thread, so blocking it now also blocks platform work — exactly like blocking the main thread in Kotlin or Swift.

## 5 · Engine Room (bottom sheet)

**Purpose:** the instrument panel. Always one swipe away.

| Element | Detail |
|---|---|
| Budget bars | UI, Raster, Total, each against an 8.33 ms marker, coloured with F1 timing colours |
| Stats | Rolling p50, p90, p99 and jank count over the last 240 frames |
| Renderer badge | "Impeller · Vulkan" or "Impeller · OpenGL ES", refresh rate |
| Pit stops | One switch per fix, labelled with the thread it helps |
| Actions | Replay 5s, Box all, Reset |

Built cheaply on purpose (TR-7): its own `RepaintBoundary`, one painter, text updated at most four times per second.

## 6 · Rosetta (tab inside Engine Room)

Translation table for Kotlin and iOS engineers. Content: [Rosetta](../reference/rosetta.md).

## Anti-pattern coverage

```mermaid
flowchart LR
    subgraph raster["Raster thread"]
        a1["duel-paths"]
        a2["ribbon-vertices"]
        a3["tower-fade"]
        a4["glass-group"]
    end
    subgraph both["UI and raster"]
        a5["map-layers"]
    end
    subgraph ui["UI (main thread)"]
        a6["feed-isolate"]
    end
```
