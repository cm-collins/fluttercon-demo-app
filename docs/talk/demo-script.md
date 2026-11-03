# Demo script

The run of show for the 40-minute talk: what is on screen, what you do, and what you say.
Quoted lines are the intended wording; say them in your own voice, but keep the facts exactly
as written (see [Say it precisely](#say-it-precisely)). The two demo segments have their own
line-by-line scripts:

- [Shader Storm script](shader-storm-script.md): Skia JIT vs Impeller AOT, first use.
- [Canvas Thrash script](canvas-thrash-script.md): drawing cost on Impeller, four fixes.

Every promise in the registered abstract is mapped to a moment here in
[Abstract alignment](abstract-alignment.md). Term definitions: [Talk vocabulary](vocabulary.md). Where each claim comes from: [Fact check](fact-check.md).

**Stage setup: the demo app carries the talk.** The slides stay quiet: one idea, few words. Run the
demos on a mirrored phone from their scripts. The recordings in `slides/local/clips-stage/` are the fallback if
there is no phone or the phone fails, and every `>>> DEMO` cue below names its clip. Slides 4 and 27 draw real frames from the captured traces. Captures live in
`~/fluttercon-captures/2026-10-31-infinix-x6873/` (see its README). Before the session, follow
the [Stage runbook](stage-runbook.md).

**The numbers on the slides were measured on the Infinix.** A different phone will show different live
numbers. Say so, or re-run `tool/benchmark` on that phone and update the slides.

**Measured on:** Infinix X6873 · Mali-G615 MC6 · Vulkan 1.3 · Android 16 · 120 Hz · Flutter
3.47.8, profile builds. Say this once, early, and put it on the evidence slides.

## How to read this script

- **Screen** is what the audience sees: `Slide`, `Video` (a file from `videos/`) or
  `Perfetto` (a trace open in ui.perfetto.dev).
- **Do** is your action on the laptop.
- **Say** is the line. About 130 words per minute; each segment fits its time box.
- ⏱ marks where you should be. If you are more than a minute late, use the cut noted there.

## Run of show

Times are estimates from the word count of the speaker notes at about 130 words a minute, plus the
clips and votes. Check them in a rehearsal.

| Time | Segment | Slides | Length | Abstract promise it delivers |
|---|---|---|---|---|
| 00:00 | Cold open and map | 1–2 | 1:15 | Real-time graphics canvas, under stress |
| 01:15 | How Flutter draws | 3–4 | 3:15 | Threads, the frame pipeline, 120 fps, ~4 ms UI / ~4 ms raster |
| 04:30 | Before: Skia | 5 | 2:15 | Skia's runtime model, compilation jank |
| 06:45 | Now: Impeller | 6–8 | 5:00 | Definitive transition to Impeller; precompiled shaders; how pipelines are scheduled; Vulkan on Android 10+, and when it isn't used |
| 11:45 | The proof | 9–10 | 3:45 | Skia JIT vs Impeller AOT, measured |
| 15:30 | Inside a frame | 11–16 | 5:45 | How a GPU works, tessellation, explicit command buffers, GPU scheduling, overdraw, render passes |
| 21:15 | What Impeller didn't fix | 17–24 | 8:15 | Thrash a real-time canvas; repaint isolation; layer reduction; custom painters |
| 29:30 | Your own shader | 25 | 1:00 | Maximize Impeller's pre-compiled rendering pathways |
| 30:30 | Prove it | 26–28 | 3:30 | DevTools, Systrace / Perfetto, frame-budget reading |
| 34:00 | Finish | 29–30 | 1:15 | Honest limits; the three registered takeaways |
| 35:15 | Q&A | 31–32 backup | 4:45 | |

If you run long, use the cuts in the [Stage runbook](stage-runbook.md#timing-cues).

## The deck

**Slides:** [`slides/beyond-skia-dark.pptx`](slides/beyond-skia-dark.pptx), with a light copy beside it. Each slide
has one message and one visual. The explanation is in your voice and the demo. **Clips:** `slides/local/clips-stage/`, played
separately in a video player, so the deck itself carries no video.

| When | Demo on the phone, or play this clip | Then |
|---|---|---|
| After slide 1 | `01-broken-chart-8x.mp4` | Slide 2 |
| After slide 4 | `02-skia-to-impeller-concept.mp4` | Slide 6 |
| During slide 9 | `03-skia-first-reveal.mp4`, then click | First score appears |
| During slide 9, after the vote | `04-skia-repeat.mp4`, then click | Second score appears |
| During slide 9 | `05-impeller-first-reveal.mp4`, then click | Impeller scores appear |
| During slide 17, before the click | `06-dial-1x-to-8x.mp4` | Slide 20 |
| After the click on slide 18 | `07-xray.mp4`, then `08-simplify-paths.mp4` | Slide 22 |

### Audience votes

A show of hands, about 20 seconds each. Ask, wait, then click.

| Slide | Ask | The answer |
|---|---|---|
| 9 | "Same effects, second time. Will it freeze again?" | No: 23 ms. The programs are built |
| 18 | "Which fix helps raster most, on its own?" | Simplify paths, 18.6 ms from 29.7. Batch draws barely moves it |
| 23 | "A `RepaintBoundary` on the grid, on its own: how much does it save?" | Almost nothing at 8×. A grid is nothing next to 130,000 points |
| 27 | "Is the raster thread waiting on the GPU?" | No: it is running 24 of 28 ms |

### Two true stories

Say these in your own words.

- **Slide 27.** "Going in, I suspected the raster thread was waiting on the GPU. The trace said
  otherwise: on this phone it's the CPU." Only say this if it is true for you.
- **Slide 4.** "The phone was set to 120 Hz, but it was quietly running my app at 60 until I set it
  per app. Check the header before you trust a number."

---

## Slide by slide

These words match the speaker notes in the deck. Say them in your own voice, but keep the facts. The everyday comparisons are suggestions, so swap in your own.

### 00:00 Cold open

**Slide 1: Beyond Skia**

Hi, I'm Collins. Let me show you a chart.

>>> DEMO, phone: Kiln → Canvas Thrash → tap 8×. Let it run red. No phone: play 01-broken-chart-8x.mp4 from local/clips-stage/.

**Slide 2: Impeller tamed one kind of jank.**

This is a live market chart in Flutter, on Impeller, on Vulkan, on a 120 hertz phone. Every red bar there was a frame that missed its deadline. It ran at about a third of the frame rate the screen can show.

Impeller was supposed to fix jank. It tamed one kind: compilation jank, about 13 times shorter on my test phone. It didn't touch the other kind: drawing cost. That's today's map. To understand either one, we first need to see how Flutter gets a picture onto the screen, so let's start at the top.

### 01:15 How Flutter draws

**Slide 3: One frame, from vsync to pixels.**

Let's follow one frame. Two words first. When I say Dart, I mean your code: widgets, layout, your paint methods. When I say engine, I mean the C++ that ships inside your app, and dart:ui is the door between them. On Android, the embedder hosts both and provides the surface, the input and the threads. Flutter doesn't ask Android to draw a button. It asks the GPU to draw triangles.

Vsync is the screen's tick: time for a new frame. It fires. CLICK: on the main thread, Flutter animates, builds, lays out and paints. Here's the first thing people get wrong: paint draws nothing. Your paint method records a list of commands called a DisplayList, and hands it over.

CLICK: the raster thread takes that list. It replays it, gets the GPU programs it needs, breaks paths into triangles, and records commands for the GPU. Raster time is CPU time. The GPU hasn't done this work yet.

CLICK: the GPU runs those commands later, on its own schedule, then Android puts the result on the display. So there are three names and only two CPU threads. Remember this picture: everything we measure today lands in one of those three. Now, how long do they have?

**Slide 4: Every frame gets 8.3 ms.**

Think of a train that leaves every 8.3 milliseconds, on time, like the SGR. If your frame isn't on the platform, it doesn't wait, and the screen shows the old frame again. That's a dropped frame. At 120 hertz that's the budget: 8.3 milliseconds. Those lines are the deadlines.

CLICK: budget about 4 milliseconds for UI and 4 for raster, and the whole frame lands in one refresh. Strictly, the threads overlap. While raster draws this frame, Dart can already build the next. So each thread can stretch to 8.3 and you still hit 120, but every frame arrives later and you have no headroom. Four and four is the target. 8.3 per thread is the limit.

CLICK: this is the chart you just saw, real frames from a trace. Raster is 28 milliseconds. A thousand divided by 28 is 36 frames a second, and that is what we measured. The slowest thread sets your frame rate.

Hold on to that. Now let's go back to where a frame could suddenly take almost two seconds.

>>> AFTER THIS SLIDE: play 02-skia-to-impeller-concept.mp4 from local/clips-stage/, then come back and press Next.

### 04:30 Before: Skia

**Slide 5: Compilation jank.**

For most of Flutter's life, the renderer on Android was Skia on OpenGL ES. Skia is the 2D library behind Chrome and Android's own UI: excellent and general purpose.

So what is compilation jank? You've felt it: you open a screen for the first time and it stutters, and the second time it's smooth. A shader is a small program for the GPU, and the driver has to compile it for that exact chip. Skia is general, so it generates a shader for each new combination of paint, blend and clip.

A new combination appears on screen. Skia writes SkSL, that's translated to GLSL, the driver compiles it on the raster thread, inside your frame, and the frame misses its deadline.

CLICK: how bad? That tiny mark is one frame's budget. Each block is one program from a real Skia trace, to scale: 118 of them, about 14.5 milliseconds each, in one frame. 1.8 seconds.

It happens once per shader, per install, and a Flutter upgrade resets the cache. You rarely see it, because your own phone is already warm. And no amount of optimising Dart touches it. The UI bar stays green while the app is frozen.

For years people worked around this with warm-up code and bundled shaders, and had to capture again after each engine upgrade. The Flutter team's own issue, opened in May 2019, asked for something that "requires 0 extra effort from developers". It closed in August 2023, with the team pointing to Impeller. So what changed?

### 06:45 Now: Impeller

**Slide 6: The Android engine, before and now.**

Here's the engine on Android, before. Read it top to bottom. Nothing was compiled ahead for your screen. Dart had its own thread, 1.ui. The raster thread wrote and compiled shaders while the user watched. Skia kept an automatic raster cache, and OpenGL ES hid the work in the driver.

CLICK: and now. A small fixed set of shaders, written by the Flutter team, goes through impellerc when the engine is built: SPIR-V for Vulkan, Metal for iOS and macOS, and GLSL ES for OpenGL ES. They ship inside the engine. Writing and compiling shaders on the raster thread are gone. That's the win, and we'll measure it.

The ones in colour are the bill. Impeller tessellates paths itself, on the CPU, so keep your eye on that. And there's no raster cache, so some old fast code is now honestly slow. Vulkan hides much less: the engine says exactly what runs and when, so what you pay for is how much you record. One more change you'll see in every trace isn't Impeller at all: since 3.29, Dart runs on the main thread, and my Skia build does too. DevTools still calls it UI. First, let's see exactly when each engine does its work.

**Slide 7: Skia compiles late. Impeller compiles early.**

Think of a restaurant. Skia writes the recipe after you order, and you wait. Impeller preps the kitchen before it opens. Here's the same app as a timeline, left to right, from when the code is built to every frame on the phone.

CLICK: Skia is just in time, JIT. Nothing happens ahead of time unless you wrote a warm-up. All the expensive work lands in the first use of an effect: about 14.5 milliseconds per program, inside the frame.

CLICK: Impeller is ahead of time, AOT. Shaders are compiled at engine build, and your own frag files when you build your app. A pipeline is a compiled shader plus fixed GPU state. Most are built at startup.

But be careful: not all of them. The design goal in Impeller's README is to build pipeline state up front, and my traces show a few still built in the frame, about 2.2 milliseconds each, when a draw needs a combination it doesn't have yet. So the honest claim is: no shader is written in the frame, and the source was compiled ahead of time. But SPIR-V isn't what the GPU runs. When a pipeline is built, the Vulkan driver still turns it into code for this chip, and Vulkan's own docs call that shader compilation. That's those 2.2 milliseconds, and Impeller saves the result to disk, which is why a relaunch is faster. So "no runtime compilation" is shorthand. It's a fraction of what it was, not zero.

**Slide 8: On Android, Vulkan isn’t guaranteed.**

Impeller didn't arrive everywhere at once. iOS came first, on Metal, as the default in 3.10 in May 2023. Android followed in 3.27, in December 2024, because of the range of hardware. Desktop arrived this year in 3.47. On Android, there's a catch. The talk's title says Android 10 and up, that's API 29. That's the minimum, not a promise of Vulkan. Android 9 or older gets Skia on OpenGL ES, unconditionally.

CLICK: from Android 10, the engine checks the device. It avoids Vulkan on emulators, on Huawei, on MediaTek chips whose vendor API is below 32, on Adreno 650 and older, and on some Exynos chips and known-bad drivers. Then it tries to start Vulkan 1.1 with the extensions it needs. Any failure means Impeller on OpenGL ES, not Skia. Note it's the vendor API, the Android version the chip's drivers were built for. So a phone updated to Android 13 can still land on OpenGL ES, and so can a recent Android version on an older Snapdragon. [Only if you've confirmed the cause: that happened on my Android 13 phone.] Flutter 3.29's notes say why: black screens and crashes with Vulkan on some MediaTek and PowerVR chips.

CLICK: so don't guess. Read the log. Every Impeller number today comes from a phone whose log says Vulkan. If yours says OpenGLES, the pipeline and command-buffer details on the next slides don't apply in the same way, though the tessellation and the drawing costs still do.

So is the win real? Let's measure it.

### 11:45 The proof

**Slide 9: Same app. Same phone. Two renderers.**

Don't trust a badge. Read what the engine writes at startup. One build says "The application opted out of Impeller". The other says "Using the Impeller rendering backend (Vulkan)". Same Flutter SDK, same Dart code, same phone, one setting different. Shader Storm reveals 144 tiles at once, and no two share the same mix of paint settings. The scoreboard shows medians of three clean runs on my test phone, an Infinix, so what you see live will differ.

>>> DEMO, phone: Kiln Skia → Shader Storm → 144 → Reveal (cold: clear the app's data before the talk). Watch the motion lane, and say nothing for two seconds. No phone: play 03-skia-first-reveal.mp4.

CLICK: Frozen. Nearly two seconds, the whole motion lane red. And the UI lane stayed green: Dart was fine, the engine stopped to compile.

VOTE: same effects, second time. Hands up: will it freeze again? Wait for hands.

>>> DEMO, phone: reveal the same 144 again. No phone: play 04-skia-repeat.mp4.

CLICK: 23 milliseconds. No freeze. The programs are already built.

Now Impeller, same phone, same 144 effects, first time.

>>> DEMO, phone: Kiln Impeller → Shader Storm → 144 → Reveal. No phone: play 05-impeller-first-reveal.mp4.

CLICK: 145 milliseconds. Short, but not zero. And its second time is 48.

CLICK: 13 times shorter at 144. And it barely grows: tripling the new effects took Skia from 0.7 to 1.9 seconds, and Impeller from 127 to 145 milliseconds. After a relaunch, disk caches help both: 102 against 73. But Skia's cache is keyed to the engine version, so a Flutter upgrade sends your users back to the top number.

**Slide 10: The cost shrank and moved. It didn’t vanish.**

Here's why it barely grows. CLICK: Skia builds a program per effect, 118 in the reveal frame. Impeller only builds pipelines from shaders that are already compiled: 40 of them, about two milliseconds each. Both on the raster thread, both in the frame. The cost moved and shrank. It did not vanish.

And to be fair, look back at the scoreboard: in the same session, Skia is actually faster, 23 against 48. So this is not 'Impeller is always faster'. It's predictable, and it took the most expensive work out of the frame. So what is Impeller doing in those frames instead? Let's look inside one.

### 15:30 Inside a frame

**Slide 11: To the GPU, everything is triangles.**

Before we go inside a frame, look at this. On the right, a mountain. On the left, the same mountain as the GPU sees it: triangles.

Game or chart, the GPU only fills triangles. It doesn't know what a mountain is, or a price line, or a button. It transforms the corners of each triangle, works out which pixels the triangle covers, and colours those pixels. Flutter's drawing is 2D, but the GPU sees it the same way.

So who makes the triangles? In many game engines, the GPU can help, with tessellation shaders. Impeller does it on the CPU. That's why a chart with 130,000 points hurts the raster thread. Let's see how.

**Slide 12: Tessellation: how a path becomes triangles.**

Now the step I told you to watch. Your GPU fills triangles. It can't fill a Bezier curve. So someone has to cut every path into triangles, and on Impeller that someone is the CPU.

CLICK: paint asks for a path: lines and curves.
CLICK: curves flatten into points. The tolerance depends on scale, so drawing it larger gives more points.
CLICK: for a stroke, each point gets two vertices, half the stroke width each side. A corner adds two more, unless the turn moves the edge by less than a quarter of a device pixel.
CLICK: those become one long triangle strip. v vertices make v minus 2 triangles.

CLICK: this all happens on the CPU, on the raster thread. The vertices are copied into per-frame memory, and it becomes one draw. Next frame, it all happens again. There's no cache between frames.

So words matter. A path is what you ask for. Tessellation is the work Impeller does with it. The chart you saw is my demo at its 8× setting: 16 lines of 8,000 points, two vertices a point. That's at least a quarter of a million vertices every frame, built by the CPU. I worked that out from the engine's own rule; Impeller doesn't report the count.

You'll see this live in a moment: my app's X-ray mode is a model of these steps on the real path.

**Slide 13: Who does what.**

So here's who does what. Look at the one in colour: tessellating paths is on the CPU's side, and so is recording the commands. The GPU's list is the part most people picture. In this chart, the expensive work is on the left. Next: how the left hand gives work to the right.

**Slide 14: The CPU records. The GPU executes.**

Those triangles don't go straight to the GPU. Think of a waiter: they write your order down, and the kitchen cooks it later. You wrote one drawCircle. The raster thread writes a list: begin a render pass, bind a pipeline, bind buffers, draw, and so on. That's a command buffer. On Vulkan this is explicit, so Impeller writes each command itself.

CLICK: watch one frame go through. Raster records. It submits to the queue and moves on. The GPU executes while the raster thread is already on the next frame. A fence tells the CPU when the GPU has finished.

That is GPU scheduling. The CPU records, the GPU executes, fences keep them in step. No single command is slow. Volume is the cost.

And there are two more costs on the GPU's side.

**Slide 15: Overdraw: painting the same pixel again.**

One more word you'll hear: overdraw. Paint a wall three times and only the last coat shows, but you paid for three coats. A screen works the same way. Here's code you've written: an image, a card on top of it, text on top of that.

CLICK: follow one pixel down through the layers. Drawn for the image, again for the card, again for the text. The image behind the card is work nobody sees.

Two honest points. Impeller and the GPU skip some of this for you: a solid colour that fills the whole screen gets merged into the clear, and Mali can kill pixels it knows are hidden. So a Stack of two full-screen coloured Containers isn't the problem people say it is. And I didn't measure overdraw in my demo, so I won't give you a number for it. What I measured is the next thing: what happens when you ask for a layer.

**Slide 16: Why a layer costs more than a draw.**

Most mobile GPUs are tile-based. They split the screen into tiles and draw each one in fast on-chip memory. Writing out to main memory is slow and costs battery, so the ideal frame is one render pass: clear, all your draws on the chip, resolve the anti-aliasing on the chip, store once.

CLICK: now add one saveLayer with a blur. The GPU has to store what it has drawn, switch to an offscreen target, draw and blur there, then load everything back to composite it. The Flutter docs compare it to making a firehose change direction. The docs list ShaderMask and ColorFilter as widgets that might trigger a saveLayer, and some Chip and Text cases.

I need to be honest about one thing. What I measured is the CPU side: 64 saveLayer and two queue submits per frame, and taking them out cut raster from 13.7 to 6.6 milliseconds. What the Mali GPU did with those passes, this phone's driver doesn't expose. So the GPU side here is the model, not my trace.

That's the full picture of a frame. Now we can break one.

### 21:15 What Impeller didn't fix

**Slide 17: What Impeller didn’t fix.**

Skia pays at the worst moment, in the frame, in front of the user. Impeller paid when the engine was built. So if compiling shaders is no longer the problem, what is? Let's go break something. This dial is mine, not a Flutter limit. Each level adds two lines and a thousand points per line, so at 8× it's 16 lines of 8,000 points, on purpose. Each step is about four times the path points. Watch which bar grows.

>>> DEMO, phone: Kiln Impeller → Canvas Thrash at 1×, then tap 2×, 4×, 8×. Stop on 8×, every fix off. No phone: play 06-dial-1x-to-8x.mp4.

CLICK: on the phone, RASTER is far taller than UI: 29.7 milliseconds against 15.9, with a budget of 8.3. My Dart finishes; the engine is the one struggling. And nothing here is compiling. This is pure drawing cost, and no renderer saves you from asking it to draw too much.

Three separate things grew. Path points, from 2,240 at 1×: that's the detail I ask for, and tessellation is the work it causes. Almost 130,000: 128,000 from the lines, the rest from the heat strip. Draw calls, 624: each one records binds and a draw. Layers, 64: each one adds an offscreen pass. Three inputs, three different costs. So which one do we fix?

**Slide 18: Which fix helps most, on its own?**

VOTE: four fixes, each one on its own. Which helps raster most? Hands up for Simplify paths. Batch draws. Glow without layers. Isolate repaints.

CLICK: Simplify paths, by a distance. 29.7 down to 18.6. Batch and Isolate on their own are within the noise between runs. Notice none of them reaches the budget alone. Let's see it. First, X-ray: a model of what Impeller does with a path, the same steps from the tessellation slide, built from the exact paths we send it. It costs work of its own, so it goes off before we judge anything. Then I turn the fix on.

>>> DEMO, phone: X-ray on, point at the lens, X-ray off. Then turn on Simplify paths. No phone: play 07-xray.mp4, then 08-simplify-paths.mp4.

**Slide 19: One pixel column. 25 points.**

Why does Simplify win? Look at one pixel column of one line. Each line in the demo is 8,000 points, on a chart about 316 pixels wide. That's 25 points for every pixel column. Every white dot here is a real point from the demo, and the grid behind them is the screen's pixels. All of that lands in one column. Nobody can see 25 points in one column, but the CPU still tessellates every one of them, on every frame.

**Slide 20: Fix 1: Simplify paths.**

So keep only what you can see. CLICK: keep the lowest and highest in each column, build the path once, then only move it. Look at the two charts. Can you see the difference? Path points go from 130,000 to 12,000.

Each line goes from 8,000 points to 632. Both bars drop: raster 29.7 to 18.6, UI 15.9 to 6.3. Raster, because there's less to tessellate. UI by even more, which surprised me: building an 8,000-point path in Dart every frame was most of the UI time.

**Slide 21: Fix 2: Batch draws.**

Fix 2. >>> DEMO, phone: turn on Batch draws. Imagine going to the shop 480 times, once per item, when you could take a list and go once. The heat strip was 480 segments, each its own path, its own paint and its own draw.

CLICK: now every segment is two triangles, all in one drawVertices call. Same picture. Draw calls go from 640 to 161. But it's a smaller raster win, 18.6 to 13.7, because on Vulkan a draw is a few small commands, not a trip to the driver. The count starts at 640, not 624, because Fix 1 draws each line twice to cover the scroll.

**Slide 22: Fix 3: Glow without saveLayer.**

Fix 3 cuts what's left in half. >>> DEMO, phone: turn on Glow without layers. Look at the picture: each glowing dot gets its own layer, placed by the demo's own formula. Each glowing dot was a saveLayer with a blur: the offscreen pass from a few slides ago, 64 times a frame. Now zero. Same glow, as a radial gradient, in the main pass. Raster goes from 13.7 to 6.6, and the trace shows two queue submits per frame become one. Here's what surprised me: the raster thread was busy the whole time, not waiting for the GPU. So on this phone the layers cost CPU time first.

And you may have this in your own app. The Flutter docs list Opacity, ShaderMask, ColorFilter and Clip.antiAliasWithSaveLayer as things that can trigger a saveLayer. They aren't banned. Just check before you put one high up in the tree: DevTools can highlight offscreen layers. For a simple shape, a semi-transparent colour often does the job, as long as nothing overlaps.

**Slide 23: Fix 4: A RepaintBoundary, on its own?**

Think of a wall with a picture on it: when the picture changes, you don't repaint the wall. VOTE: the grid and labels are redrawn every frame, so wrap them in a RepaintBoundary. Hands up: how much did that save at 8×?

CLICK: almost nothing. A grid is nothing next to 130,000 path points. Fix the big cost first.

>>> DEMO, phone: turn on Isolate repaints.

Once the other fixes are in, it pays off. Grid repaints go from 120 a second to zero. UI drops from 4.4 to 3.4 milliseconds. And raster barely moves: 6.6 to 6.5.

CLICK: that's the point, especially if you learned Flutter on Skia. There's no raster cache to reuse the layer, so the raster thread still draws it every frame. On Impeller a RepaintBoundary saves Dart work, not GPU work.

**Slide 24: Four fixes. From 36 fps to 120.**

CLICK through each fix, five times: raster from 30 milliseconds to six and a half. UI from 16 to three and a half. From about 36 frames a second to the full 120. Nothing here was clever. Fewer points, fewer draws, no offscreen layers, no pointless repainting. Impeller took shader compilation out of the frame. You still pay for every point, every draw and every layer you ask for.

### 29:30 Your own shader

**Slide 25: Your effects can be pre-compiled too.**

One more pattern, for the pre-compiled part. Everything Impeller drew in both demos ran on shaders compiled when the engine was built. Your own effects can join that path: write a fragment shader, list it in pubspec, load it once, and only set uniforms in paint.

And here's what the build did with this 500-byte file: a 4-kilobyte bundle. SPIR-V for Vulkan. GLSL for Impeller's OpenGL backend. And SkSL for Skia, as source text, which Skia still compiles on the phone the first time it's drawn. Same file, two engines: the whole talk in one asset. I didn't time this shader on the phone, so I won't quote a speed.

### 30:30 Prove it

**Slide 26: DevTools: which thread, then which code.**

How do you find all this on your own app? Always in profile mode, on a real device. This shot is an emulator in debug mode, so ignore its milliseconds. I'm showing you where to look. [With a phone attached, open DevTools on the live app and show this for real, in profile mode.]

Each pair is one frame. Red is late. Raster is the taller one, so that's where I look first. Select a frame, and Timeline Events tells me which code, because I wrapped my painters in named spans. That's the whole method, and it's the one we just used: which thread, which event, which code, one fix, measure again. DevTools gives you the frame. For the whole system, you need a system trace.

**Slide 27: Systrace, now Perfetto: 5 s of frames.**

Now the system's view, in Perfetto, which replaced Systrace. Every bar here is one real raster frame from five seconds of the broken chart. Every one is far above the 8.3 line. It never rests.

CLICK: all four fixes, same scale. Short bars, under the line. 179 frames became 604. In the trace, raster goes from 28 to 4.8 milliseconds, and almost all of that is SurfaceFrame Encode, 27 down to 3.7: Impeller turning our DisplayList into triangles and command buffers. 64 saveLayer down to zero. Two queue submits down to one.

VOTE: so in the broken case, is the raster thread waiting on the GPU? Hands up.

CLICK: no. It's running for 24 of its 28 milliseconds. [Only if it is true for you: going in, I suspected the GPU, and the trace said otherwise.] On this phone the cost is the CPU preparing the frame. I can't show you the GPU side: this phone's driver doesn't expose render stages. If yours does, Perfetto and AGI will show it.

**Slide 28: Read the budget from the trace.**

Now read the budget. Broken: divide a thousand by 28 and you get 36, and we measured 35.5. Now the middle row, halfway through the fixes: UI is inside four milliseconds on 94 percent of frames, and we're still at 70 frames a second, because raster is at 14. A green UI bar proves nothing if raster is red.

CLICK: the slowest thread sets the rate. With all fixes, raster is over the 4 millisecond target on 81 percent of frames but inside 8.3 on 99 percent, and UI plus raster passed 8.3 on more than a quarter of frames, while we averaged 120. That's the overlap from the start of the talk. Four and four is the target for latency. 8.3 per thread is the limit for frame rate. These are trace medians with tracing on; the benchmark figures, 3.4 and 6.5, are p90s with tracing off.

### 34:00 Finish

**Slide 29: Take this home.**

Three honest limits first. Not every fix helped on its own. What the Mali GPU did with those buffers, this phone's driver doesn't show me. And Skia, same phone, same chart: 188 milliseconds broken, 58 with every fix. Impeller made this workload possible. It didn't make it free.

So take this home. One: demystify the engine. Skia compiles in the frame; Impeller compiles ahead, tessellates on the CPU and records explicit command buffers. Two: profile low-level. DevTools for the frame, Perfetto for the system, and the slowest thread sets your frame rate. Three: tame your custom painters, and your own effects as build-time shaders. Prove every fix with numbers.

**Slide 30: Impeller made performance predictable. It didn’t make expensive work free.**

Impeller made performance predictable. It didn't make expensive work free. Thread, event, code, fix, measure: that's the method you can take into production. The repo has the app and every script behind these numbers, so run it on your own phone. Thank you.

Leave this slide up during Q&A so people can scan the code.

### 35:15 Q&A backup

**Slide 31: Backup: Shader Storm medians**

Backup for Q&A: press Next past the closing slide, or type the slide number and press Enter.

**Slide 32: Backup: Canvas Thrash medians at 8×**

Backup for Q&A: press Next past the closing slide, or type the slide number and press Enter.

---

## Optional: Perfetto, for Q&A or a live trace

Slide 27 already draws the real frames. If someone asks to see a trace, open these from `traces/` in the
captures folder.

| # | Screen | Do | Say |
|---|---|---|---|
| 24 | `06-dial-1x-to-8x.mp4` | 25 "129,920" |
| 29 | `07-xray.mp4`, then `08-simplify-paths.mp4` | 30 "Fix 1" |
| 27 | "Which fix helps raster most, on its own?" | Simplify paths, 18.6 ms from 29.7. Batch draws barely moves it |
| 23 | Perfetto: `perfetto-system/thrash-trace-none.txt` | Pin the app's main thread and `1.raster`. Zoom to 3–4 frames. | "This is the broken chart at 8×, as the system sees it. Here's the main thread, the work DevTools calls UI. And here's `1.raster`: long slices, back to back. It never rests." |
| 24 | Same | Click one `GPURasterizer::Draw` slice, expand to `SurfaceFrame::Encode`. | "Each raster frame is 28 milliseconds, and 27 of them are this: `Encode`. That's Impeller turning our DisplayList into triangles and command buffers, on the CPU." |
| 25 | Same | Search `Canvas::saveLayer`, then `QueueSubmit`. | "Sixty-four `saveLayer` per frame, our glowing dots. And two queue submissions per frame. Those are the explicit command buffers going to the GPU." |
| 26 | Same | Select a frame on `1.raster`; show the thread-state track (Running vs Sleeping). | "And the thread state: running. Not sleeping, not waiting for the GPU. On this phone, the cost is the CPU preparing the frame." |
| 27 | Perfetto: `perfetto-system/thrash-trace-all.txt` | Same zoom. | "All four fixes. Four point eight milliseconds a frame, zero layers, one submission, and 604 frames in five seconds: 120 frames a second." |
| 28 | Perfetto: `dart-timeline/devtools-timeline-8x-broken.perfetto-trace` | Search `KILN::Thrash`. | "This is the Dart timeline, the same events DevTools' Performance page reads, with paint tracking on. Our painters are named: `grid`, `strip`, `lines`, `dots`. The grid paints every frame." |
| 29 | Perfetto: `dart-timeline/devtools-timeline-8x-isolate.perfetto-trace` | Search `KILN::Thrash::grid`. | "Isolate repaints on. Search for the grid: nothing. That's what a precise repaint boundary looks like in a trace: the event that shouldn't be there is gone." |

## Say it precisely

Senior engineers will catch loose wording. These are the statements most likely to be
challenged.

| Say | Don't say | Why |
|---|---|---|
| "Budget about 4 ms UI and 4 ms raster for single-frame latency" | "Each thread must be under 4 ms or the frame drops" | Threads pipeline; each can reach 8.3 ms at 120 Hz without dropping, at the cost of latency and headroom. Measured: fixed raster is over 4 ms on 81% of frames, at 120 fps |
| "The slowest thread sets the frame rate" (when it is over 8.3 ms) | "UI plus raster must fit in 8.3 ms" | Measured: 35.5 fps at 27.9 ms raster, 70.4 fps at 13.8 ms; and 120 fps with UI + raster over 8.3 ms on 28% of frames |
| "These budget shares come from traces, and tracing slows frames" | Quoting them as the benchmark medians | Bench medians are separate: UI 3.4 ms, raster 6.5 ms p90 |
| "Impeller has no raster cache" | "RepaintBoundary caches it" | Impeller draws every layer every frame; the boundary saves Dart re-recording |
| "We keep at most two points per pixel column" | "We cache the path" | The win is less geometry |
| "Impeller builds pipelines from precompiled shaders, mostly at startup, the rest on first use" | "Impeller never does anything at runtime" | Storm measured 40 pipelines built in the reveal frame, about 2 ms each. Impeller's README states the goal as building them up front; the trace shows some still built in the frame |
| "Impeller tessellates on the CPU. Game engines often use the GPU for it" | "The GPU tessellates the path" | Impeller has no tessellation shader stage: `impeller/core/shader_types.h`. Tessellation shaders are optional in general, so say "often" |
| "A path is what you ask for; tessellation is the work Impeller does with it" | "Paths are tessellation" | A path is the input. Tessellation is CPU work on `1.raster`, every frame |
| "At least 256,000 vertices a frame, by the engine's stroke rule" | "We measured 256,000 vertices" | 16 × 8,000 × 2 is worked out from `stroke_path_geometry.cc`; Impeller does not report its vertex count to Dart |
| "A custom `.frag` is precompiled for Impeller; Skia gets SkSL text and compiles it on the device" | "A custom shader means no runtime compilation on any engine" | The APK bundle contains SPIR-V, GLSL ES and SkSL; Skia compiles the SkSL at first use |
| "This is the pattern; we didn't time a custom shader on the phone" | Any millisecond figure for the custom shader | No on-device measurement exists for it |
| "Command buffers are recorded on the raster thread and executed by the GPU asynchronously" | "Impeller renders on the GPU thread" | Flutter has no GPU thread |
| "On this phone the raster thread was CPU-bound" | "The GPU was the bottleneck" | `1.raster` was running 24 of 28 ms on the median frame, and 70–99% across frames |
| "The layers cost raster-thread time; the GPU-side cost is the model" | "We measured 64 extra render passes on the GPU" | GPU render stages are not available on this phone |
| "Android 10 is the minimum for Impeller. The engine then checks the device, and picks Vulkan or OpenGL ES" | "Android 10+ means Vulkan" or "Skia is gone from Android" | [Fact check](fact-check.md#which-backend-an-android-phone-gets). Below API 29: Skia on OpenGL ES. API 29+, a check fails: Impeller on OpenGL ES. Web also still uses Skia |
| "Vulkan on Android, Metal on iOS and macOS" | "Impeller runs on Vulkan", with no platform | iOS has no Vulkan path |
| "The source is compiled ahead of time; on Vulkan the driver finishes the job when a pipeline is built" | "Impeller never compiles anything at runtime" | The 2.2 ms per pipeline is that driver step. Vulkan's docs call it shader compilation |
| "Overdraw costs work, and the engine and GPU skip some of it" | "A Stack of two full-screen Containers is wasteful" | Impeller merges a full-screen solid colour into the clear. Overdraw isn't measured in the demo |
| "8,000 points is my demo's stress setting" | Implying Flutter has a limit at that number | `pointsPerLine = 1000 × level` in the demo app |
| "Dart runs on the platform main thread since 3.29; DevTools calls it UI" | "The UI thread" as a separate thread | The threads were merged in 3.29 |
| "Impeller is more predictable" | "Impeller is always faster" | In-session repeats were faster on Skia (18 vs 45 ms) |
| "Vulkan cost is the volume of what we record" | "Vulkan is slow" | Vulkan removes hidden driver work and exposes your call count instead |
| "Both APKs use the same Flutter SDK; the Skia flavor opts out of Impeller" | "The Skia app is an old Flutter version" | One SDK removes the biggest confounder |
| Live: "The scoreboard is from my test phone; this phone will differ." Recording: "This is a recording from my test phone" | Calling a recording live, or a slide number this phone's result | The scoreboard is medians from the Infinix, without recording |

## Fallback cues

| If… | Then… |
|---|---|
| A video won't play | Show the matching slide screenshot and narrate from the script; the numbers are on the slide |
| ui.perfetto.dev won't load (no network) | Use slide 27, which draws the real frames. Open the tabs before the talk: once loaded, the page works offline |
| Running over time | Use the ⏱ cuts; then shorten Q&A |
| No phone, and someone asks to see it live | "These recordings are from my test phone; the repo has the scripts to reproduce every number on yours" |
