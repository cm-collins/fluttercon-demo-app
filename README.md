# Kiln: Pit Wall

**The live demo app for "Beyond Skia: Deep-Dive GPU Scheduling and Profiling with Impeller on Android 10+"**
Droidcon / FlutterCon KE 2026

Kiln is an F1 race-replay dashboard built with Flutter. It looks like a premium product,
but every component hides a realistic rendering anti-pattern. On stage, each one is
profiled live with Flutter DevTools and Perfetto, explained at the Impeller and Vulkan
level, and fixed with a "pit stop" toggle until every frame fits the 8.33 ms budget of a
120 Hz display: about 4 ms for the UI thread and 4 ms for the raster thread.

> OpenF1 car data arrives about 3.7 times per second. The screen refreshes 120 times per
> second. That is about 32 frames between data points, and every frame has 8.33 ms.

## Why "Kiln"

A kiln fires pottery before it is used. Impeller does the same with shaders: they are
compiled when the engine is built, not while your app runs. That is the difference from
Skia, and the starting point of the talk.

## What the demo shows

```mermaid
flowchart LR
    broken["Beautiful dashboard,<br/>red frames"] --> diagnose["Diagnose live:<br/>DevTools + Perfetto"]
    diagnose --> explain["Explain the engine:<br/>tessellation, draw calls,<br/>offscreen passes"]
    explain --> fix["Pit stop:<br/>one surgical fix"]
    fix --> verify["Verify:<br/>replay 5 s, compare p90"]
    verify -->|next lap| diagnose
    verify --> finish["All fixes on:<br/>every frame on time"]
```

| Lap | Screen | Anti-pattern | Fix |
|---|---|---|---|
| 1 | Telemetry Duel | Rebuilding thousands of path segments every frame | Reduce to screen resolution, build once, separate cursor layer |
| 2 | Speed Ribbon, thrashed live (1× to 8×) | Thousands of `drawPath` calls | One `drawVertices` call, then a build-time fragment shader in the same draw |
| 3 | Pit Wall | `canvas.saveLayer` per car glow, hidden `saveLayer` in the tower, one blur per card, static map repainting | Gradient glows, leaf fades, `RepaintBoundary`, `BackdropGroup` |
| 4 | Race Control | JSON decoded in `build()` on the main thread | `Isolate.run` |

Every promise in the registered abstract is mapped to a demo moment in
[Abstract alignment](docs/talk/abstract-alignment.md).

## Status

**Planning.** Documentation and the sample code package are in place; the demo app itself
has not been scaffolded yet.

## Repository layout

```text
docs/       PRD, TRD, research, design, talk, reference, history and deep-dive notes
samples/    kiln_samples: broken and fixed code for every pattern, Perfetto config and queries
```

## Sample code

[`samples/`](samples/README.md) is a small Flutter package. Every scenario has a
`...Broken` and a `...Fixed` widget with the same constructor, so the demo app can swap
them with one toggle.

```text
cd samples
flutter pub get
flutter analyze
flutter test
```

## Documentation

Start at [`docs/README.md`](docs/README.md).

| Document | Purpose |
|---|---|
| [PRD](docs/product/PRD.md) | Product requirements: goals, audience, scope, success metrics |
| [TRD](docs/technical/TRD.md) | Technical requirements: architecture, instrumentation, build modes |
| [Impeller architecture](docs/research/01-impeller-architecture.md) | How Impeller turns paint calls into Vulkan work |
| [Profiling toolchain](docs/research/02-profiling-toolchain.md) | DevTools, Perfetto, AGI and the diagnosis method |
| [OpenF1 data](docs/research/03-openf1-data.md) | Telemetry source, limits and licence |
| [Design system](docs/design/design-system.md) | "Obsidian & Aurora" palette, typography, motion |
| [Screens](docs/design/screens.md) | Every screen with its anti-pattern and fix |
| [Talk outline](docs/talk/talk-outline.md) | 40-minute narrative and slide list |
| [Demo script](docs/talk/demo-script.md) | What to click and say, minute by minute |
| [Stage runbook](docs/talk/stage-runbook.md) | Setup, rehearsal and failure recovery |
| [Rosetta](docs/reference/rosetta.md) | Flutter concepts mapped to Android and iOS |
| [Sources](docs/reference/sources.md) | Primary sources behind the research |
| [History](docs/history/README.md) | Skia to Impeller, OpenGL ES to Vulkan, Systrace to Perfetto |
| [Deep-dive notes](docs/README.md#deep-dive-notes-notes) | Flutter internals, Skia, Impeller, Vulkan, scheduling, profiling, patterns |

## Requirements

- Flutter 3.47+ (stable)
- A physical Android 10+ (API 29+) device with Vulkan 1.1 and a 120 Hz display
- Profile mode for every measurement: `flutter run --profile --trace-systrace`

## Data and trademarks

Telemetry comes from [OpenF1](https://openf1.org), an independent, community-run API, and is
used here for a non-commercial, educational demo. Kiln is not affiliated with Formula 1, the
FIA, Formula One Management or any team, and uses none of their logos or liveries.

## License

See [LICENSE](LICENSE).
