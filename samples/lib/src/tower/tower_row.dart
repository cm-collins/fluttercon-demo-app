import 'package:flutter/widgets.dart';

import '../core/kiln_colors.dart';

@immutable
class TowerRowData {
  const TowerRowData({
    required this.position,
    required this.code,
    required this.gap,
    required this.tyreColor,
  });

  final int position;
  final String code;
  final String gap;
  final Color tyreColor;
}

/// Row content shared by the broken and fixed tower rows.
///
/// [alpha] is applied to each leaf colour so the fixed row can fade without an
/// offscreen layer.
class TowerRowContent extends StatelessWidget {
  const TowerRowContent({super.key, required this.row, this.alpha = 1});

  final TowerRowData row;
  final double alpha;

  @override
  Widget build(BuildContext context) {
    final primary = KilnColors.textPrimary.withValues(alpha: alpha);
    final secondary = KilnColors.textSecondary.withValues(alpha: alpha);
    const mono = TextStyle(fontFamily: 'JetBrains Mono', fontSize: 16);
    return Row(
      children: [
        SizedBox(width: 24, child: Text('${row.position}', style: mono.copyWith(color: secondary))),
        Expanded(child: Text(row.code, style: mono.copyWith(color: primary))),
        Text(row.gap, style: mono.copyWith(color: secondary)),
        const SizedBox(width: 8),
        DecoratedBox(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: row.tyreColor.withValues(alpha: alpha), width: 2),
          ),
          child: const SizedBox.square(dimension: 10),
        ),
      ],
    );
  }
}
