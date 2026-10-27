import 'package:flutter/widgets.dart';

/// "Obsidian & Aurora" tokens used by Shader Lab (see docs/design/design-system.md).
///
/// Colours are const ARGB literals so the palette is immutable and exact.
abstract final class LabColors {
  static const Color bg = Color(0xFF07080C);
  static const Color surface = Color(0xFF10131A);
  static const Color surfaceElevated = Color(0xFF171B24);
  static const Color hairline = Color(0xFF262B36);
  static const Color textPrimary = Color(0xFFF2F4F8);
  static const Color textSecondary = Color(0xFF9AA3B2);

  static const Color ember = Color(0xFFFFB547);
  static const Color aurora = Color(0xFF4FD1FF);
  static const Color violet = Color(0xFF8B5CF6);

  static const Color purple = Color(0xFFB26BFF);
  static const Color green = Color(0xFF3DDC97);
  static const Color yellow = Color(0xFFFFD60A);
  static const Color red = Color(0xFFFF4D6D);
}

abstract final class LabText {
  static const List<FontFeature> _tabular = <FontFeature>[
    FontFeature.tabularFigures(),
  ];

  // inherit: false so MaterialApp's fallback style cannot leak through.
  // That fallback is a yellow double underline on purpose, to mark text that
  // never set its own style. These screens are not inside a Material widget.
  static const TextStyle title = TextStyle(
    inherit: false,
    color: LabColors.textPrimary,
    fontSize: 24,
    fontWeight: FontWeight.w600,
    decoration: TextDecoration.none,
  );

  static const TextStyle label = TextStyle(
    inherit: false,
    color: LabColors.textSecondary,
    fontSize: 13,
    fontWeight: FontWeight.w500,
    letterSpacing: 0.4,
    decoration: TextDecoration.none,
  );

  static const TextStyle body = TextStyle(
    inherit: false,
    color: LabColors.textPrimary,
    fontSize: 16,
    fontWeight: FontWeight.w400,
    decoration: TextDecoration.none,
  );

  static const TextStyle number = TextStyle(
    inherit: false,
    color: LabColors.textPrimary,
    fontFamily: 'monospace',
    fontSize: 18,
    fontWeight: FontWeight.w600,
    fontFeatures: _tabular,
    decoration: TextDecoration.none,
  );

  static const TextStyle lapTime = TextStyle(
    inherit: false,
    color: LabColors.textPrimary,
    fontFamily: 'monospace',
    fontSize: 56,
    fontWeight: FontWeight.w700,
    height: 1.0,
    fontFeatures: _tabular,
    decoration: TextDecoration.none,
  );
}

/// F1 timing colour for a lap time (time to smooth).
Color lapColor(Duration timeToSmooth) {
  final int ms = timeToSmooth.inMilliseconds;
  if (timeToSmooth == Duration.zero) {
    return LabColors.purple;
  }
  if (ms <= 100) {
    return LabColors.green;
  }
  if (ms <= 500) {
    return LabColors.yellow;
  }
  return LabColors.red;
}

/// F1 timing colour for a single frame cost against the budget.
Color frameColor(Duration cost, Duration budget) {
  final int us = cost.inMicroseconds;
  if (us <= 6000) {
    return LabColors.purple;
  }
  if (us <= budget.inMicroseconds) {
    return LabColors.green;
  }
  if (us <= 12000) {
    return LabColors.yellow;
  }
  return LabColors.red;
}
