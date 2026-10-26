import 'package:flutter/widgets.dart';

import 'frame_window.dart';
import 'lab_tokens.dart';
import 'run_board.dart';

/// Lap time (time to smooth) in large type, with stall time and worst frame.
class BudgetReadout extends StatelessWidget {
  const BudgetReadout({
    super.key,
    required this.latest,
    required this.measuring,
    required this.budget,
  });

  final LabRun? latest;
  final bool measuring;
  final Duration budget;

  @override
  Widget build(BuildContext context) {
    final FrameWindowResult? result = measuring ? null : latest?.result;

    final String lap;
    final Color lapTint;
    final String caption;
    if (measuring) {
      lap = '·.···';
      lapTint = LabColors.ember;
      caption = 'MEASURING UNTIL FRAMES ARE BACK ON BUDGET';
    } else if (result == null) {
      lap = '–.–––';
      lapTint = LabColors.textSecondary;
      caption = 'PRESS LIGHTS ON';
    } else {
      lap = formatLap(result.timeToSmooth);
      lapTint = result.timedOut ? LabColors.red : lapColor(result.timeToSmooth);
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
          Text('LAP TIME · $caption', style: LabText.label),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: <Widget>[
              Text(lap, style: LabText.lapTime.copyWith(color: lapTint)),
              const SizedBox(width: 8),
              Text(
                's',
                style: LabText.number.copyWith(color: LabColors.textSecondary),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: <Widget>[
              _Stat(
                label: 'STALL',
                value: result == null ? '–' : '${formatMs(result.stall)} ms',
              ),
              _Stat(
                label: 'WORST FRAME',
                value: result == null ? '–' : '${formatMs(result.worst)} ms',
                color: result == null ? null : frameColor(result.worst, budget),
              ),
              _Stat(
                label: 'OVER BUDGET',
                value: result == null
                    ? '–'
                    : '${result.overBudgetFrames}/${result.frames}',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value, this.color});

  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(label, style: LabText.label),
          const SizedBox(height: 2),
          Text(value, style: LabText.number.copyWith(color: color)),
        ],
      ),
    );
  }
}
