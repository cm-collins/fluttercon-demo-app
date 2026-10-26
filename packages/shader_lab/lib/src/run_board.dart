import 'package:flutter/foundation.dart';

import 'frame_window.dart';

class LabRun {
  const LabRun({
    required this.number,
    required this.first,
    required this.result,
  });

  /// 1-based count since the process started; survives [RunBoard.clear].
  final int number;

  /// True only for the first Draw depth since the process started.
  final bool first;

  final FrameWindowResult result;
}

/// Recent Shader Lab runs for this app process, newest first.
///
/// Held above the screen so runs survive leaving and re-entering it. Not
/// persisted: a restart or `pm clear` starts a fresh board, matching the
/// shader cache reset.
class RunBoard extends ChangeNotifier {
  RunBoard({this.capacity = 5});

  final int capacity;
  final List<LabRun> _runs = <LabRun>[];
  int _count = 0;
  Duration? _firstRecovery;

  List<LabRun> get runs => List<LabRun>.unmodifiable(_runs);
  LabRun? get latest => _runs.isEmpty ? null : _runs.first;

  /// First recovery minus the latest repeat recovery.
  ///
  /// The first measurement remains available after it scrolls off the visible
  /// board or the board is cleared. Null until a repeat run exists.
  Duration? get recoveryGap {
    final LabRun? repeat = latest;
    final Duration? firstRecovery = _firstRecovery;
    if (repeat == null || repeat.first || firstRecovery == null) {
      return null;
    }
    return firstRecovery - repeat.result.timeToSmooth;
  }

  LabRun add(FrameWindowResult result) {
    final bool first = _count == 0;
    if (first) {
      _firstRecovery = result.timeToSmooth;
    }
    final LabRun run = LabRun(number: _count + 1, first: first, result: result);
    _count++;
    _runs.insert(0, run);
    if (_runs.length > capacity) {
      _runs.removeLast();
    }
    notifyListeners();
    return run;
  }

  void clear() {
    if (_runs.isEmpty) {
      return;
    }
    _runs.clear();
    notifyListeners();
  }
}
