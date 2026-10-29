import 'dart:developer' show Timeline;

import 'package:flutter/foundation.dart';

import 'durations.dart';
import 'frame_timer.dart';
import 'frame_window.dart';
import 'storm_tiles.dart';

/// Shader Storm results for this app process.
///
/// Skia keeps compiled programs for the life of the process, so "first" means
/// first since launch, not first since the screen opened. Skia also keeps a
/// disk cache; a truly cold Skia run needs `adb shell pm clear` first.
class StormRecord extends ChangeNotifier {
  int reveals = 0;
  FrameWindowResult? first;
  FrameWindowResult? repeat;

  bool get nextIsFirst => reveals == 0;

  void add(FrameWindowResult result) {
    reveals++;
    if (reveals == 1) {
      first = result;
    } else {
      repeat = result;
    }
    notifyListeners();
  }
}

final StormRecord processStormRecord = StormRecord();

enum StormState { hidden, measuring, revealed }

/// Reveals every [StormTileSpec] in one frame and times the frames after it.
class StormSession extends ChangeNotifier {
  StormSession({required this.record, int tileCount = 48})
    : tiles = stormTiles(tileCount);

  final StormRecord record;
  List<StormTileSpec> tiles;
  final FrameTimer _timer = FrameTimer();

  StormState state = StormState.hidden;
  bool _disposed = false;

  bool get revealed => state != StormState.hidden;

  /// The grid size can only change before the first reveal of the process.
  /// A later change would draw new effects in a run labelled "repeat".
  bool get canResize => state == StormState.hidden && record.nextIsFirst;

  void resize(int tileCount) {
    if (!canResize || tileCount == tiles.length) {
      return;
    }
    tiles = stormTiles(tileCount);
    _notify();
  }

  void reveal(Duration budget) {
    if (_disposed || state != StormState.hidden) {
      return;
    }
    state = StormState.measuring;
    Timeline.instantSync(
      'KILN::Storm::reveal',
      arguments: <String, String>{
        'temperature': record.nextIsFirst ? 'first' : 'repeat',
        'tiles': '${tiles.length}',
      },
    );
    _timer.arm(budget: budget, onResult: _complete);
    _notify();
  }

  void hide() {
    if (state != StormState.revealed) {
      return;
    }
    state = StormState.hidden;
    _notify();
  }

  void _complete(FrameWindowResult result) {
    if (_disposed) {
      return;
    }
    Timeline.instantSync(
      'KILN::Storm::result',
      arguments: <String, String>{
        'temperature': record.nextIsFirst ? 'first' : 'repeat',
        'worstMs': '${result.worst.inMicroseconds / 1000}',
        'overBudget': '${result.overBudgetFrames}',
      },
    );
    // One logcat line per reveal, so benchmark scripts can collect results.
    debugPrint(
      'KILN::Storm::result '
      'temperature=${record.nextIsFirst ? 'first' : 'repeat'} '
      'tiles=${tiles.length} '
      'worstMs=${formatMs(result.worst)} '
      'overBudget=${result.overBudgetFrames}/${result.frames}',
    );
    record.add(result);
    state = StormState.revealed;
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
