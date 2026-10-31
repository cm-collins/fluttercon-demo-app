#!/usr/bin/env python3
"""Summarises steady-state Canvas Thrash frames in a text system trace.

usage: python3 tool/benchmark/thrash_trace_summary.py <trace.txt>

Reads the output of thrash_trace.sh. Reports raster frame times on 1.raster, the
engine phases inside each frame, and per-frame counts of offscreen layers and
Vulkan command buffers, so a broken and a fixed trace can be compared side by side.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_summary import FRAME, read  # noqa: E402

PHASES = ["SurfaceFrame::BuildDisplayList", "SurfaceFrame::Encode", "SurfaceFrame::Submit"]
COUNTED = ["Canvas::saveLayer", "AllocateCommandBuffers", "QueueSubmit"]
UI_FRAME = "Animator::BeginFrame"


def pct(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))] if values else 0.0


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
    ui = [s.ms for s in spans if s.name == UI_FRAME]
    if ui:
        print(f"UI {UI_FRAME}: {len(ui)} frames, p50 {pct(ui, .5):.1f} ms, p90 {pct(ui, .9):.1f} ms")


if __name__ == "__main__":
    main(sys.argv[1])
