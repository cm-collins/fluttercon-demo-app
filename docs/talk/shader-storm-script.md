# Shader Storm script

What is on screen, what you do, and what you say for the Skia JIT vs Impeller AOT segment.
Quoted lines are the intended wording; say them in your own voice, but keep the numbers
and claims exactly as written. Every number below was measured on the stage phone and is
listed in [Measured evidence](#measured-evidence).

**Length:** about 6 minutes. **Phones:** one, with both flavors installed. **Grid:** 144
tiles. What every panel means and what happens on each thread:
[09 · Shader Storm findings](../notes/09-shader-storm-findings.md).

## Before you walk on

1. Charge the phone and turn on Developer options → **Stay awake**. Set the display refresh
   rate to a fixed 120 Hz; the phone otherwise switches between 120 Hz and 90 Hz.
2. Wipe Skia's shader cache so the first reveal is truly cold:

   ```text
   adb shell pm clear dev.fluttercon.kiln.skia
   adb shell pm clear dev.fluttercon.kiln
   ```

3. Open **Kiln Skia** on the home screen. Mirror the phone on the projector.
4. Tracing stays **off** for the live run. Tracing slows every frame and changes the
   numbers; the trace slides were recorded beforehand.
5. Do not open Shader Storm while rehearsing after step 2. Any reveal fills the cache.

## How to read this script

- **Screen** is what the audience sees: `Phone` (mirrored) or `Slide`.
- **Do** is your action.
- **Say** is the line.

## 1. The phone (0:30)

**Screen:** Phone, Kiln home screen, orange **Skia · OpenGL ES** badge.

**Say:**

> "This is a Flutter app on a mid-range Android phone: Mali GPU, 120 Hz screen. That gives
> every frame 8.3 milliseconds. Miss it and the user sees a stutter.
>
> The badge says Skia on OpenGL ES, Flutter's previous renderer. Don't trust the badge. When
> this app started, the Flutter engine wrote in the log: *'the application opted out of
> Impeller'*. On the other build it writes: *'Using the Impeller rendering backend
> (Vulkan)'*. Same Dart code, same phone, one setting different."

**Do:** Tap **Shader Storm**, then tap **144** under the empty grid.

## 2. The screen (0:45)

**Screen:** Phone, Shader Storm before the reveal.

**Do:** Point at each panel as you name it.

**Say:**

> "Four things.
>
> **The motion lane.** This dot moves every frame. If the app freezes, the dot jumps and the
> jump stays on screen in red. You don't need to read a number.
>
> **Two CPU threads.** Every Flutter frame is made twice. The top lane is your Dart code,
> running on Android's main thread: it decides *what* to draw. The bottom lane is Flutter's
> **raster thread**: it turns that into work the GPU understands. Neither of them is the GPU.
> The orange line is the budget, and the corner shows the worst frame since the last reveal.
>
> **The scoreboard.** The slowest frame after the first reveal, and after a repeat.
>
> **144 tiles, not drawn yet.** Each is a different mix of ordinary Flutter paint:
> gradients, blurs, colour filters, blend modes, strokes. The kind of thing every app has."

## 3. The idea (0:45)

**Screen:** Phone.

**Say:**

> "Before a GPU can draw a gradient or a blur, it needs a small program: a **shader**.
>
> Skia writes its shaders **just in time**. The first time it meets an effect it has never
> seen, it writes the shader source, hands it to the GPU driver, and waits while the driver
> compiles it. Inside your frame. While the user watches. Let's see it."

## 4. Skia, cold (0:45)

**Do:** Tap **REVEAL 144 EFFECTS**. Say nothing for two seconds.

**Screen:** The whole motion lane turns red; FIRST REVEAL reads about 1,860 ms. The UI lane
stays green; the RASTER peak reads the same 1.8 s.

**Say:**

> "The whole lane is red. The app froze for longer than one trip of that dot.
>
> Slowest frame: almost **two seconds**. Our budget is 8.3 milliseconds. One frame took the
> time of more than **two hundred**.
>
> And look which lane is red. Not the top one. Your Dart code finished in a few
> milliseconds. It is the **raster thread**."

## 5. What the phone was doing (1:00)

**Screen:** Slide: Skia system trace of the reveal frame (recorded with 48 tiles).

**Say:**

> "You might think the drawing is just expensive. So here is a system trace of the same
> moment, recorded with 48 tiles.
>
> On the thread named **`1.raster`**, inside one frame, Skia built **52 new GPU programs**.
> Look at the nesting: the frame submits, Skia flushes its work, and inside the flush is an
> event Flutter itself labels **`shader_compile`**. **648 milliseconds** of compiling.
> About twelve and a half milliseconds per program.
>
> The freeze is not drawing. It is **writing and compiling shaders, mid-frame**. And it
> grows with your UI: 48 effects, 0.7 seconds. 96, 1.3. 144, 1.9."

## 6. Skia, repeat (0:30)

**Do:** Tap **HIDE**, then **REVEAL** again.

**Screen:** REPEAT reads about 23 ms.

**Say:**

> "Same tiles, same session. About **25 milliseconds**. The trace shows **zero** programs
> built. Skia kept them. So drawing was never the problem; **first use** was."

## 7. When first use happens (0:30)

**Say:**

> "Skia also saves those programs to disk. On this phone they are in a folder named after
> the Flutter engine's git hash. So 'first use' is a new install, a screen nobody has opened
> yet, and **every Flutter upgrade you ship**. The folder name changes, and every user is
> cold again."

## 8. Impeller, cold (1:00)

**Do:** Open **Kiln Impeller** (violet badge) → **Shader Storm** → **144** →
**REVEAL 144 EFFECTS**.

**Screen:** FIRST REVEAL reads about 145 ms.

**Say:**

> "Same app, same code, same phone. Impeller, on Vulkan.
>
> About **145 milliseconds**. Thirteen times better, and still not zero, and I want to show
> you why, because it is the real difference between the two engines.
>
> **[Slide: Impeller trace of the reveal frame, recorded with 48 tiles.]**
>
> Impeller's shaders were compiled **when the Flutter engine was built**, before this app
> existed. What it still does on first use is build **pipelines**: it takes a compiled shader
> and fixes the GPU state around it. With 48 tiles: **30 pipelines, 58 milliseconds**. About
> **two milliseconds each**, against Skia's twelve and a half.
>
> And it barely grows. Skia went from 0.7 to 1.9 seconds as we tripled the effects.
> Impeller went from 127 to 145 milliseconds. Skia needs a program per *effect*. Impeller
> needs a pipeline per *GPU state*, and there are far fewer of those.
>
> And look at the clock. During this frame the CPU core was running at 700 megahertz. The
> phone had been idle. Part of what you see is the CPU waking up."

## 9. The honest scoreboard (0:30)

**Screen:** Slide: the median table from [Measured evidence](#measured-evidence).

**Say:**

> "Three runs each, medians. Cold, first use, 144 effects: Skia **1,863**, Impeller **145**.
> With 48 effects, relaunch with the cache warm: both about **60**. Repeat inside the same
> session: Skia is actually faster, **18** against **45**, because Impeller does some
> per-frame work that Skia doesn't.
>
> So this is not 'Impeller is always faster'. It is: **Impeller moved the most expensive
> work, writing and compiling shaders, out of the frame.**"

## 10. Hand-off (0:15)

**Say:**

> "Skia pays at the worst moment, in the frame, in front of the user. Impeller paid when the
> engine was built and pays a much smaller bill at first use. The cost moved.
>
> So if compiling shaders is no longer the problem, what is? Let's go break something."

**Do:** Move to the next segment.

## Measured evidence

Device: Infinix X6873, Mali GPU, Android 16 (API 36), 120 Hz. Flutter 3.47.8, engine
`cf636b1dfb`, profile builds. Tracing off. Three rounds, alternating engines; worst frame
in the 16 frames after the reveal, median (range). Run on 2026-10-31.

Cold first reveal by grid size:

| Tiles | Skia, OpenGL ES | Impeller, Vulkan | Ratio |
|---|---|---|---|
| 48 | 687 ms (671–690) | 127 ms (122–129) | 5× |
| 96 | 1,310 ms (1,293–1,324) | 145 ms (143–149) | 9× |
| 144 | 1,863 ms (1,809–1,864) | 145 ms (145–162) | 13× |

By situation, 48 tiles and 144 tiles (the stage grid):

| Scenario | Skia, 48 | Impeller, 48 | Skia, 144 | Impeller, 144 |
|---|---|---|---|---|
| Cold: data cleared, first reveal | **687 ms** (671–690) | **127 ms** (122–129) | **1,863 ms** (1,809–1,864) | **145 ms** (145–162) |
| Repeat in the same session | 18 ms (16–20) | 45 ms (44–49) | 23 ms (22–26) | 48 ms (44–56) |
| Relaunch, disk cache kept | 58 ms (55–60) | 66 ms (63–69) | 102 ms (101–103) | 73 ms (68–78) |

144-tile traces, tracing on: Skia built 118 programs in the reveal frame (1,714 ms, 14.6 ms
each); Impeller built 40 pipelines (87 ms, 2.2 ms each). Both on `1.raster`.

From system traces of the cold reveal frame, 48 tiles:

| | Skia | Impeller |
|---|---|---|
| First-use work | 52 × `GrGLProgramBuilder::finalize`, 121 × `SkSL::Compiler::convertProgram` | 30 × `PipelineVK::Create` |
| Time | 648 ms, about 12.5 ms each | 58 ms, about 2 ms each |
| Thread | `1.raster`, inside `GrDrawingManager::flush` | `1.raster`, inside `SurfaceFrame::Encode` |
| Repeat reveal | 0 programs built | 0 pipelines built |
| Disk cache | `code_cache/flutter_engine/cf636b1dfb…/skia/`, 62 programs | `code_cache/flutter.impeller.vkcache`, 200 KB |

Renderer identity, from the engine log at startup:

- Skia flavor: `Impeller opt-out deprecated … The application opted out of Impeller`
- Impeller flavor: `Using the Impeller rendering backend (Vulkan).`

## Say it precisely

| Don't say | Say | Why |
|---|---|---|
| "Impeller has no first-use cost." | "Impeller moved shader compilation out of the frame. It still builds pipelines on first use." | The trace shows 30 pipeline builds in the reveal frame. |
| "Impeller is faster." | "Impeller is five times faster on first use. Warm, they are level; in-session repeat, Skia is faster here." | Measured medians. |
| "Vulkan fixed this." | "Compiling shaders ahead of time fixed this." | Impeller compiles its shaders ahead of time whether it runs on Vulkan or OpenGL ES. |
| "Skia compiles every time." | "Skia compiles once per new effect, then caches in memory and on disk until the engine version changes." | Repeat and relaunch numbers. |
| Any number from a traced run | The untraced medians above | Tracing slows every frame. |

## Questions senior engineers may ask

**"Couldn't Skia warm up its shaders?"** It could, with SkSL warm-up captured on a device
ahead of time. It was fragile: a capture only covered the effects and devices you
exercised, and Flutter removed the tooling. Impeller makes the warm-up part of building the
engine.

**"Why isn't Impeller's first reveal zero?"** A Vulkan pipeline is a compiled shader plus
fixed GPU state: blending, attachments, stencil. Impeller builds some at startup and the
rest on first use, and the driver still turns SPIR-V into GPU machine code at that point.
It is cheaper than Skia because the shader is already compiled from source, not generated.

**"What is the 700 MHz thing?"** CPU frequency scaling. The trace shows the raster thread
on a big core clocked at 700 MHz out of 3.2 GHz during the reveal frame, because the phone
had been idle. It makes first-use costs larger and noisier on both engines. It is also why
we quote medians.

**"Why is Impeller slower on the repeat?"** After the cold reveal, the trace shows three
frames of roughly 30 ms, all CPU work inside Impeller's frame encoding, with no shader or
pipeline work, before it settles to about 6 ms. The likely cause is offscreen render
targets for the blurs being allocated and then reused. No trace event confirms that, and
the repeat itself has not been traced, so present it as a likely cause.

**"Does the meter on screen distort the result?"** The bars are drawn as a handful of paths
and the motion dot is 24 circles; idle raster time stays under budget on both engines. The
numbers come from the engine's `FrameTiming`, not from the meter.
