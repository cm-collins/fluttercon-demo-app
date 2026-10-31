# 02 · The Skia era and why it had to end

Skia is the 2D graphics library behind Chrome and Android's own UI toolkit. It powered
Flutter from the start. Understanding its one structural weakness explains why Impeller exists.

## How Skia renders on the GPU

Skia is extremely general. For each new combination of draw state (shape type, paint,
gradient, blend mode, clip, antialiasing…) it **generates a shader program** on the fly.

```mermaid
flowchart LR
    draw["New kind of draw<br/>appears in a frame"] --> gen["Skia generates SkSL<br/>for this combination"]
    gen --> translate["Translated to GLSL<br/>(or SPIR-V / MSL)"]
    translate --> driver["GPU driver compiles<br/>the shader"]
    driver --> stall["Raster thread stalls<br/>measured: about 12.5 ms<br/>per program"]
    stall --> cached["Cached in memory,<br/>and on disk per engine version"]
```

Measured on a Mali phone with the Shader Storm screen
([note 09](09-shader-storm-findings.md)): revealing 48 new effects at once made Skia build
**52 programs in 648 ms** on `1.raster`, inside one 677 ms frame. The freeze grows with the
number of new effects: **0.68 s** for 48, **1.3 s** for 96, **1.86 s** for 144.

The first time an animation used a new effect, the raster thread waited for the driver
compiler. Users saw a stutter **the first time** something happened — known as
**shader compilation jank** or "early-onset jank". It was most visible on iOS (Metal) and
on low-end Android GPUs.

## The workarounds (and why they failed)

| Workaround | Idea | Problem |
|---|---|---|
| Shader warm-up (`ShaderWarmUp`) | Draw common shapes offscreen at startup | Guesswork; slowed startup; default routine was removed in 2021 because it didn't help benchmarks |
| SkSL warm-up (`--cache-sksl`, `--bundle-sksl-path`) | Record shaders used during a manual run, bundle them in the app | Per device and driver, needed re-capturing for every app change; only reliably useful on iOS |
| Raster cache | Cache complex, stable layers as images | Heuristic, uses GPU memory, doesn't fix first-use compilation |

In February 2025 the SkSL bundling was **removed from the Flutter tool**: Skia can no longer
be used on iOS, and on other platforms the generated shaders were device-specific anyway.

## The insight behind Impeller

> You cannot fix runtime shader compilation with a cache. You fix it by not needing
> runtime compilation at all.

Impeller uses a **small, fixed set of shaders** written by the Flutter team, compiled
**when the engine is built**. Every Flutter drawing operation must be expressed with that
set. That is a constraint — and the source of its predictability.

What remains at runtime is building **pipelines**: a compiled shader plus fixed GPU state
such as blending. Impeller builds many at startup and the rest on first use, where the
driver still lowers the precompiled shader to GPU machine code. That is far cheaper than
generating and compiling shader source, but it is not zero; see
[03 · Impeller internals](03-impeller-internals.md#shaders-and-pipelines).

## Skia vs Impeller at a glance

| | Skia (GPU backend) | Impeller |
|---|---|---|
| Shaders | Generated per draw combination at runtime | Fixed set, compiled at engine build time |
| First-use cost | Large: write and compile a program per new effect (measured ~12.5 ms each) | Small: build a pipeline per new GPU state (measured ~2 ms each, 30 for 48 effects) |
| Disk cache | Compiled programs, in a folder named after the engine version | Vulkan pipeline cache (`flutter.impeller.vkcache`) |
| Raster cache | Yes (heuristic) | No |
| Path filling | GPU techniques incl. stencil-based approaches | CPU tessellation to triangles, MSAA for antialiasing |
| Where it runs in 2026 | Web (CanvasKit / skwasm); Android when Impeller is disabled | iOS (only option), Android API 29+, desktop (default since 3.47) |

## What Skia did better (be honest on stage)

- A **raster cache** that could make some static-but-complex scenes cheap after a few frames.
- Mature, heavily tuned paths for some effects; certain blurs measured faster on Skia than on
  Impeller in 2025–2026 issues.

That is why the talk says Impeller is **predictable**, not **always faster**. Measured: when
the same 48 tiles were redrawn in the same session, Skia's worst frame was 23 ms and
Impeller's 44 ms.

## Demo tie-in

The **Shader Storm** screen in the `skia` and `impeller` flavors. Clear app data, press
**REVEAL**, and the first reveal freezes on Skia (about 1.9 s at 144 tiles) while Impeller
pays about 145 ms. The repeat shows the cached case. Full results and traces:
[09 · Shader Storm findings](09-shader-storm-findings.md); stage wording:
[Shader Storm script](../talk/shader-storm-script.md).

## Sources

[Impeller rendering engine](https://docs.flutter.dev/perf/impeller) ·
[Remove SkSL bundling — flutter#162849](https://github.com/flutter/flutter/pull/162849) ·
[No default shader warm-up — flutter#87126](https://github.com/flutter/flutter/pull/87126) ·
[cache-sksl not usable with Impeller — flutter#140310](https://github.com/flutter/flutter/issues/140310) ·
[Android backdrop filter slower than Skia — flutter#174984](https://github.com/flutter/flutter/issues/174984)
