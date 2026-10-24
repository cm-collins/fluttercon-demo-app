import 'dart:ui';

/// Colour tokens from the "Obsidian & Aurora" design system.
abstract final class KilnColors {
  static const bg = Color(0xFF07080C);
  static const surface = Color(0xFF10131A);
  static const surfaceElevated = Color(0xFF171B24);
  static const hairline = Color(0xFF262B36);
  static const textPrimary = Color(0xFFF2F4F8);
  static const textSecondary = Color(0xFF9AA3B2);

  static const ember = Color(0xFFFFB547);
  static const aurora = Color(0xFF4FD1FF);
  static const violet = Color(0xFF8B5CF6);

  static const timingPurple = Color(0xFFB26BFF);
  static const timingGreen = Color(0xFF3DDC97);
  static const timingYellow = Color(0xFFFFD60A);
  static const timingRed = Color(0xFFFF4D6D);

  static const speedSlow = Color(0xFFFF4D6D);
  static const speedMid = Color(0xFFFFB547);
  static const speedFast = Color(0xFF4FD1FF);

  /// Maps a normalised speed (0 = slowest, 1 = fastest) onto the ribbon ramp.
  static Color speed(double t) {
    final v = t.clamp(0.0, 1.0);
    if (v < 0.45) {
      return Color.lerp(speedSlow, speedMid, v / 0.45)!;
    }
    return Color.lerp(speedMid, speedFast, (v - 0.45) / 0.55)!;
  }
}
