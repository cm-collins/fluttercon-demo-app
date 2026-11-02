#!/usr/bin/env python3
"""Summarises steady-state Canvas Thrash frames in a text system trace.

usage: python3 tool/benchmark/thrash_trace_summary.py <trace.txt>

Reads the output of thrash_trace.sh. Reports raster frame times on 1.raster, the
engine phases inside each frame, and per-frame counts of offscreen layers and
Vulkan command buffers, so a broken and a fixed trace can be compared side by side.
Also reads the frame budget: the share of frames inside the ~4 ms target and the 8.33 ms
limit on each thread, and the frame rate next to what the raster thread alone would allow.
Tracing slows frames, so use thrash_bench.sh for the headline numbers.
"""

import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_summary import FRAME, read  # noqa: E402

PHASES = ["SurfaceFrame::BuildDisplayList", "SurfaceFrame::Encode", "SurfaceFrame::Submit"]
COUNTED = ["Canvas::saveLayer", "AllocateCommandBuffers", "QueueSubmit"]
UI_FRAME = "Animator::BeginFrame"
# BeginFrame also fires as a short no-op; real frames are longer. With this floor, the UI
# frame count matches the raster frame count in the Canvas Thrash traces.
UI_FRAME_MIN_MS = 0.3
TARGET_MS = 4.17
LIMIT_MS = 8.33


def pct(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))] if values else 0.0


def inside(values, limit):
    return 100 * sum(1 for v in values if v <= limit) / len(values) if values else 0.0


def budget_line(name, values):
    return (
        f"  {name:<7} p50 {pct(values, .5):5.1f} ms  p90 {pct(values, .9):5.1f} ms  "
        f"<= {TARGET_MS}: {inside(values, TARGET_MS):3.0f}%  <= {LIMIT_MS}: {inside(values, LIMIT_MS):3.0f}%"
    )


def main(path):
    spans, raster_tid, _, _ = read(path)
    raster = [s for s in spans if s.thread == "1.raster"]
    frames = [s for s in raster if s.name == FRAME]
    if not frames:
        sys.exit("no raster frames in trace")
    draw = [f.ms for f in frames]
    print(f"raster frames: {len(frames)}, GPURasterizer::Draw p50 {pct(draw, .5):.1f} ms, p90 {pct(draw, .9):.1f} ms")
    for name in PHASES:
        ms = [s.ms for s in raster if s.name == name]
        if ms:
            print(f"  {name:<32} p50 {pct(ms, .5):6.2f} ms  p90 {pct(ms, .9):6.2f} ms")
    for name in COUNTED:
        n = sum(1 for s in spans if s.name == name)
        print(f"  {name:<32} {n / len(frames):6.1f} per frame")
    ui_spans = sorted(
        (s for s in spans if s.name == UI_FRAME and s.ms >= UI_FRAME_MIN_MS),
        key=lambda s: s.start,
    )
    ui = [s.ms for s in ui_spans]
    print("frame budget (traced):")
    if ui:
        print(budget_line("UI", ui))
    print(budget_line("Raster", draw))
    ordered = sorted(frames, key=lambda s: s.start)
    seconds = (ordered[-1].start - ordered[0].start) / 1000
    if seconds > 0:
        fps = (len(ordered) - 1) / seconds
        print(f"  frame rate {fps:.1f} fps; 1000 / raster p50 = {1000 / pct(draw, .5):.1f} fps")
    # Paired by order, so approximate: a pair is one frame's Dart work and raster work.
    pairs = [u + r for u, r in zip(ui, (f.ms for f in ordered))]
    if pairs:
        print(f"  UI + raster p50 {pct(pairs, .5):.1f} ms, <= {LIMIT_MS}: {inside(pairs, LIMIT_MS):.0f}%")


if __name__ == "__main__":
    main(sys.argv[1])
