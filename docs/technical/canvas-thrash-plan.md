# Canvas Thrash plan

Step 2 of the demo: a live animated canvas that is thrashed until frames go red, then fixed
one cause at a time. It delivers the abstract's remaining promises: thrash a real-time
canvas, tessellation, command buffers, avoiding `saveLayer`, and repaint isolation.

Shader Storm ([note 09](../notes/09-shader-storm-findings.md)) ends with *"if compiling
shaders is no longer the problem, what is?"*. Canvas Thrash answers it.

Items marked 📱 need the 120 Hz stage phone. Tick items as they land.

## Decisions

- Four fixes plus a thrash dial (1×, 2×, 4×, 8×).
- Market-themed canvas from data generated in the app; no network.
- The Markets button leaves the home screen; its code stays.
- X-ray mode is included and presented as a **model** of Impeller's tessellator built from
  the paths the app draws, not as the engine's own output.
- Docs carry numbers only after measuring on the stage phone.

## The screen

```text
┌──────────────────────────────────┐
│ Canvas Thrash          Impeller  │
│ 120 Hz · 8.3 ms budget           │
├──────────────────────────────────┤
│   live canvas, always animating  │
│   price lines, glowing dots,     │
│   heat strip, grid and axes      │
├──────────────────────────────────┤
│ UI      ▁▁▂▁▁▁▂▁     peak 3.1 ms │
│ RASTER  ▅▇█▇▆█▇█    peak 24.0 ms │
├──────────────────────────────────┤
│ THRASH   [1×] [2×] [4×] [8×]     │
│ FIXES                            │
│ ○ Simplify paths       raster    │
│ ○ Batch draws          raster    │
│ ○ Glow without layers  raster    │
│ ○ Isolate repaints     UI        │
│ ○ X-ray                          │
└──────────────────────────────────┘
```

## The four fixes

| Fix | Broken | Fixed | Lesson | Lane expected to drop |
|---|---|---|---|---|
| Simplify paths | Each price line is a new path with thousands of points, rebuilt every frame | At most two points per pixel column, rebuilt only when data changes | Impeller tessellates paths into triangles on the CPU, every frame | Raster, some UI |
| Batch draws | Heat strip drawn with one `drawPath` per segment | Whole strip in one `drawVertices` call | Every draw is a command recorded into the command buffer | Raster |
| Glow without layers | Each dot's glow is `saveLayer` plus a blur | Radial gradient, same look, no layer | `saveLayer` adds offscreen render passes | Raster |
| Isolate repaints | Static grid repaints every frame with the lines | Grid behind a `RepaintBoundary`, never repainted | On Impeller this saves Dart work, not GPU work: there is no raster cache | UI |

The "expected" column is a hypothesis until section C measures it.

## A. Build Canvas Thrash

- [x] **A1 · Scene data.** Deterministic made-up market data: price lines, dots, heat strip,
  scaled by the thrash dial.
- [x] **A2 · Layers.** Grid and axes, price lines, glowing dots, heat strip, each with a broken
  and a fixed painter that draw the same picture.
- [x] **A3 · Controls.** Thrash dial, four fix switches, the UI and RASTER lanes and peaks from
  Shader Storm, and a live grid-repaints-per-second counter.
- [x] **A4 · Instrumentation.** `KILN::Thrash::…` timeline markers and a logcat line with the
  fixes, dial level and recent raster and UI times.
- [x] **A5 · Navigation.** Canvas Thrash on the home screen; Markets button removed.
- [x] **A6 · Tests.** Scene, dial and fix switches.

## B. X-ray mode

- [x] **B1 · Triangle model.** Split each path into segments and triangles the way Impeller's
  tessellator does, from the exact paths the canvas draws.
- [x] **B2 · Zoom lens.** A magnified window on part of the canvas showing the triangle wireframe.
- [x] **B3 · Live counters.** Points, triangles per frame and per second, draw calls, offscreen
  layers, repaints.
- [x] **B4 · Tests.** Counts match the geometry.

X-ray adds raster work of its own. Turn it on to explain, off to measure.

## C. Measure on the stage phone

- [x] 📱 **C1 · Step 1 leftover.** Shader Storm bench and 144-tile traces with
  `tool/benchmark`, then update note 09 and the Storm script with the new phone's numbers.
- [x] 📱 **C2 · Thrash benchmark.** At 8×, each fix in turn, three rounds, medians of raster
  and UI time.
- [x] 📱 **C3 · Traces.** Broken vs fixed; look for tessellation and render-pass events on `1.raster`.
- [ ] 📱 **C4 · Tuning.** If a fix's effect is too small to see, adjust the 8× workload. Tune,
  never fake.
  2026-10-31: not tuned. Batch draws is the smallest win (raster 18.6 → 13.7 ms, overlapping
  ranges); the script narrates it as such. Retuning would have invalidated the recorded
  videos and traces. Revisit on the next stage phone.
- [ ] 📱 **C5 · Optional.** Try Android GPU Inspector for the engine's real geometry.

## D. Docs

Concepts are drafted before measuring; numbers are filled in after section C. D1 to D3
are ticked for their concepts; their results sections still wait for section C.

- [x] **D1 · Note 10, Canvas Thrash explained.** Each fix in plain words, with diagrams: path to
  triangles on the CPU, draws to the command buffer, `saveLayer` to render passes,
  `RepaintBoundary` vs a raster cache, what X-ray models and what it does not, measured results.
- [x] **D2 · Existing notes.** 03 Impeller internals, 04 Vulkan primer, 07 Optimisation
  patterns, glossary.
- [x] **D3 · Screens and indexes.** Section 9 in screens.md, the docs README, the benchmark README.
- [ ] **D4 · Stage script.** `talk/canvas-thrash-script.md`: what to click and say, and likely
  questions from senior engineers.

## E. Rebuild the talk (step 3)

- [ ] **E1 · Run of show.** Rewrite `talk/demo-script.md`: Shader Storm, Canvas Thrash,
  Perfetto walkthrough, takeaways.
- [ ] **E2 · Abstract alignment.** Every promise in the abstract points at a real demo moment.
- [ ] **E3 · Stage runbook.** Setup checklist, fixed refresh rate, failure recovery.
- [ ] **E4 · Slides.** Two Shader Storm trace slides, one Canvas Thrash trace slide.
- [ ] 📱 **E5 · Rehearsal.** Three runs on the stage phone, backup videos, exported traces.

## Order

```text
Without the phone    A1 to A6, then B1 to B4, then D1 to D3 drafts
With the phone       C1, C2 to C4, numbers into D1 to D3, D4, C5 if time allows
After that           E1 to E5
```

## Learning path

Read, in order:

1. [01 · How Flutter runs](../notes/01-how-flutter-runs.md): threads, and what the UI and raster lanes are.
2. [05 · Frame scheduling](../notes/05-frame-scheduling.md): budgets, pipelining, ways a frame is late.
3. [09 · Shader Storm findings](../notes/09-shader-storm-findings.md): what was measured so far.
4. [03 · Impeller internals](../notes/03-impeller-internals.md) and
   [04 · Vulkan primer](../notes/04-vulkan-primer.md): tessellation, command buffers, render passes.
5. Note 10, once drafted.

Practise:

- Run `tool/benchmark/storm_bench.sh`, open a trace in [Perfetto UI](https://ui.perfetto.dev)
  and find `GrGLProgramBuilder::finalize` on `1.raster`.
- In Canvas Thrash at 8×, turn on one fix at a time and say out loud which lane dropped and why.
