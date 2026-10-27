import 'package:flutter/widgets.dart';

import 'lab_tokens.dart';
import 'market.dart';

/// Shared surface. Every panel in Markets uses this radius, border, and padding.
class LabCard extends StatelessWidget {
  const LabCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
  });

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: LabColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: LabColors.hairline),
      ),
      child: Padding(padding: padding, child: child),
    );
  }
}

/// Renderer identity. Colour follows the flavor, not the price direction.
class LabBadge extends StatelessWidget {
  const LabBadge({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final bool skia = label.toLowerCase().contains('skia');
    final Color accent = skia ? LabColors.ember : LabColors.violet;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: LabColors.surfaceElevated,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: accent),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        child: Text(
          label,
          style: LabText.body.copyWith(
            color: accent,
            fontSize: 14,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

/// Up or down change. Green and red are reserved for price direction.
class LabPercent extends StatelessWidget {
  const LabPercent({super.key, required this.changePercent});

  final double changePercent;

  @override
  Widget build(BuildContext context) {
    final bool up = changePercent >= 0;
    final Color tint = up ? LabColors.green : LabColors.red;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: tint.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        child: Text(
          formatPercent(changePercent),
          style: LabText.number.copyWith(color: tint, fontSize: 14),
        ),
      ),
    );
  }
}

/// Small section title above a card.
class LabSectionTitle extends StatelessWidget {
  const LabSectionTitle(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text,
        style: LabText.body.copyWith(fontWeight: FontWeight.w600),
      ),
    );
  }
}
