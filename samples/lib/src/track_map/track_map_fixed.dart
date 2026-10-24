import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import '../core/geometry.dart';
import '../core/kiln_colors.dart';
import '../core/kiln_trace.dart';
import 'track_map_broken.dart' show paintCars;

/// Fix: the circuit lives in its own layer behind a `RepaintBoundary` and is
/// only re-recorded when its data or size changes; a light painter draws cars.
///
/// On Impeller the circuit layer is still rasterized each frame (there is no
/// raster cache), but the Dart paint work and display-list recording for it
/// disappear from every frame.
class TrackMapFixed extends StatelessWidget {
  const TrackMapFixed({super.key, required this.circuit, required this.cars});

  final Float32List circuit;
  final ValueListenable<List<Offset>> cars;

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        RepaintBoundary(child: CustomPaint(painter: _CircuitPainter(circuit))),
        CustomPaint(painter: _CarsPainter(cars)),
      ],
    );
  }
}

class _CircuitPainter extends CustomPainter {
  _CircuitPainter(this.circuit);

  final Float32List circuit;
  Path? _outline;
  Size? _size;

  @override
  void paint(Canvas canvas, Size size) {
    kilnTrace('PitWall', 'trackMap', () {
      if (_outline == null || _size != size) {
        _outline = polylinePath(circuit, size, close: true);
        _size = size;
      }
      canvas
        ..drawPath(
          _outline!,
          Paint()
            ..color = KilnColors.hairline
            ..style = PaintingStyle.stroke
            ..strokeWidth = 12
            ..strokeJoin = StrokeJoin.round,
        )
        ..drawPath(
          _outline!,
          Paint()
            ..color = KilnColors.textSecondary
            ..style = PaintingStyle.stroke
            ..strokeWidth = 2,
        );
    });
  }

  @override
  bool shouldRepaint(_CircuitPainter oldDelegate) => oldDelegate.circuit != circuit;
}

class _CarsPainter extends CustomPainter {
  _CarsPainter(this.cars) : super(repaint: cars);

  final ValueListenable<List<Offset>> cars;

  @override
  void paint(Canvas canvas, Size size) => paintCars(canvas, size, cars.value);

  @override
  bool shouldRepaint(_CarsPainter oldDelegate) => oldDelegate.cars != cars;
}
