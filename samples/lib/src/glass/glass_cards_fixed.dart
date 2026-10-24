import 'package:flutter/widgets.dart';

import 'kpi_card.dart';

/// Fix: the cards share one backdrop pass through `BackdropGroup`.
///
/// Only valid because every card uses the identical [kilnGlassBlur] filter and
/// the cards never overlap.
class GlassCardsFixed extends StatelessWidget {
  const GlassCardsFixed({super.key, required this.cards});

  final List<KpiCardData> cards;

  @override
  Widget build(BuildContext context) {
    return BackdropGroup(
      child: Row(
        children: [
          for (final card in cards)
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: BackdropFilter.grouped(
                    filter: kilnGlassBlur,
                    child: KpiCardContent(card: card),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
