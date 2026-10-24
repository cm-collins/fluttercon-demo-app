import 'package:flutter/widgets.dart';

import '../core/kiln_colors.dart';
import 'tower_row.dart';

/// Anti-pattern: group opacity over overlapping children plus a save-layer clip.
///
/// The background and the text overlap, so the engine cannot fold the opacity
/// into each draw and allocates an offscreen layer for the whole row.
/// `Clip.antiAliasWithSaveLayer` adds another one.
class TowerRowBroken extends StatelessWidget {
  const TowerRowBroken({super.key, required this.row, required this.highlight});

  final TowerRowData row;

  /// 0 = dimmed, 1 = fully visible (for example after a position change).
  final Animation<double> highlight;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: highlight,
      builder: (context, child) => Opacity(opacity: 0.4 + 0.6 * highlight.value, child: child),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(10),
        clipBehavior: Clip.antiAliasWithSaveLayer,
        child: Container(
          color: KilnColors.surfaceElevated,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: TowerRowContent(row: row),
        ),
      ),
    );
  }
}
