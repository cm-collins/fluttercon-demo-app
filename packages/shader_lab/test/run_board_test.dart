import 'package:flutter_test/flutter_test.dart';
import 'package:shader_lab/shader_lab.dart';

FrameWindowResult result(int lapMs) => FrameWindowResult(
  timeToSmooth: Duration(milliseconds: lapMs),
  stall: Duration.zero,
  worst: Duration.zero,
  frames: 12,
  overBudgetFrames: 0,
  timedOut: false,
);

void main() {
  test('only the first run since the process started is tagged first', () {
    final RunBoard board = RunBoard();
    board.add(result(900));
    board.add(result(40));

    expect(board.runs.map((LabRun r) => r.first), <bool>[false, true]);
    expect(board.latest!.number, 2);
  });

  test('keeps the newest runs up to capacity', () {
    final RunBoard board = RunBoard(capacity: 3);
    for (int i = 1; i <= 5; i++) {
      board.add(result(i));
    }

    expect(board.runs.map((LabRun r) => r.number), <int>[5, 4, 3]);
  });

  test('clear empties the board but keeps counting runs', () {
    final RunBoard board = RunBoard();
    board.add(result(900));
    board.clear();
    final LabRun next = board.add(result(30));

    expect(board.runs, hasLength(1));
    expect(next.number, 2);
    expect(next.first, isFalse);
  });
}
