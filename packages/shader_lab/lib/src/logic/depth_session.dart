import 'dart:developer' show Timeline;
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';

import 'durations.dart';
import 'frame_timer.dart';
import 'frame_window.dart';
import 'run_board.dart';

/// Loads one fragment program and times its first paint.
///
/// File I/O finishes in [enter], before [draw]. The clock starts inside [draw].
class DepthSession extends ChangeNotifier {
  DepthSession({
    required this.shaderAsset,
    required this.board,
    required this.rendererLabel,
    this.onMeasuring,
  });

  final String shaderAsset;
  final RunBoard board;
  final String rendererLabel;
  final void Function(bool measuring)? onMeasuring;

  final FrameTimer _timer = FrameTimer();
  ui.FragmentProgram? program;
  int generation = 0;
  bool measuring = false;
  bool _disposed = false;

  void enter() {
    Timeline.instantSync('KILN::Markets::enter');
    ui.FragmentProgram.fromAsset(shaderAsset).then((ui.FragmentProgram loaded) {
      program = loaded;
      _notify();
    });
  }

  bool get ready => program != null;

  void draw(Duration budget) {
    Timeline.instantSync(
      'KILN::Markets::drawDepth',
      arguments: <String, String>{'renderer': rendererLabel},
    );
    _timer.arm(budget: budget, onResult: _onResult);
    onMeasuring?.call(true);
    generation += 1;
    measuring = true;
    _notify();
  }

  void _onResult(FrameWindowResult result) {
    final LabRun run = board.add(result);
    Timeline.instantSync(
      'KILN::Markets::smooth',
      arguments: <String, String>{
        'renderer': rendererLabel,
        'run': '${run.number}',
        'timeToSmoothMs': formatMs(result.timeToSmooth),
        'stallMs': formatMs(result.stall),
        'worstMs': formatMs(result.worst),
      },
    );
    measuring = false;
    _notify();
    onMeasuring?.call(false);
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
