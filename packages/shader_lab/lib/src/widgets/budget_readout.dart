import 'package:flutter/widgets.dart';

import '../logic/durations.dart';
import '../logic/frame_window.dart';
import '../logic/run_board.dart';
import 'lab_chrome.dart';
import 'lab_tokens.dart';

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
      caption = 'PRESS DRAW DEPTH';
    } else {
      recovery = formatLap(result.timeToSmooth);
      recoveryTint = result.timedOut
          ? LabColors.red
          : result.capped
          ? LabColors.yellow
          : lapColor(result.timeToSmooth);
      caption = result.timedOut
          ? 'NOT SMOOTH AFTER 5 s'
          : result.capped
          ? 'SAMPLED'
          : 'DRAW DEPTH → SMOOTH';
    }

    return LabCard(
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
                style: LabText.lapTime.copyWith(
                  color: recoveryTint,
                  fontSize: 40,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                's',
                style: LabText.number.copyWith(color: LabColors.textSecondary),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _Metric(
            label: 'ACCUMULATED OVERRUN',
            value: result == null ? '–' : '${formatMs(result.stall)} ms',
          ),
          _Metric(
            label: 'SLOWEST FRAME',
            value: result == null ? '–' : '${formatMs(result.worst)} ms',
            valueColor: result == null
                ? null
                : frameColor(result.worst, budget),
          ),
          _Metric(
            label: 'FIRST − REPEAT',
            value: recoveryGap == null
                ? '–'
                : '${formatSignedLap(recoveryGap!)} s',
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
  const _Metric({required this.label, required this.value, this.valueColor});

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        children: <Widget>[
          Expanded(child: Text(label, style: LabText.label)),
          const SizedBox(width: 12),
          Text(value, style: LabText.number.copyWith(color: valueColor)),
        ],
      ),
    );
  }
}
