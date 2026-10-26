import 'package:flutter/widgets.dart';

import 'frame_window.dart';
import 'lab_tokens.dart';
import 'run_board.dart';

/// Recovery time in large type, with the measurements that explain it.
class BudgetReadout extends StatelessWidget {
  const BudgetReadout({
    super.key,
    required this.latest,
    required this.measuring,
    required this.budget,
    required this.recoveryGap,
  });

  final LabRun? latest;
  final bool measuring;
  final Duration budget;
  final Duration? recoveryGap;

  @override
  Widget build(BuildContext context) {
    final FrameWindowResult? result = measuring ? null : latest?.result;
    final String budgetMs = formatMs(budget);

    final String recovery;
    final Color recoveryTint;
    final String caption;
    if (measuring) {
      recovery = '·.···';
      recoveryTint = LabColors.ember;
      caption = 'MEASURING UNTIL FRAMES STAY ON BUDGET';
    } else if (result == null) {
      recovery = '–.–––';
      recoveryTint = LabColors.textSecondary;
      caption = 'PRESS LIGHTS ON';
    } else {
      recovery = formatLap(result.timeToSmooth);
      recoveryTint = result.timedOut
          ? LabColors.red
          : lapColor(result.timeToSmooth);
      caption = result.timedOut ? 'NOT SMOOTH AFTER 5 s' : 'LIGHTS ON → SMOOTH';
    }

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      decoration: BoxDecoration(
        color: LabColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: LabColors.hairline),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('RECOVERY TIME · $caption', style: LabText.label),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: <Widget>[
              Text(
                recovery,
                style: LabText.lapTime.copyWith(color: recoveryTint),
              ),
              const SizedBox(width: 8),
              Text(
                's',
                style: LabText.number.copyWith(color: LabColors.textSecondary),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Time from Lights on until frames stay within $budgetMs ms.',
            style: LabText.label,
          ),
          const SizedBox(height: 10),
          _Metric(
            label: 'ACCUMULATED OVERRUN',
            value: result == null ? '–' : '${formatMs(result.stall)} ms',
            detail:
                'Extra time late frames spent beyond $budgetMs ms, added together.',
          ),
          _Metric(
            label: 'SLOWEST FRAME',
            value: result == null ? '–' : '${formatMs(result.worst)} ms',
            detail:
                'Longest single UI or raster duration. The budget is $budgetMs ms.',
            valueColor: result == null
                ? null
                : frameColor(result.worst, budget),
          ),
          _Metric(
            label: 'FIRST − REPEAT',
            value: recoveryGap == null
                ? '–'
                : '${formatSignedLap(recoveryGap!)} s',
            detail: recoveryGap == null
                ? 'Run Lights on again to compare the first recovery with a repeat.'
                : 'First recovery minus the latest repeat. A large positive gap means first-use shader work.',
            valueColor: recoveryGap == null ? null : _gapColor(recoveryGap!),
          ),
          if (result != null)
            Text(
              '${result.overBudgetFrames}/${result.frames} frames over budget',
              style: LabText.label,
            ),
        ],
      ),
    );
  }

  Color _gapColor(Duration gap) {
    final int ms = gap.inMilliseconds.abs();
    if (ms <= 100) {
      return LabColors.green;
    }
    return gap.isNegative ? LabColors.yellow : LabColors.ember;
  }
}

class _Metric extends StatelessWidget {
  const _Metric({
    required this.label,
    required this.value,
    required this.detail,
    this.valueColor,
  });

  final String label;
  final String value;
  final String detail;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(child: Text(label, style: LabText.label)),
              Text(value, style: LabText.number.copyWith(color: valueColor)),
            ],
          ),
          const SizedBox(height: 2),
          Text(detail, style: LabText.label),
        ],
      ),
    );
  }
}
