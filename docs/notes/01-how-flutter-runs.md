# 01 · How Flutter runs

From your `build()` method to pixels on an Android screen. This is the mental model the
rest of the notes build on.

## The three layers

```mermaid
flowchart TB
    subgraph framework["Framework (Dart)"]
        direction LR
        mat["Material / Cupertino"] --> widgets["Widgets"] --> rendering["Rendering"] --> foundation["Animation · Painting · Gestures · Foundation"]
    end
    subgraph engine["Engine (C++)"]
        direction LR
        dartrt["Dart runtime"] --- renderer["Impeller<br/>(Skia on web / opt-out)"] --- text["Text layout"] --- channels["Platform channels"]
    end
    subgraph embedder["Embedder (Java/Kotlin + C++ on Android)"]
        direction LR
        activity["FlutterActivity / FlutterView"] --- surface["Rendering surface"] --- input["Input, lifecycle, threads"]
    end
    framework -->|"dart:ui"| engine
    engine -->|"Embedder API"| embedder
    embedder --> os["Android OS · SurfaceFlinger · GPU driver"]
```

| Layer | Written in | Responsibility |
|---|---|---|
| Framework | Dart | Widgets, layout, painting, animation, gestures. Everything you write lives here. |
| Engine | C++ | Runs Dart, renders frames (Impeller), lays out text, talks to the platform. Exposed to Dart through `dart:ui`. |
| Embedder | Java/Kotlin + C++ on Android | Hosts the engine in an `Activity`, provides the surface, forwards input, sets up threads. |

Flutter ships its own renderer inside the app. Unlike a Compose or UIKit app, it does not
ask the OS to draw platform widgets; it asks the GPU to draw triangles.

## How Dart is compiled

| Mode | Dart compilation | Use it for |
|---|---|---|
| Debug | JIT, with asserts and hot reload | Development only. **Never measure performance here.** |
| Profile | AOT to native ARM code, plus tracing hooks | All profiling, every number in this talk |
| Release | AOT, no tracing | Shipping |

## Three trees

```mermaid
flowchart LR
    w["Widget tree<br/>(immutable configuration,<br/>rebuilt often)"] --> e["Element tree<br/>(lifecycle, identity,<br/>long-lived)"]
    e --> r["RenderObject tree<br/>(layout and paint,<br/>long-lived)"]
    r --> l["Layer tree<br/>(compositing,<br/>sent to the engine)"]
```

Rebuilding widgets is cheap. Layout and paint are where the work is. Paint records
drawing commands into **DisplayLists** grouped into **layers**; nothing is rasterized in Dart.

## The frame pipeline

```mermaid
flowchart LR
    vsync["Vsync"] --> anim["Animate<br/>(tickers)"]
    anim --> build["Build"]
    build --> layout["Layout"]
    layout --> paint["Paint<br/>(record DisplayLists)"]
    paint --> composite["Composite<br/>(layer tree)"]
    composite --> raster["Rasterize<br/>(Impeller, raster thread)"]
    raster --> gpu["GPU executes<br/>and presents"]
```

Steps from Animate to Composite are Dart work (DevTools "UI"). Rasterize is engine work on
the raster thread. The GPU then runs the command buffers Impeller submitted.

## Threads (2026)

```mermaid
flowchart TB
    subgraph process["App process"]
        main["Main / platform thread<br/>Android UI + Flutter Dart code<br/>(merged since Flutter 3.29)"]
        raster["Raster thread (1.raster)<br/>Impeller: DisplayList → GPU commands"]
        io["IO thread (1.io)<br/>image decode, uploads"]
        workers["Worker isolates / engine workers"]
    end
    gpu["GPU"]
    main -->|"layer tree per frame"| raster
    raster -->|"command buffers"| gpu
    io -.->|"textures"| raster
```

**The big change:** since Flutter 3.29, Dart runs on the Android main thread; there is no
separate Flutter UI thread. DevTools still calls this work "UI". Consequences:

- Blocking Dart now blocks the Android main thread too, exactly as in Kotlin or Swift.
- Synchronous calls between Dart and the platform become possible (the reason for the change).
- In Perfetto, look for Dart work on the app's **main thread**, not a `1.ui` thread.

The **raster thread** runs on the CPU. "Raster time" means CPU time spent preparing GPU
work, plus any waiting on the GPU — not GPU execution time itself.

## How a frame gets on screen on Android

```mermaid
sequenceDiagram
    autonumber
    participant C as Choreographer (vsync)
    participant M as Main thread (Dart)
    participant R as Raster thread (Impeller)
    participant G as GPU
    participant SF as SurfaceFlinger

    C->>M: vsync → begin frame
    M->>M: animate, build, layout, paint, composite
    M->>R: layer tree
    R->>R: dispatch DisplayLists, tessellate, record render passes
    R->>G: submit command buffers
    R->>SF: present buffer (queued)
    G-->>SF: buffer ready (fence)
    SF->>SF: compose with system UI on a later vsync
```

Main and raster work for consecutive frames overlap: while the raster thread draws frame
N, Dart can already build frame N+1. That pipelining is why each thread gets close to the
full frame budget, not half of it.

## Talk takeaway

> Your Dart code produces a description of a frame. Impeller turns that description into
> GPU work on another thread. Jank lives in one of those two places, and the profiler tells
> you which.

## Sources

[Architectural overview](https://docs.flutter.dev/resources/architectural-overview) ·
[What's new in Flutter 3.29](https://flutter.dev/blog/whats-new-in-flutter-3-29) ·
[Flutter performance profiling](https://docs.flutter.dev/perf/ui-performance)
