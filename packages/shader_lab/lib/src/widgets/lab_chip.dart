import 'package:flutter/widgets.dart';

import 'lab_tokens.dart';

/// A rounded choice chip. Violet when selected.
class LabChip extends StatelessWidget {
  const LabChip({
    super.key,
    required this.label,
    required this.selected,
    required this.onTap,
    this.padding = const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final Color accent = selected ? LabColors.violet : LabColors.textSecondary;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: selected ? LabColors.surfaceElevated : LabColors.surface,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: selected ? accent : LabColors.hairline),
        ),
        child: Padding(
          padding: padding,
          child: Text(
            label,
            style: LabText.body.copyWith(
              color: accent,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );
  }
}
