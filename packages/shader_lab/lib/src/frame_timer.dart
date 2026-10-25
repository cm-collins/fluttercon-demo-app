import 'dart:ui' show FramePhase, FrameTiming;

import 'package:flutter/scheduler.dart';

import 'frame_window.dart';

typedef FrameWindowCallback = void Function(FrameWindowResult result);

/// Frame budget for a display refresh rate (8.33 ms at 120 Hz).
Duration budgetFor(double refreshRate) {
  final double hz = refreshRate > 0 ? refreshRate : 60;
  return Duration(microseconds: (1000000 / hz).round());
}

FrameSample sampleFrom(FrameTiming timing) {
  return FrameSample(
    vsyncStartMicros: timing.timestampInMicroseconds(FramePhase.vsyncStart),
    rasterFinishMicros: timing.timestampInMicroseconds(FramePhase.rasterFinish),
    build: timing.buildDuration,
    raster: timing.rasterDuration,
  );
}

/// Runs a [FrameWindow] on frames reported by the engine after [arm].
///
/// The trigger is the raw vsync time of the last frame before the call, which
/// is in the same clock as `FrameTiming`, so frames that were already in
/// flight are excluded. Results arrive when the engine flushes its timing
/// batch, so they lag the screen slightly.
class FrameTimer {
  FrameWindow? _window;
  FrameWindowCallback? _onResult;
  bool _listening = false;

  bool get isArmed => _window != null;

  void arm({
    required Duration budget,
    required FrameWindowCallback onResult,
    Duration timeout = const Duration(seconds: 5),
  }) {
    final SchedulerBinding binding = SchedulerBinding.instance;
    _window = FrameWindow(
      budget: budget,
      triggerMicros: binding.currentSystemFrameTimeStamp.inMicroseconds,
      timeout: timeout,
    );
    _onResult = onResult;
    if (!_listening) {
      binding.addTimingsCallback(_handleTimings);
      _listening = true;
    }
    binding.scheduleFrame();
  }

  void cancel() {
    _window = null;
    _onResult = null;
  }

  void dispose() {
    cancel();
    if (_listening) {
      SchedulerBinding.instance.removeTimingsCallback(_handleTimings);
      _listening = false;
    }
  }

  void _handleTimings(List<FrameTiming> timings) {
    final FrameWindow? window = _window;
    if (window == null) {
      return;
    }
    for (final FrameTiming timing in timings) {
      final FrameWindowResult? result = window.add(sampleFrom(timing));
      if (result != null) {
        final FrameWindowCallback? onResult = _onResult;
        cancel();
        onResult?.call(result);
        return;
      }
    }
  }
}
