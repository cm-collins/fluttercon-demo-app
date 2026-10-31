# Canvas Thrash script

What is on screen, what you do, and what you say for the drawing-cost segment. Quoted lines
are the intended wording; say them in your own voice, but keep the numbers and claims exactly
as written.

**Length:** about 7 minutes. **Phone:** the stage phone, **Kiln Impeller** only. **Follows:**
[Shader Storm](shader-storm-script.md), which ends on *"So if compiling shaders is no longer
the problem, what is? Let's go break something."* What every panel means and why each fix
works: [10 · Canvas Thrash explained](../notes/10-canvas-thrash.md).

Counter values are exact: the scene is generated from the dial level, so they are the same
on every run on the stage phone. Timings are medians from `thrash_bench.sh`; see
[Measured evidence](#measured-evidence). If you demo on a different phone, re-run the bench
there and replace the timings.

## Before you walk on

1. Screen fixed at **120 Hz** for Kiln (Settings → Display → Screen Refresh Rate → **High**,
   then **Customize App Refresh Rate** → Kiln → 120 Hz). Check the header reads
   **120 Hz · 8.3 ms budget**.
2. Kiln Impeller open on the home screen. Canvas Thrash always opens at **1×** with every fix
   and X-ray off; if you rehearsed on it, go back to Home and open it again.
3. Tracing **off**. X-ray **off** except in step 4.

## How to read this script

- **Screen** is what the audience sees.
- **Do** is your action.
- **Say** is the line.

The fixes are switched on **top to bottom, in the order they appear on screen**, and each one
stays on. The counter values below assume that order.

## 1. Pick up from Shader Storm (0:20)

**Do:** Home → **Canvas Thrash**.

**Say:**

> "Impeller fixed shader compilation. So we're done? This is a live trading chart: price
> lines, glowing markers, a heat strip, all animating. Same phone, same 8.3-millisecond
> budget."

## 2. Calm (0:30)

**Screen:** 1×. Lanes mostly green. Counter line: **draws 78 · layers 8 · path points
2,240 · grid repaints 120/s**.

**Say:**

> "Same two lanes as before. **UI** is my Dart code: building the frame and recording what to
> draw. **RASTER** is the engine turning that recording into GPU work. At this size,
> everything fits in the budget."

## 3. Break it (0:45)

**Do:** Tap **2×**, **4×**, then **8×**. Stop on 8× and let it run red for a few seconds.

**Say:**

> "Now I'll do what real apps do: more data. Each step doubles the lines, the points and the
> segments.
>
> Everything is red. And look at *which* lane: RASTER is far taller than UI. My Dart code
> finishes; the engine is the one struggling. Nothing is compiling here. This is pure
> **drawing cost**, and no renderer saves you from asking it to draw too much."

**Do:** Point at the counter line: **draws 624 · layers 64 · path points 129,920**, grid
repaints around **40–50/s**.

**Say:**

> "This is the bill for one frame. **624 draw calls. 64 offscreen layers. Almost 130,000
> path points.** And the grid behind it, which never changes, is redrawn every frame. Read
> that counter as the frame rate: under 50 frames a second, on a 120 hertz screen."

## 4. Fix 1 · Simplify paths (1:15)

**Say:**

> "First suspect: points. Every line has 8,000 of them. This chart is only a few hundred
> pixels wide, so that's about 25 points for every pixel column. You cannot see 25 points in
> one column."

**Do:** Turn on **X-ray**. Point at the lens.

**Say:**

> "This is what Impeller does with a path. The GPU only draws triangles, so Impeller cuts
> every stroke into triangles first: **on the CPU, on the raster thread, every frame.** That
> number is the triangle count, live. This lens is a model of that work, built from the exact
> paths the chart draws."

**Do:** Turn **X-ray off**.

**Say:**

> "X-ray costs work of its own, so it goes off before we judge anything."

**Do:** Turn on **Simplify paths**. Counter: path points **12,032**, draws **640**.

**Say:**

> "The fix: keep two points per pixel column, the lowest and the highest, so the line looks
> identical. Build those paths once and slide them sideways instead of rebuilding them.
> **130,000 points down to 12,000.** Draws went *up* by 16, because each line is drawn twice
> to cover the wrap at the edge, and it doesn't matter: points were the cost, not draws.
> Watch **both** lanes drop: building an 8,000-point path every frame was Dart work too.
> UI from 16 milliseconds to about 6. Raster from 30 to about 19."

## 5. Fix 2 · Batch draws (0:45)

**Say:**

> "The heat strip at the bottom: 480 segments, each its own path and its own draw call."

**Do:** Turn on **Batch draws**. Counter: draws **161**, path points **10,112**.

**Say:**

> "Now every segment is two triangles, all of them in **one `drawVertices` call**. Draws
> from 640 to **161**. Every draw call carries a fixed cost, so the engine does less
> bookkeeping for the same picture. And these are triangles already, so there's nothing left
> to cut up. Raster drops to about 14 milliseconds: the smallest win of the four. On Vulkan a
> draw call is cheap; it's a few commands in a command buffer, not a trip to the driver."

## 6. Fix 3 · Glow without layers (1:00)

**Say:**

> "Those glowing markers. Each one is a `saveLayer` with a blur. For every marker Impeller
> starts a separate offscreen render pass, draws the dot, blurs it, and composites it back.
> **64 extra render passes per frame.**"

**Do:** Turn on **Glow without layers**. Counter: layers **0**.

**Say:**

> "Same soft glow, drawn as a circle with a radial gradient that fades to transparent: one
> ordinary draw, no layer. Layers: **zero**. Look at the markers: they look the same.
> Raster: from 14 milliseconds to under 7. The biggest raster win.
>
> And here's what the trace says about *where* that cost was. The raster thread was busy the
> whole time, not waiting for the GPU. Setting up 64 offscreen passes, 64 blurs, 64
> composites is CPU work on the raster thread before the GPU sees anything. The layers also
> split every frame's GPU work into two queue submissions instead of one."

## 7. Fix 4 · Isolate repaints (0:45)

**Say:**

> "The last one is on the **UI** side. Watch *grid repaints*. The grid never moves, but it
> repaints every frame, and it lays out its price labels again each time, because it shares a
> canvas with the animation."

**Do:** Turn on **Isolate repaints**. Counter: grid repaints **0/s**.

**Say:**

> "Put the grid on its own layer with a `RepaintBoundary`. It is painted once and reused.
> Grid repaints: **zero**. UI from 4.4 milliseconds to 3.4: under the 4-millisecond
> target."

## 8. The point (0:45)

**Screen:** 8×, all four fixes on.

**Say:**

> "Same picture. Same 8× data. Raster went from 30 milliseconds to six and a half. UI from
> 16 to three and a half. We went from about 36 frames a second to the full 120.
>
> Nothing here was clever. Fewer points, fewer draw calls, no offscreen layers, no
> pointless repainting.
>
> And the order mattered: I looked at **which lane** was red before touching code. RASTER
> red: you're asking the engine to draw too much. UI red: your Dart is doing too much.
> Impeller took shader compilation out of the frame. **You still pay for every point, every
> draw and every layer you ask for.**"

## 9. Hand-off (0:10)

**Say:**

> "Now let's look at the same thing inside a real trace."

**Do:** Move to the Perfetto walkthrough.

## Questions to expect

**"Isn't simplifying the data cheating?"**
> "No. I only drop points that land in the same pixel column, and I keep each column's lowest
> and highest value, so every peak and dip is still drawn."

**"Why not let the raster cache handle the grid?"**
> "Impeller has no raster cache. A `RepaintBoundary` gives the grid its own layer so it isn't
> re-recorded every frame, but nothing caches it as a picture the way Skia's raster cache
> did."

**"Are those X-ray triangles Impeller's real triangles?"**
> "No, it's a model of how Impeller's tessellator splits strokes, run on the same paths the
> chart draws. The real geometry would come from Android GPU Inspector."

**"Would this be different on Skia?"**
> "Much worse. Same phone, same 8×: Skia's raster thread takes about **190 milliseconds**
> a frame broken, and still **58** with every fix on, against Impeller's six and a half. In
> the Skia trace almost all of it is the 32 line draws, each one followed by a pixel upload,
> which looks like Skia drawing each line into an image on the CPU. Impeller turns the same
> line into triangles. On Skia no single fix helped; only all of them together did."

**"So is the GPU the bottleneck?"**
> "Not on this phone. In every trace the raster thread is running on the CPU 90 percent of
> the frame or more; it almost never waits for the GPU. The cost is Impeller encoding the
> frame: tessellating, setting up passes, recording command buffers. What the GPU does with
> them, I can't show you: this phone's driver doesn't expose GPU render stages to Perfetto.
> On a Pixel you can trace that too."

**"Why does Simplify paths add draw calls?"**
> "Each line is drawn twice to cover the wrap as it scrolls. Sixteen extra draws are cheap;
> 118,000 fewer points are not."

## Counter values on the stage phone

At 8×, fixes switched on top to bottom. Path point totals depend on the canvas width, so
they apply to the stage phone only.

| After | Draws | Layers | Path points | Grid repaints |
|---|---|---|---|---|
| 8×, no fixes | 624 | 64 | 129,920 | every frame (40–50/s) |
| + Simplify paths | 640 | 64 | 12,032 | every frame |
| + Batch draws | 161 | 64 | 10,112 | every frame |
| + Glow without layers | 161 | 0 | 10,112 | every frame |
| + Isolate repaints | 161 | 0 | 10,112 | 0/s |

At 1× with no fixes: 78 draws, 8 layers, 2,240 path points.

## Measured evidence

Stage phone: Infinix X6873, Mali-G615 MC6, Vulkan 1.3, Android 16, 120 Hz. Flutter 3.47.8,
Impeller profile build. `tool/benchmark/thrash_bench.sh 3`, tracing off, X-ray off. Frame
p90 over the last 120 frames, median of 3 rounds (range).

| 8×, fixes on | UI | Raster |
|---|---|---|
| none | 15.9 ms (15.6–16.3) | 29.7 ms (22.8–30.9) |
| + Simplify paths | 6.3 (5.1–6.9) | 18.6 (13.5–18.7) |
| + Batch draws | 4.9 (3.5–5.5) | 13.7 (13.1–18.1) |
| + Glow without layers | 4.4 (4.2–4.5) | 6.6 (6.6–6.8) |
| + Isolate repaints | 3.4 (3.3–3.4) | 6.5 (6.2–6.7) |

Each fix on its own: Simplify paths 6.3 / 18.6, Batch draws 14.7 / 28.6, Glow without layers
14.8 / 21.2, Isolate repaints 16.9 / 25.2 (UI / raster). Isolate repaints alone does not
help at 8×: with 130,000 path points per frame, the grid is not the cost. It pays off once
the rest is fixed.

System traces, 5 s each (`tool/benchmark/thrash_trace.sh`):

| 8× | Raster frame p50 | `SurfaceFrame::Encode` p50 | `saveLayer` / frame | `QueueSubmit` / frame | Frames in 5 s |
|---|---|---|---|---|---|
| no fixes | 27.9 ms | 27.1 ms | 64 | 2 | 179 |
| Simplify + Batch | 13.8 ms | 12.9 ms | 64 | 2 | 355 |
| all fixes | 4.8 ms | 3.7 ms | 0 | 1 | 604 |

Dart timeline with paint tracking: `KILN::Thrash::grid` appears every frame without
Isolate repaints and never with it.

Skia flavor, same bench (UI / raster p90, median of 3): no fixes 21.8 / 188.4 ms; every fix
alone and Simplify + Batch stay at 184–202 ms raster; + Glow 3.9 / 61.5; all fixes
3.9 / 57.7. Skia trace with all fixes: 47 of 53 ms per raster frame inside 32
`SkCanvas::drawPath` calls, with about 31 `GrGpu::writePixels` per frame.
