import 'package:flutter/widgets.dart';

import '../core/kiln_colors.dart';
import '../core/kiln_trace.dart';
import 'ribbon_geometry.dart';

/// Anti-pattern: one `drawPath` call per segment, each with its own paint.
///
/// With ~5,000 segments that is ~5,000 stroked paths to tessellate and ~5,000
/// draws for Impeller to record into the Vulkan render pass, every frame.
class SpeedRibbonBroken extends StatelessWidget {
  const SpeedRibbonBroken({
    super.key,
    required this.geometry,
    this.strokeWidth = 6,
  });

  final RibbonGeometry geometry;
  final double strokeWidth;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.infinite,
      painter: _BrokenRibbonPainter(geometry, strokeWidth),
    );
  }
}

class _BrokenRibbonPainter extends CustomPainter {
  _BrokenRibbonPainter(this.geometry, this.strokeWidth);

  final RibbonGeometry geometry;
  final double strokeWidth;

  @override
  void paint(Canvas canvas, Size size) {
    kilnTrace('SpeedRibbon', 'paint', () {
      for (var i = 0; i < geometry.length - 1; i++) {
        final a = geometry.pointAt(i, size);
        final b = geometry.pointAt(i + 1, size);
        canvas.drawPath(
          Path()
            ..moveTo(a.dx, a.dy)
            ..lineTo(b.dx, b.dy),
          Paint()
            ..color = KilnColors.speed(geometry.speeds[i])
            ..style = PaintingStyle.stroke
            ..strokeCap = StrokeCap.round
            ..strokeWidth = strokeWidth,
        );
      }
    });
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
