import 'package:flutter/widgets.dart';

import '../logic/durations.dart';
import 'lab_chrome.dart';
import 'lab_tokens.dart';

/// Screen title with the refresh rate, the frame budget and the renderer badge.
class LabHeader extends StatelessWidget {
  const LabHeader({
    super.key,
    required this.title,
    required this.rendererLabel,
    required this.budget,
    this.backLabel = 'Home',
    this.onBack,
  });

  final String title;
  final String rendererLabel;
  final Duration budget;

  /// Shown above the title when [onBack] is set.
  final String backLabel;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    final double hz = 1000000 / budget.inMicroseconds;
    return Row(
      children: <Widget>[
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              if (onBack != null)
                GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: onBack,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Text(backLabel, style: LabText.label),
                  ),
                ),
              Text(title, style: LabText.title),
              Text(
                '${hz.round()} Hz · ${formatMs(budget)} ms budget',
                style: LabText.label,
              ),
            ],
          ),
        ),
        const SizedBox(width: 12),
        LabBadge(label: rendererLabel),
      ],
    );
  }
}
