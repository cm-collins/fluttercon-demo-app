# Renderer Proof Plan

## Purpose

This plan turns Kiln from a renderer comparison harness into a reliable engineering
demonstration of Flutter's rendering path on Android.

The demonstration must make three things easy to verify:

1. The same Flutter scene can run with Skia or Impeller.
2. The Android graphics backend is actually OpenGL ES or Vulkan for that run.
3. The difference can be reproduced through frame timings, Flutter traces and Android
   system traces.

The plan is written for the current Kiln app: a Binance market dashboard with a candle
chart, order book, depth chart and measured fragment shader. The live market experience is
useful for the opening product moment. Performance measurements use deterministic offline
data so network and market changes cannot contaminate the result.

## Technical model

The talk should teach this pipeline:

```text
Dart widgets and CustomPaint
          ↓
Flutter framework
          ↓
Layer tree
          ↓
Raster thread
          ├── Skia → OpenGL ES driver → GPU
          └── Impeller → Vulkan driver → GPU
```

Skia and Impeller are rendering engines. OpenGL ES and Vulkan are graphics APIs. They are
related, but they are not interchangeable names. Impeller prefers Vulkan on supported
Android devices and may fall back to OpenGL ES. The app must show the actual backend for
each measured run instead of inferring it from the flavor name.

Primary references:

- [Flutter Impeller documentation](https://docs.flutter.dev/perf/impeller)
- [Impeller Android backend selection](https://flutter.googlesource.com/mirrors/flutter.git/%2B/HEAD/docs/engine/impeller/docs/android.md)
- [Flutter architecture overview](https://docs.flutter.dev/resources/architectural-overview)
- [Flutter performance profiling](https://docs.flutter.dev/perf/ui-performance)
- [Flutter fragment shaders](https://docs.flutter.dev/ui/design/graphics/fragment-shaders)

## Renderer matrix

The first release of the comparison contains two required runs and one optional control:

| Run | Engine | Backend | Purpose |
|---|---|---|---|
| A | Skia | OpenGL ES | Legacy baseline |
| B | Impeller | Vulkan | Target comparison |
| C | Impeller | OpenGL ES fallback | Optional control separating engine and API effects |

Runs A and B must use the same physical device, Flutter SDK, Dart code, assets, build
mode, screen state and workload. Run C requires a suitable device or a separately labelled
fallback capture; it must not be presented as a same-device comparison unless it is one.

## Phase 0 — Freeze the experiment

### Objective

Define a comparison that can be repeated by another engineer without relying on judgment
or live data.

### Work

- Freeze the Flutter SDK, Dart SDK, Android SDK, JDK and dependency lockfiles.
- Keep `impeller` and `skia` as Android product flavors from the same source tree.
- Define profile mode as the measurement mode.
- Record the target display refresh rate and frame budget.
- Add an offline fixture containing fixed candles, bids, asks and selected symbol.
- Keep Binance live mode for product demonstration, but exclude it from benchmark runs.
- Define a run protocol: cold start, first draw, warm draw and repeated draw.
- Record the device model, Android API, GPU, refresh rate, Flutter version and git commit.

### Deliverables

- `OfflineDemoDataSource` beside the existing live Binance gateway.
- A written benchmark protocol in this document.
- A device/run manifest stored with every benchmark result.
- A clear app mode indicator: `LIVE` or `BENCHMARK`.

### Acceptance gate

An engineer can run the same benchmark twice without a network connection and receive the
same scene, same shader inputs and the same run sequence.

## Phase 1 — Prove renderer and backend identity

### Objective

Make the renderer path visible and independently verifiable.

### Work

Add a Renderer Evidence panel showing:

```text
Flavor: Kiln Impeller
Engine: Impeller
Backend: Vulkan
Android API: 35
GPU: device name
Flutter: version
Build: profile
Refresh rate: 120 Hz
Frame budget: 8.33 ms
```

The panel must distinguish three facts:

1. Declared flavor from the Android manifest.
2. Device capabilities reported by Android.
3. Actual engine/backend confirmation from engine startup logs.

The Android method channel can provide the flavor and device metadata. The actual backend
must be confirmed by a controlled `adb logcat` capture or an engine-supported diagnostic
source. A manifest value alone is not proof that the driver selected Vulkan.

### Deliverables

- `RendererEvidence` model and UI.
- Native device metadata method-channel endpoint.
- Backend verification script using `adb logcat`.
- Exportable evidence record containing the run ID, APK checksum and backend log excerpt.
- Clear fallback state: `Impeller · backend not verified`.

### Acceptance gate

No screenshot or stage explanation can say “Impeller Vulkan” unless the run artifact contains
backend evidence confirming Vulkan.

## Phase 2 — Split shader timing into explicit phases

### Objective

Separate asset loading, program creation, first use and steady-state drawing.

### Current limitation

The current `DepthSession` loads the `FragmentProgram` before the user presses **DRAW
DEPTH**. That is useful for keeping file I/O outside the tap, but it hides the difference
between shader loading and first-use rendering.

### Work

Instrument these phases independently:

1. App startup
2. Shader asset load
3. Fragment program creation
4. First shader draw
5. Second shader draw
6. Ten warm draws
7. Recovery after the first draw

Add controls:

- `LOAD SHADER`
- `FIRST DRAW`
- `WARM DRAW`
- `RUN 10 DRAWS`
- `RESET COLD RUN`

Each phase reports:

- UI duration
- Raster duration
- Total frame duration
- p50
- p90
- Worst frame
- Missed frame budgets
- Recovery duration

Flutter compiles declared shader assets to backend-specific formats during the build, while
first-use work can still occur when a shader is used. Both Skia and Impeller support Flutter
fragment shaders, so this phase must be explained as a first-use and pipeline comparison,
not as a shader feature available only to Impeller.

### Deliverables

- Phase-specific `FrameWindow` runs.
- Timeline markers for every phase.
- A visible cold/warm state.
- Results retained after navigating back to the watchlist.

### Acceptance gate

The UI and trace can answer whether a slow frame came from loading, first use, raster work or
recovery.

## Phase 2A — Demonstrate shader compilation jank

### Objective

Show the audience what first-use shader jank looks like, then distinguish it from ordinary
shader asset loading and steady-state raster work.

This is a separate experiment from the existing depth draw. The current depth flow loads its
`FragmentProgram` before the user presses **DRAW DEPTH**, which is correct for isolating the
draw but cannot by itself demonstrate a shader-first-use spike.

### Experiment design

Add a dedicated `Shader Jank` scenario with a deliberately cold first-use path:

```text
Launch app
    ↓
Show a simple animated surface without the test shader
    ↓
Start measurement
    ↓
Load the test FragmentProgram
    ↓
Use it during an animation frame
    ↓
Continue the animation for warm frames
```

The scenario must use a deterministic shader and fixed animation workload. It should not
depend on Binance, a network response or changing market data.

Expose these controls:

- `COLD SHADER RUN`
- `WARM SHADER RUN`
- `RUN 10 FRAMES`
- `RESET INSTRUCTIONS`

The reset instructions must explain that a true cold engine/cache state normally requires
restarting the app and, where appropriate, clearing the flavor's app data. Repeating a
button after the shader and pipeline are already cached is a warm run, not a second cold run.

### What to measure

For every run, record:

- Shader asset load duration
- Fragment program creation duration
- First shader-use frame duration
- First-use raster duration
- Number of frames over the display budget
- Largest over-budget frame
- p50, p90 and p95 for warm frames
- Recovery time until the animation is back on budget
- Whether the frame was marked as shader compilation in DevTools

At 120 Hz, the primary threshold is 8.33 ms. The UI must show the threshold beside the
measured frame so the audience can see the jank rather than infer it from a colour alone.

### Required comparison

Run the same scenario with:

| Run | Expected teaching point |
|---|---|
| Skia / OpenGL ES cold | Possible first-use shader compilation spike |
| Skia / OpenGL ES warm | The same shader after its first-use cost |
| Impeller / Vulkan cold | Compare first-use behavior with the same workload |
| Impeller / Vulkan warm | Steady-state behavior after the first draw |

The result must not promise that every device will show a large Skia spike or zero Impeller
spike. The scenario demonstrates a mechanism; the observed magnitude is device, driver,
shader and Flutter-version dependent.

### Trace evidence

Add explicit markers:

```text
KILN::ShaderJank::load
KILN::ShaderJank::program
KILN::ShaderJank::first_use
KILN::ShaderJank::warm_frame
KILN::ShaderJank::recovery
```

The trace and report must identify:

```text
experiment=shader_jank
temperature=cold|warm
renderer=skia|impeller
backend=opengles|vulkan|unverified
run=001
```

DevTools should be used to show the Flutter frame and shader-compilation indicators. Perfetto
should be used to show the corresponding raster-thread and system scheduling interval. The
two captures must share the same run ID.

### Teaching script

The explanation should follow this order:

1. The shader source is declared in the package and compiled into the app's backend format.
2. Loading the `FragmentProgram` is not the same event as drawing it.
3. The first use may require additional engine or driver work.
4. If that work lands inside a frame, it can exceed the frame budget.
5. A warm draw shows the steady-state cost after first use.
6. Skia and Impeller use different rendering implementations, but both support Flutter
   fragment shaders.
7. The trace, not the visual appearance, establishes whether a frame was late and where the
   time was spent.

### Acceptance gate

The scenario is complete when a presenter can reset the app, run a cold shader-use sequence,
show the first-use frame and then show the warm sequence with matching DevTools and Perfetto
evidence. If the device does not produce a visible spike, the UI must still show the measured
first-use and warm values and explain that the device did not reproduce a large jank event.

## Phase 3 — Build the architecture teaching surface

### Objective

Give junior engineers a simple mental model and senior engineers an inspectable deep dive.

### Work

Add a `Renderer Lab` or `Pipeline Evidence` screen with four sections:

#### Scene

- Widget and render-object summary
- Layer tree summary
- Repaint boundary state
- Canvas operation summary

#### Engine

- UI thread
- Raster thread
- Frame timing
- Layer tree handoff

#### Renderer

```text
Skia → OpenGL ES
Impeller → Vulkan
```

The renderer section must include the fallback note and actual backend evidence.

#### Evidence

- DevTools frame chart capture
- Perfetto trace capture
- Benchmark table
- Backend log confirmation

Every term should have a one-sentence explanation. Expandable details can cover command
encoding, pipeline state, render passes, synchronization and driver submission.

### Acceptance gate

A junior engineer can explain the pipeline in one minute. A senior engineer can inspect the
run ID and trace markers to locate the expensive phase without relying on the speaker's
narration.

## Phase 4 — Instrument traces for correlation

### Objective

Make app events, Flutter frame timing and Android system traces line up.

### Work

Standardize trace names:

```text
KILN::startup
KILN::load_shader
KILN::create_program
KILN::first_draw
KILN::warm_draw
KILN::recovery
KILN::benchmark_run
```

Attach metadata to every run:

```text
run=skia-opengles-cold-001
renderer=skia
backend=opengles
mode=profile
phase=first_draw
```

Update the Perfetto configuration and SQL queries to answer:

- Which frame first exceeded budget?
- Was the delay on the UI or raster thread?
- How long was recovery?
- Did the draw create additional raster work?
- Did scheduling gaps contribute to the result?
- Did cold and warm runs differ?

### Deliverables

- Shared run ID across app timeline, logcat and benchmark report.
- Perfetto trace config for the benchmark.
- SQL queries for cold/warm and UI/raster comparisons.
- A trace naming and metadata guide.

### Acceptance gate

An engineer can select one run ID and correlate the app event, Flutter frame and Android
system trace without guessing where the event belongs.

## Phase 5 — Automate the renderer comparison

### Objective

Turn the stage experiment into a repeatable engineering tool.

### Work

Create `tool/benchmark/` with a script or command sequence that:

1. Verifies the connected device.
2. Checks Android API, GPU and refresh rate.
3. Installs the selected flavor.
4. Clears data for cold runs.
5. Launches profile mode.
6. Opens benchmark mode.
7. Executes the scripted run sequence.
8. Captures logcat backend evidence.
9. Captures Flutter timeline data.
10. Captures Perfetto.
11. Writes Markdown and JSON reports.

The report must include actual values, for example:

```text
Renderer comparison
Device: <device>
Refresh: 120 Hz
Flutter: <version>

Skia / OpenGL ES
Cold first draw: <measured>
Warm p90: <measured>
Missed budgets: <measured>
Recovery: <measured>

Impeller / Vulkan
Cold first draw: <measured>
Warm p90: <measured>
Missed budgets: <measured>
Recovery: <measured>
```

Never commit illustrative measurements as if they were device results. Reports must label
the device, build and date.

### Acceptance gate

Another engineer can run the tool from a clean checkout and produce a complete report with
backend evidence and matching trace files.

## Phase 6 — Statistical and device validation

### Objective

Prevent a single noisy frame from becoming the talk's conclusion.

### Protocol

- Run at least 10 cold samples per required flavor.
- Run at least 30 warm samples per required flavor.
- Report median, p90, p95 and worst frame.
- Record missed budgets and recovery duration.
- Record device temperature when available.
- Allow the device to cool between flavor comparisons.
- Keep brightness, refresh rate and power mode fixed.
- Record whether the device is charging.
- Repeat the comparison on a second device before making a general claim.

### Acceptance gate

The presentation states what was measured, on which device, under which conditions, and
which conclusions are device-specific.

## Phase 7 — Stage-ready teaching and fallback

### Objective

Make the demonstration understandable and recoverable in a conference environment.

FlutterConKE and DroidconKE combine technical sessions, workshops, panels, networking and
exhibitions for a broad mobile engineering audience. The live demo therefore needs a short
mental model, an inspectable deep dive and a reliable fallback. See [FlutterConKE](https://fluttercondev.ke/)
and [DroidconKE](https://droidcon.co.ke/).

### Talk sequence

1. Show the same market scene in both flavors.
2. Ask which renderer and backend produced it.
3. Show the evidence panel and backend log.
4. Run Skia cold and warm draws.
5. Run Impeller cold and warm draws.
6. Show DevTools UI/raster timings.
7. Show the matching Perfetto trace.
8. Explain which differences come from Flutter, the renderer, the graphics API or the
   device driver.
9. Repeat a warm draw to show steady state.
10. End with measured results and limitations.

### Fallback levels

#### Live

- Connected device
- Both flavors installed
- DevTools and Perfetto ready
- Network available for the opening market screen

#### Offline

- Bundled market fixture
- Local benchmark mode
- No network dependency

#### Recording

- Exported DevTools captures
- Exported Perfetto traces
- Backend log captures
- Screen recording of the same run

### Acceptance gate

The talk can continue if Binance, the device connection or live tracing fails. The speaker
can still demonstrate the same evidence and explain the same conclusion.

## Definition of done

The renderer proof is ready when:

- Actual backend identity is visible and independently verifiable.
- Skia and Impeller use identical deterministic workload inputs.
- Cold, first-use, warm and steady-state phases are separated.
- At least ten repeated samples are collected for each required flavor.
- p50, p90, worst frame, missed budgets and recovery are shown.
- DevTools, Perfetto and logcat share a run ID.
- The app teaches the pipeline at junior and senior depth.
- The benchmark works without network access.
- The stage has tested offline and recording fallbacks.
- README, TRD, talk notes and stage runbook describe the same implemented behavior.
- No claim equates Impeller with Vulkan without backend evidence.

## Recommended implementation order

Implement Phases 0–2A first. They establish deterministic inputs, backend truth, valid timing
boundaries and the shader-jank experiment. Then implement Phases 4–5 so every later UI and talk
improvement is based on evidence. Build the teaching surface and stage polish after the
measurement pipeline is trustworthy.
