#!/usr/bin/env python3
"""Summarises first-use shader and pipeline work in a text system trace.

usage: python3 tool/benchmark/trace_summary.py <trace.txt>

Reads the output of `adb shell atrace --async_stop` from an app started with
`--ez trace-systrace true` (Skia also needs `--ez trace-skia true`). Reports the
slowest raster frame, Skia program builds, Impeller pipeline builds, which thread
ran them, and how the raster thread spent the slowest frame.
"""

import collections
import re
import sys

MARK = re.compile(
    r"^\s*(?P<thread>.+?)-(?P<tid>\d+)\s+\(\s*(?:\d+|-+)\).*?\s(?P<ts>\d+\.\d+): "
    r"tracing_mark_write: (?P<phase>[BE])(?:\|\d+)?(?:\|(?P<name>.*))?$"
)
SWITCH = re.compile(
    r"\[(?P<cpu>\d+)\].*?\s(?P<ts>\d+\.\d+): sched_switch: .*?prev_pid=(?P<prev>\d+) "
    r"prev_prio=\d+ prev_state=(?P<state>\S+) ==> .*?next_pid=(?P<next>\d+)"
)
FREQ = re.compile(r"\s(?P<ts>\d+\.\d+): cpu_frequency: state=(?P<khz>\d+) cpu_id=(?P<cpu>\d+)")

FRAME = "GPURasterizer::Draw"
SKIA_PROGRAM = "GrGLProgramBuilder::finalize"
IMPELLER_PIPELINE = "PipelineVK::Create"

Span = collections.namedtuple("Span", "thread name start ms depth")


def read(path):
    """Returns (spans, raster tid, sched switches, cpu frequency changes)."""
    stacks = collections.defaultdict(list)
    spans, switches, freqs = [], [], collections.defaultdict(list)
    raster_tid = None
    with open(path, errors="replace") as trace:
        for line in trace:
            m = MARK.match(line)
            if m:
                ts = float(m["ts"]) * 1000
                if m["thread"] == "1.raster":
                    raster_tid = m["tid"]
                if m["phase"] == "B":
                    stacks[m["tid"]].append((m["name"] or "", ts, m["thread"]))
                elif stacks[m["tid"]]:
                    name, start, thread = stacks[m["tid"]].pop()
                    spans.append(Span(thread, name, start, ts - start, len(stacks[m["tid"]])))
                continue
            m = SWITCH.search(line)
            if m:
                switches.append((float(m["ts"]) * 1000, int(m["cpu"]), m["prev"], m["state"], m["next"]))
                continue
            m = FREQ.search(line)
            if m:
                freqs[int(m["cpu"])].append((float(m["ts"]) * 1000, int(m["khz"])))
    return spans, raster_tid, switches, freqs


def inside(spans, frame, name):
    end = frame.start + frame.ms
    return [s for s in spans if name in s.name and frame.start <= s.start <= end]


def thread_states(switches, tid, frame):
    """Milliseconds the thread spent running, and off-CPU by state, during the frame."""
    start, end = frame.start, frame.start + frame.ms
    running, off = 0.0, collections.Counter()
    on_at = off_at = off_state = None
    cpus = collections.Counter()
    for ts, cpu, prev, state, nxt in switches:
        if ts > end:
            break
        if nxt == tid:
            if off_at is not None and ts > start:
                off[off_state] += ts - max(off_at, start)
            on_at, off_at = max(ts, start), None
            if ts >= start:
                cpus[cpu] += 1
        elif prev == tid:
            if on_at is not None and ts > start:
                running += ts - on_at
            on_at, off_at, off_state = None, ts, state
    if on_at is not None:
        running += end - on_at
    return running, off, cpus


def freq_at(freqs, cpu, ts):
    khz = None
    for at, value in freqs.get(cpu, []):
        if at > ts:
            break
        khz = value
    return khz


def main(path):
    spans, raster_tid, switches, freqs = read(path)
    frames = sorted((s for s in spans if s.name == FRAME), key=lambda s: s.start)
    if not frames:
        sys.exit("no Flutter raster frames found: was the app started with --ez trace-systrace true?")
    slowest = max(frames, key=lambda s: s.ms)
    at = frames.index(slowest)

    print(f"raster frames: {len(frames)}, slowest {slowest.ms:.1f} ms")
    print("frames around it (ms):", " ".join(f"{f.ms:.1f}" for f in frames[max(0, at - 2):at + 6]))

    for label, name in (("Skia programs built", SKIA_PROGRAM), ("Impeller pipelines built", IMPELLER_PIPELINE)):
        every = [s for s in spans if name in s.name]
        if not every:
            continue
        frame = inside(spans, slowest, name)
        threads = ", ".join(sorted({s.thread for s in every}))
        print(f"{label}: {len(every)} in the trace ({sum(s.ms for s in every):.1f} ms), "
              f"{len(frame)} in the slowest frame ({sum(s.ms for s in frame):.1f} ms), "
              f"average {sum(s.ms for s in every) / len(every):.2f} ms, on {threads}")

    begin = collections.Counter(s.thread for s in spans if s.name == "Animator::BeginFrame")
    if begin:
        print(f"Dart frame work ran on: {begin.most_common(1)[0][0]}")

    if raster_tid and switches:
        running, off, cpus = thread_states(switches, raster_tid, slowest)
        states = ", ".join(f"{state} {ms:.1f} ms" for state, ms in off.most_common()) or "none"
        print(f"1.raster in the slowest frame: running {running:.1f} ms; off CPU: {states}")
        if cpus:
            cpu = cpus.most_common(1)[0][0]
            khz = freq_at(freqs, cpu, slowest.start + slowest.ms / 2)
            if khz:
                print(f"mostly on cpu{cpu} at {khz / 1000:.0f} MHz")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
