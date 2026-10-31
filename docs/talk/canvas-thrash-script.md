# Canvas Thrash script

What is on screen, what you do, and what you say for the drawing-cost segment. Quoted lines
are the intended wording; say them in your own voice, but keep the numbers and claims exactly
as written.

**Length:** about 7 minutes. **Phone:** the stage phone, **Kiln Impeller** only. **Follows:**
[Shader Storm](shader-storm-script.md), which ends on *"So if compiling shaders is no longer
the problem, what is? Let's go break something."* What every panel means and why each fix
works: [10 · Canvas Thrash explained](../notes/10-canvas-thrash.md).

> **Status.** The counter values below are exact: the scene is generated from the dial level,
> so they are the same on every run on this phone. Timings marked **⟨C2⟩** wait for the
> Canvas Thrash benchmark ([plan](../technical/canvas-thrash-plan.md), item C2). Until then,
> describe what the lanes do and say no timing numbers.

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
> ⟨C2: UI from X to Y ms, raster from X to Y ms⟩"

## 5. Fix 2 · Batch draws (0:45)

**Say:**

> "The heat strip at the bottom: 480 segments, each its own path and its own draw call."

**Do:** Turn on **Batch draws**. Counter: draws **161**, path points **10,112**.

**Say:**

> "Now every segment is two triangles, all of them in **one `drawVertices` call**. Draws
> from 640 to **161**. Every draw call carries a fixed cost, so the engine does less
> bookkeeping for the same picture. And these are triangles already, so there's nothing left
> to cut up. ⟨C2⟩"

## 6. Fix 3 · Glow without layers (1:00)

**Say:**

> "Those glowing markers. Each one is a `saveLayer` with a blur. For every marker Impeller
> starts a separate offscreen render pass, draws the dot, blurs it, and composites it back.
> **64 extra render passes per frame.**"

**Do:** Turn on **Glow without layers**. Counter: layers **0**.

**Say:**

> "Same soft glow, drawn as a circle with a radial gradient that fades to transparent: one
> ordinary draw, no layer. Layers: **zero**. Look at the markers: they look the same. ⟨C2⟩"

## 7. Fix 4 · Isolate repaints (0:45)

**Say:**

> "The last one is on the **UI** side. Watch *grid repaints*. The grid never moves, but it
> repaints every frame, and it lays out its price labels again each time, because it shares a
> canvas with the animation."

**Do:** Turn on **Isolate repaints**. Counter: grid repaints **0/s**.

**Say:**

> "Put the grid on its own layer with a `RepaintBoundary`. It is painted once and reused.
> Grid repaints: **zero**. ⟨C2: UI from X to Y ms⟩"

## 8. The point (0:45)

**Screen:** 8×, all four fixes on.

**Say:**

> "Same picture. Same 8× data. ⟨C2: RASTER from X to Y ms, UI from X to Y ms⟩
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
> "The broken patterns are expensive on both. The bill shifts: offscreen layers and path
> work cost different amounts on each engine. This segment runs on Impeller because that's
> what ships by default."

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
