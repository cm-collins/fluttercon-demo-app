import 'package:flutter/widgets.dart';

import '../core/kiln_colors.dart';
import 'tower_row.dart';

/// Fix: fade the leaf colours instead of the group, and draw the rounded
/// background as a decoration instead of clipping.
///
/// No `Opacity`, no clip, so no offscreen layer. The visual result differs
/// slightly from group opacity where text overlaps the background, which is
/// acceptable for a highlight fade.
class TowerRowFixed extends StatelessWidget {
  const TowerRowFixed({super.key, required this.row, required this.highlight});

  final TowerRowData row;
  final Animation<double> highlight;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: highlight,
      builder: (context, _) {
        final alpha = 0.4 + 0.6 * highlight.value;
        return DecoratedBox(
          decoration: BoxDecoration(
            color: KilnColors.surfaceElevated.withValues(alpha: alpha),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: TowerRowContent(row: row, alpha: alpha),
          ),
        );
      },
    );
  }
}
