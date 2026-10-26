import 'dart:collection';

import 'package:flutter/foundation.dart';
import 'package:flutter/scheduler.dart';

/// Frame state expressed with F1 timing colours.
enum FrameState { best, inBudget, atRisk, dropped }

@immutable
class FrameStats {
  const FrameStats({required this.p50, required this.p90, required this.p99});

  static const zero = FrameStats(p50: 0, p90: 0, p99: 0);

  /// Milliseconds.
  final double p50;
  final double p90;
  final double p99;
}

@immutable
class FrameBudgetSnapshot {
  const FrameBudgetSnapshot({
    required this.budgetMs,
    required this.ui,
    required this.raster,
    required this.total,
    required this.jankCount,
    required this.frameCount,
  });

  const FrameBudgetSnapshot.empty(this.budgetMs)
    : ui = FrameStats.zero,
      raster = FrameStats.zero,
      total = FrameStats.zero,
      jankCount = 0,
      frameCount = 0;

  final double budgetMs;

  /// `FrameTiming.buildDuration`: Dart work, labelled "UI" in DevTools.
  final FrameStats ui;

  /// `FrameTiming.rasterDuration`: Impeller work on the raster thread.
  final FrameStats raster;

  /// `FrameTiming.totalSpan`: vsync start to raster finish.
  final FrameStats total;

  /// Frames since the last [FrameBudgetMonitor.reset] where UI or raster
  /// exceeded the budget.
  final int jankCount;

  /// Frames in the rolling window.
  final int frameCount;
}

/// Rolling frame-budget statistics built from [FrameTiming] reports.
///
/// The engine batches timing reports (roughly once per second in profile and
/// release builds), so [value] updates at that cadence, not every frame.
class FrameBudgetMonitor extends ValueNotifier<FrameBudgetSnapshot> {
  FrameBudgetMonitor({this.refreshRateHz = 120, this.windowSize = 240})
    : super(FrameBudgetSnapshot.empty(1000 / refreshRateHz));

  final double refreshRateHz;
  final int windowSize;

  double get budgetMs => 1000 / refreshRateHz;

  final ListQueue<double> _ui = ListQueue<double>();
  final ListQueue<double> _raster = ListQueue<double>();
  final ListQueue<double> _total = ListQueue<double>();
  int _jankCount = 0;
  bool _listening = false;

  void start() {
    if (_listening) {
      return;
    }
    SchedulerBinding.instance.addTimingsCallback(_onTimings);
    _listening = true;
  }

  void stop() {
    if (!_listening) {
      return;
    }
    SchedulerBinding.instance.removeTimingsCallback(_onTimings);
    _listening = false;
  }

  void reset() {
    _ui.clear();
    _raster.clear();
    _total.clear();
    _jankCount = 0;
    value = FrameBudgetSnapshot.empty(budgetMs);
  }

  @override
  void dispose() {
    stop();
    super.dispose();
  }

  void _onTimings(List<FrameTiming> timings) {
    for (final timing in timings) {
      final ui = _ms(timing.buildDuration);
      final raster = _ms(timing.rasterDuration);
      _push(_ui, ui);
      _push(_raster, raster);
      _push(_total, _ms(timing.totalSpan));
      if (ui > budgetMs || raster > budgetMs) {
        _jankCount++;
      }
    }
    value = FrameBudgetSnapshot(
      budgetMs: budgetMs,
      ui: computeStats(_ui),
      raster: computeStats(_raster),
      total: computeStats(_total),
      jankCount: _jankCount,
      frameCount: _ui.length,
    );
  }

  void _push(ListQueue<double> window, double ms) {
    window.addLast(ms);
    if (window.length > windowSize) {
      window.removeFirst();
    }
  }

  static double _ms(Duration duration) => duration.inMicroseconds / 1000;

  /// Classifies a frame time. At 120 Hz the thresholds are 6.0, 8.33 and 12 ms.
  static FrameState classify(double ms, double budgetMs) {
    if (ms <= budgetMs * 0.72) {
      return FrameState.best;
    }
    if (ms <= budgetMs) {
      return FrameState.inBudget;
    }
    if (ms <= budgetMs * 1.44) {
      return FrameState.atRisk;
    }
    return FrameState.dropped;
  }

  @visibleForTesting
  static FrameStats computeStats(Iterable<double> values) {
    if (values.isEmpty) {
      return FrameStats.zero;
    }
    final sorted = values.toList()..sort();
    return FrameStats(
      p50: _percentile(sorted, 0.50),
      p90: _percentile(sorted, 0.90),
      p99: _percentile(sorted, 0.99),
    );
  }

  static double _percentile(List<double> sorted, double p) {
    return sorted[((sorted.length - 1) * p).round()];
  }
}
