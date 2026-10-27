import 'package:flutter/widgets.dart';

import 'lab_tokens.dart';

/// Flat button with no ink effect.
///
/// Material's sparkle splash is a runtime fragment shader; on Skia it would
/// compile on the very tap being measured and pollute the frame.
class LabButton extends StatelessWidget {
  const LabButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.primary = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool primary;

  @override
  Widget build(BuildContext context) {
    final bool enabled = onPressed != null;
    final Color fill = primary ? LabColors.violet : LabColors.surfaceElevated;
    final Color text = LabColors.textPrimary;
    return Semantics(
      button: true,
      enabled: enabled,
      label: label,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onPressed,
        child: Opacity(
          opacity: enabled ? 1 : 0.4,
          child: Container(
            height: 52,
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(
              color: fill,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: primary ? fill : LabColors.hairline),
            ),
            child: Text(
              label,
              style: LabText.body.copyWith(
                color: text,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.6,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
