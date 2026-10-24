import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import '../core/geometry.dart';
import '../core/kiln_colors.dart';
import '../core/kiln_trace.dart';

/// Anti-pattern: the static circuit and the moving cars share one painter.
///
/// Every car update rebuilds and repaints the whole circuit, and
/// `shouldRepaint` always returns true.
class TrackMapBroken extends StatelessWidget {
  const TrackMapBroken({super.key, required this.circuit, required this.cars});

  /// Interleaved, normalised `x, y` pairs of the circuit outline.
  final Float32List circuit;

  /// Normalised car positions; index 0 is the leader.
  final ValueListenable<List<Offset>> cars;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(size: Size.infinite, painter: _BrokenTrackPainter(circuit, cars));
  }
}

class _BrokenTrackPainter extends CustomPainter {
  _BrokenTrackPainter(this.circuit, this.cars) : super(repaint: cars);

  final Float32List circuit;
  final ValueListenable<List<Offset>> cars;

  @override
  void paint(Canvas canvas, Size size) {
    kilnTrace('PitWall', 'trackMap', () {
      final outline = polylinePath(circuit, size, close: true);
      canvas
        ..drawPath(
          outline,
          Paint()
            ..color = KilnColors.hairline
            ..style = PaintingStyle.stroke
            ..strokeWidth = 12
            ..strokeJoin = StrokeJoin.round,
        )
        ..drawPath(
          outline,
          Paint()
            ..color = KilnColors.textSecondary
            ..style = PaintingStyle.stroke
            ..strokeWidth = 2,
        );
      paintCars(canvas, size, cars.value);
    });
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

/// Draws car dots; the leader is larger and highlighted.
void paintCars(Canvas canvas, Size size, List<Offset> cars) {
  final others = Paint()..color = KilnColors.textPrimary;
  final leader = Paint()..color = KilnColors.ember;
  for (var i = cars.length - 1; i >= 0; i--) {
    final p = Offset(cars[i].dx * size.width, cars[i].dy * size.height);
    canvas.drawCircle(p, i == 0 ? 5 : 3.5, i == 0 ? leader : others);
  }
}
