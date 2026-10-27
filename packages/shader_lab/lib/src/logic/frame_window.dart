/// One frame's timing, in the engine's clock.
///
/// Mirrors the parts of `dart:ui` `FrameTiming` the timers need, so the window
/// logic can be unit tested without the engine.
class FrameSample {
  const FrameSample({
    required this.vsyncStartMicros,
    required this.rasterFinishMicros,
    required this.build,
    required this.raster,
  });

  final int vsyncStartMicros;
  final int rasterFinishMicros;
  final Duration build;
  final Duration raster;

  /// The slower of the two threads decides whether the frame was on time.
  Duration get cost => build > raster ? build : raster;
}

class FrameWindowResult {
  const FrameWindowResult({
    required this.timeToSmooth,
    required this.stall,
    required this.worst,
    required this.frames,
    required this.overBudgetFrames,
    required this.timedOut,
    this.capped = false,
  });

  /// From window start to the end of the last over-budget frame; zero if none.
  final Duration timeToSmooth;

  /// Sum of the time each over-budget frame spent beyond the budget.
  final Duration stall;

  /// Largest single-frame cost in the window.
  final Duration worst;

  final int frames;
  final int overBudgetFrames;

  /// True if frames were still over budget when the timeout expired.
  final bool timedOut;

  /// True when the window closed after [FrameWindow.maxFrames] without a
  /// settle run. The slowest frame is still the number to read.
  final bool capped;
}

/// Measures how long frames take to get back on budget after a trigger.
///
/// Feed every reported frame to [add]. Frames that started at or before
/// [triggerMicros] are ignored. The window closes after [settleFrames]
/// consecutive on-budget frames, or when [timeout] passes.
class FrameWindow {
  FrameWindow({
    required this.budget,
    required this.triggerMicros,
    this.settleFrames = 12,
    this.timeout = const Duration(seconds: 5),
    this.maxFrames,
  });

  final Duration budget;
  final int triggerMicros;
  final int settleFrames;
  final Duration timeout;
  final int? maxFrames;

  int? _startMicros;
  int? _lastOverFinishMicros;
  int _frames = 0;
  int _overFrames = 0;
  int _onBudgetRun = 0;
  Duration _stall = Duration.zero;
  Duration _worst = Duration.zero;
  FrameWindowResult? _result;

  FrameWindowResult? get result => _result;
  bool get isClosed => _result != null;

  /// Returns the result once the window closes, otherwise null.
  FrameWindowResult? add(FrameSample sample) {
    if (_result != null) {
      return _result;
    }
    if (sample.vsyncStartMicros <= triggerMicros) {
      return null;
    }
    final int start = _startMicros ??= sample.vsyncStartMicros;

    _frames++;
    final Duration cost = sample.cost;
    if (cost > _worst) {
      _worst = cost;
    }
    if (cost > budget) {
      _overFrames++;
      _stall += cost - budget;
      _lastOverFinishMicros = sample.rasterFinishMicros;
      _onBudgetRun = 0;
    } else {
      _onBudgetRun++;
    }

    final bool settled = _onBudgetRun >= settleFrames;
    final int? limit = maxFrames;
    final bool capped = limit != null && _frames >= limit;
    final bool expired =
        sample.rasterFinishMicros - start >= timeout.inMicroseconds;
    if (settled || expired || capped) {
      final int? lastOver = _lastOverFinishMicros;
      _result = FrameWindowResult(
        timeToSmooth: lastOver == null
            ? Duration.zero
            : Duration(microseconds: lastOver - start),
        stall: _stall,
        worst: _worst,
        frames: _frames,
        overBudgetFrames: _overFrames,
        timedOut: expired && !settled && !capped,
        capped: capped && !settled,
      );
    }
    return _result;
  }
}
