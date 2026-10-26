import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import '../core/kiln_trace.dart';
import 'telemetry_trace.dart';

/// Anti-pattern: every frame rebuilds every trace as a full-resolution curve.
///
/// Thousands of quadratic segments per trace are recorded on the UI side, then
/// flattened and triangulated again on the raster thread, 120 times a second,
/// even though only the cursor moved.
class TelemetryDuelBroken extends StatelessWidget {
  const TelemetryDuelBroken({
    super.key,
    required this.traces,
    required this.progress,
  });

  final List<TelemetryTrace> traces;
  final ValueListenable<double> progress;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.infinite,
      painter: _BrokenDuelPainter(traces, progress),
    );
  }
}

class _BrokenDuelPainter extends CustomPainter {
  _BrokenDuelPainter(this.traces, this.progress) : super(repaint: progress);

  final List<TelemetryTrace> traces;
  final ValueListenable<double> progress;

  @override
  void paint(Canvas canvas, Size size) {
    kilnTrace('TelemetryDuel', 'paint', () {
      for (final trace in traces) {
        canvas.drawPath(
          _smoothPath(trace.values, size),
          Paint()
            ..color = trace.color
            ..style = PaintingStyle.stroke
            ..strokeWidth = 2,
        );
      }
      paintLapCursor(canvas, size, progress.value);
    });
  }

  Path _smoothPath(Float32List values, Size size) {
    final path = Path();
    if (values.length < 2) {
      return path;
    }
    final dx = size.width / (values.length - 1);
    var previous = Offset(0, size.height * (1 - values[0]));
    path.moveTo(previous.dx, previous.dy);
    for (var i = 1; i < values.length; i++) {
      final point = Offset(i * dx, size.height * (1 - values[i]));
      final mid = Offset.lerp(previous, point, 0.5)!;
      path.quadraticBezierTo(previous.dx, previous.dy, mid.dx, mid.dy);
      previous = point;
    }
    return path;
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
