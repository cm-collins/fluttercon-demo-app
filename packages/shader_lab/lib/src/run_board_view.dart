import 'package:flutter/widgets.dart';

import 'lab_tokens.dart';
import 'run_board.dart';

/// The last runs, newest first, so first and repeat runs sit one above the other.
class RunBoardView extends StatelessWidget {
  const RunBoardView({super.key, required this.board, required this.onClear});

  final RunBoard board;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
      decoration: BoxDecoration(
        color: LabColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: LabColors.hairline),
      ),
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
              const SizedBox(height: 6),
              const _Row(
                cells: <String>['#', 'RECOV s', 'OVERRUN', 'SLOW ms', ''],
                style: LabText.label,
              ),
              for (int i = 0; i < board.capacity; i++)
                if (i < runs.length)
                  _RunRow(run: runs[i])
                else
                  const _Row(
                    cells: <String>['', '', '', '', ''],
                    style: LabText.number,
                  ),
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
      style: LabText.number,
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
