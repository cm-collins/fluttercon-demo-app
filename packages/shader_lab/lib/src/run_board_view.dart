import 'package:flutter/widgets.dart';

import 'lab_chrome.dart';
import 'lab_tokens.dart';
import 'run_board.dart';

/// The last runs, newest first, so first and repeat runs sit one above the other.
class RunBoardView extends StatelessWidget {
  const RunBoardView({super.key, required this.board, required this.onClear});

  final RunBoard board;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return LabCard(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: ListenableBuilder(
        listenable: board,
        builder: (BuildContext context, Widget? _) {
          final List<LabRun> runs = board.runs;
          return Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Row(
                children: <Widget>[
                  const Expanded(child: Text('RUNS', style: LabText.label)),
                  GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: runs.isEmpty ? null : onClear,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Text(
                        'CLEAR',
                        style: LabText.label.copyWith(
                          color: runs.isEmpty
                              ? LabColors.hairline
                              : LabColors.aurora,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (runs.isEmpty)
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text('No draws yet.', style: LabText.body),
                )
              else ...<Widget>[
                const _Row(
                  cells: <String>['#', 'RECOV s', 'OVERRUN', 'SLOW ms', ''],
                  style: LabText.label,
                ),
                for (final LabRun run in runs) _RunRow(run: run),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _RunRow extends StatelessWidget {
  const _RunRow({required this.run});

  final LabRun run;

  @override
  Widget build(BuildContext context) {
    final r = run.result;
    final Color lapTint = r.timedOut ? LabColors.red : lapColor(r.timeToSmooth);
    return _Row(
      cells: <String>[
        '${run.number}',
        formatLap(r.timeToSmooth),
        formatMs(r.stall),
        formatMs(r.worst),
        run.first ? 'FIRST' : 'REPEAT',
      ],
      style: LabText.number.copyWith(fontSize: 14),
      tints: <int, Color>{
        1: lapTint,
        4: run.first ? LabColors.ember : LabColors.textSecondary,
      },
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({required this.cells, required this.style, this.tints = const {}});

  static const List<int> _flex = <int>[2, 4, 4, 4, 4];

  final List<String> cells;
  final TextStyle style;
  final Map<int, Color> tints;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 26,
      child: Row(
        children: <Widget>[
          for (int i = 0; i < cells.length; i++)
            Expanded(
              flex: _flex[i],
              child: Text(
                cells[i],
                maxLines: 1,
                textAlign: i == 0 ? TextAlign.start : TextAlign.end,
                style: tints[i] == null
                    ? style
                    : style.copyWith(color: tints[i]),
              ),
            ),
        ],
      ),
    );
  }
}
