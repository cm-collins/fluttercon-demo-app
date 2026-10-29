import 'dart:async';
import 'dart:developer' show Timeline;
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';

import 'frame_timer.dart';
import 'frame_window.dart';

enum ShaderJankState { idle, loading, measuring, complete, failed }

/// Runs a deliberately separate cold/warm first-use shader experiment.
///
/// The program is not loaded when the session is created. A cold run loads it
/// on demand, then paints it through an animation while [FrameTimer] observes
/// the first-use and warm frames. A repeated run is explicitly warm.
class ShaderJankSession extends ChangeNotifier {
  ShaderJankSession({
    required this.shaderAsset,
    this.onMeasuring,
    this.onComplete,
  });

  final String shaderAsset;
  final ValueChanged<bool>? onMeasuring;
  final VoidCallback? onComplete;
  final FrameTimer _timer = FrameTimer();

  ui.FragmentProgram? program;
  ShaderJankState state = ShaderJankState.idle;
  FrameWindowResult? result;
  Duration? loadDuration;
  int generation = 0;
  String? error;
  bool lastRunWasCold = false;
  bool _disposed = false;

  bool get active => state == ShaderJankState.measuring && program != null;

  Future<void> run({required Duration budget, required bool cold}) async {
    if (_disposed || state == ShaderJankState.loading || active) {
      return;
    }
    lastRunWasCold = cold;
    result = null;
    error = null;
    state = ShaderJankState.loading;
    if (cold) {
      program = null;
      loadDuration = null;
    }
    _notify();

    try {
      if (program == null) {
        final Stopwatch stopwatch = Stopwatch()..start();
        Timeline.instantSync(
          'KILN::ShaderJank::load',
          arguments: <String, String>{'temperature': cold ? 'cold' : 'warm'},
        );
        program = await ui.FragmentProgram.fromAsset(shaderAsset);
        loadDuration = stopwatch.elapsed;
        Timeline.instantSync(
          'KILN::ShaderJank::program',
          arguments: <String, String>{
            'loadMs': '${loadDuration!.inMicroseconds / 1000}',
          },
        );
      }
      if (_disposed || program == null) {
        return;
      }
      generation++;
      state = ShaderJankState.measuring;
      onMeasuring?.call(true);
      Timeline.instantSync(
        'KILN::ShaderJank::first_use',
        arguments: <String, String>{'temperature': cold ? 'cold' : 'warm'},
      );
      _timer.arm(budget: budget, onResult: _complete);
      _notify();
    } on Object catch (caught) {
      state = ShaderJankState.failed;
      error = '$caught';
      _notify();
    }
  }

  void _complete(FrameWindowResult value) {
    if (_disposed) {
      return;
    }
    result = value;
    state = ShaderJankState.complete;
    Timeline.instantSync(
      'KILN::ShaderJank::recovery',
      arguments: <String, String>{
        'temperature': lastRunWasCold ? 'cold' : 'warm',
        'worstMs': '${value.worst.inMicroseconds / 1000}',
        'overBudget': '${value.overBudgetFrames}',
      },
    );
    onMeasuring?.call(false);
    onComplete?.call();
    _notify();
  }

  void _notify() {
    if (!_disposed) {
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _timer.dispose();
    super.dispose();
  }
}
