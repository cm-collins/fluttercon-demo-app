import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import '../core/kiln_colors.dart';

/// Shared by every card. Grouped backdrop filters only collapse into one pass
/// when their filters are identical.
final ui.ImageFilter kilnGlassBlur = ui.ImageFilter.blur(sigmaX: 18, sigmaY: 18);

@immutable
class KpiCardData {
  const KpiCardData({required this.label, required this.value, this.valueColor = KilnColors.textPrimary});

  final String label;
  final String value;
  final Color valueColor;
}

class KpiCardContent extends StatelessWidget {
  const KpiCardContent({super.key, required this.card});

  final KpiCardData card;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: KilnColors.surface.withValues(alpha: 0.55),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            card.value,
            style: TextStyle(fontFamily: 'JetBrains Mono', fontSize: 20, color: card.valueColor),
          ),
          const SizedBox(height: 2),
          Text(card.label, style: const TextStyle(fontSize: 13, color: KilnColors.textSecondary)),
        ],
      ),
    );
  }
}
