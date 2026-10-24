# kiln_samples

Broken and fixed rendering samples for the talk
**"Beyond Skia: Deep-Dive GPU Scheduling and Profiling with Impeller on Android 10+"**.

Every scenario has a `...Broken` widget (the anti-pattern) and a `...Fixed` widget (the
"pit stop") with the same constructor, so the Kiln demo app can swap them at runtime. The
notes that explain each pattern are in
[`docs/notes/07-optimization-patterns.md`](../docs/notes/07-optimization-patterns.md).

## Layout

```text
lib/
  kiln_samples.dart              public exports
  src/
    core/                        colours, trace spans, geometry helpers
    frame_budget/                FrameTiming monitor (UI / raster / total, p50–p99)
    telemetry_duel/              pattern 1 · reduce path complexity
    speed_ribbon/                pattern 2 · batch draws with drawVertices
    tower/                       pattern 3 · avoid hidden saveLayer
    glass/                       pattern 4 · group backdrop blurs
    track_map/                   pattern 5 · isolate repaints
    shaders/                     pattern 6 · precompiled fragment shader
    race_control/                pattern 8 · move work off the main thread
shaders/
  speed_ramp.frag                compiled by impellerc at build time
tool/perfetto/
  kiln_trace_config.pbtx         Perfetto recording config
  queries/*.sql                  trace_processor / Perfetto UI queries
test/                            unit tests for the pure logic
```

| Pattern | Broken | Fixed |
|---|---|---|
| Path complexity | `TelemetryDuelBroken` | `TelemetryDuelFixed` |
| Draw batching | `SpeedRibbonBroken` | `SpeedRibbonFixed` |
| Hidden `saveLayer` | `TowerRowBroken` | `TowerRowFixed` |
| Backdrop blur | `GlassCardsBroken` | `GlassCardsFixed` |
| Repaint isolation | `TrackMapBroken` | `TrackMapFixed` |
| Main-thread work | `RaceControlFeedBroken` | `RaceControlFeedFixed` + `RaceControlFeedController` |

## Commands

```text
flutter pub get
flutter analyze
flutter test
```

## Conventions

- Scenario paint and decode work is wrapped in `kilnTrace('<Scenario>', '<phase>', ...)`,
  producing `KILN::<Scenario>::<phase>` spans in DevTools and Perfetto.
- Broken and fixed files are siblings and share models, so a diff between them shows only the fix.
- No third-party dependencies, so traces contain only framework and engine work.
