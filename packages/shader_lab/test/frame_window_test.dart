import 'package:flutter_test/flutter_test.dart';
import 'package:shader_lab/shader_lab.dart';

const Duration budget = Duration(microseconds: 8333);
const int frameUs = 8333;

/// Frame [i] after a trigger at t = 0, costing [costUs] on the raster thread.
FrameSample frame(int i, int costUs, {int buildUs = 2000}) {
  final int start = (i + 1) * frameUs;
  return FrameSample(
    vsyncStartMicros: start,
    rasterFinishMicros: start + costUs,
    build: Duration(microseconds: buildUs),
    raster: Duration(microseconds: costUs),
  );
}

FrameWindowResult? feed(FrameWindow window, List<FrameSample> frames) {
  FrameWindowResult? result;
  for (final FrameSample f in frames) {
    result = window.add(f);
  }
  return result;
}

void main() {
  test('no over-budget frame gives a zero lap time after the settle run', () {
    final FrameWindow window = FrameWindow(budget: budget, triggerMicros: 0);
    final FrameWindowResult? result = feed(window, <FrameSample>[
      for (int i = 0; i < 12; i++) frame(i, 4000),
    ]);

    expect(result, isNotNull);
    expect(result!.timeToSmooth, Duration.zero);
    expect(result.stall, Duration.zero);
    expect(result.worst, const Duration(microseconds: 4000));
    expect(result.frames, 12);
    expect(result.timedOut, isFalse);
  });

  test('stays open until 12 consecutive on-budget frames', () {
    final FrameWindow window = FrameWindow(budget: budget, triggerMicros: 0);
    expect(
      feed(window, <FrameSample>[for (int i = 0; i < 11; i++) frame(i, 4000)]),
      isNull,
    );
    expect(window.isClosed, isFalse);
  });

  test('a compile spike sets lap time to the end of the last slow frame', () {
    final FrameWindow window = FrameWindow(budget: budget, triggerMicros: 0);
    final FrameWindowResult? result = feed(window, <FrameSample>[
      frame(0, 120000),
      frame(1, 30000),
      for (int i = 2; i < 14; i++) frame(i, 4000),
    ]);

    expect(result, isNotNull);
    expect(
      result!.timeToSmooth,
      const Duration(microseconds: 2 * frameUs + 30000 - frameUs),
    );
    expect(
      result.stall,
      const Duration(microseconds: (120000 - 8333) + (30000 - 8333)),
    );
    expect(result.worst, const Duration(microseconds: 120000));
    expect(result.overBudgetFrames, 2);
  });

  test('an on-budget frame between spikes does not reset the lap', () {
    final FrameWindow window = FrameWindow(budget: budget, triggerMicros: 0);
    final FrameWindowResult? result = feed(window, <FrameSample>[
      frame(0, 50000),
      frame(1, 4000),
      frame(2, 20000),
      for (int i = 3; i < 15; i++) frame(i, 4000),
    ]);

    expect(result!.overBudgetFrames, 2);
    expect(
      result.timeToSmooth,
      const Duration(microseconds: 3 * frameUs + 20000 - frameUs),
    );
  });

  test('the slower thread decides the frame cost', () {
    final FrameWindow window = FrameWindow(budget: budget, triggerMicros: 0);
    final FrameWindowResult? result = feed(window, <FrameSample>[
      frame(0, 3000, buildUs: 40000),
      for (int i = 1; i < 13; i++) frame(i, 4000),
    ]);

    expect(result!.worst, const Duration(microseconds: 40000));
    expect(result.overBudgetFrames, 1);
  });

  test('frames that started before the trigger are ignored', () {
    final FrameWindow window = FrameWindow(
      budget: budget,
      triggerMicros: 3 * frameUs,
    );
    final FrameWindowResult? result = feed(window, <FrameSample>[
      frame(0, 90000),
      frame(1, 90000),
      for (int i = 3; i < 15; i++) frame(i, 4000),
    ]);

    expect(result!.timeToSmooth, Duration.zero);
    expect(result.frames, 12);
  });

  test('the frame whose vsync starts at the trigger timestamp is counted', () {
    // Back-to-back frames: the timestamp Dart saw is the previous frame's
    // vsync target, which equals the next frame's vsync start.
    final FrameWindow window = FrameWindow(
      budget: budget,
      triggerMicros: 3 * frameUs,
    );
    final FrameWindowResult? result = feed(window, <FrameSample>[
      frame(1, 4000),
      frame(2, 677000),
      for (int i = 3; i < 15; i++) frame(i, 4000),
    ]);

    expect(result!.worst, const Duration(microseconds: 677000));
    expect(result.overBudgetFrames, 1);
  });

  test('a frame cap closes a burst that never gets under budget', () {
    final FrameWindow window = FrameWindow(
      budget: budget,
      triggerMicros: 0,
      maxFrames: 16,
    );
    final FrameWindowResult? result = feed(window, <FrameSample>[
      for (int i = 0; i < 20; i++) frame(i, 25000),
    ]);

    expect(result!.capped, isTrue);
    expect(result.timedOut, isFalse);
    expect(result.frames, 16);
    expect(result.worst, const Duration(microseconds: 25000));
  });

  test('times out when frames never settle', () {
    final FrameWindow window = FrameWindow(
      budget: budget,
      triggerMicros: 0,
      timeout: const Duration(milliseconds: 100),
    );
    final FrameWindowResult? result = feed(window, <FrameSample>[
      for (int i = 0; i < 20; i++) frame(i, 20000),
    ]);

    expect(result, isNotNull);
    expect(result!.timedOut, isTrue);
    expect(result.frames, lessThan(20));
  });

  test('ignores frames after it closes', () {
    final FrameWindow window = FrameWindow(budget: budget, triggerMicros: 0);
    final FrameWindowResult? first = feed(window, <FrameSample>[
      for (int i = 0; i < 12; i++) frame(i, 4000),
    ]);
    final FrameWindowResult? after = window.add(frame(12, 90000));

    expect(identical(first, after), isTrue);
    expect(after!.worst, const Duration(microseconds: 4000));
  });

  test('budgetFor converts refresh rate to a frame budget', () {
    expect(budgetFor(120), const Duration(microseconds: 8333));
    expect(budgetFor(60), const Duration(microseconds: 16667));
    expect(budgetFor(0), const Duration(microseconds: 16667));
  });
}
