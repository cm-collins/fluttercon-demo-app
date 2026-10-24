import 'package:flutter/widgets.dart';

import 'kpi_card.dart';

/// Anti-pattern: one independent `BackdropFilter` per card.
///
/// Each card reads back the scene behind it and blurs it in its own pass.
class GlassCardsBroken extends StatelessWidget {
  const GlassCardsBroken({super.key, required this.cards});

  final List<KpiCardData> cards;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (final card in cards)
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: BackdropFilter(filter: kilnGlassBlur, child: KpiCardContent(card: card)),
              ),
            ),
          ),
      ],
    );
  }
}
