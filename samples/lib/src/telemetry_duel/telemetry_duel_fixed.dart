import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import '../core/kiln_trace.dart';
import 'telemetry_trace.dart';

/// Fix: traces are reduced to screen resolution and built once; only the
/// cursor layer repaints each frame.
///
/// Impeller has no raster cache, so the static layer is still rasterized every
/// frame. The win on the raster thread comes from tessellating roughly one
/// segment per pixel instead of thousands of curves; the win on the UI side
/// comes from not rebuilding or re-recording the paths.
class TelemetryDuelFixed extends StatelessWidget {
  const TelemetryDuelFixed({super.key, required this.traces, required this.progress});

  final List<TelemetryTrace> traces;
  final ValueListenable<double> progress;

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        RepaintBoundary(child: CustomPaint(painter: _TraceLayerPainter(traces))),
        CustomPaint(painter: _CursorPainter(progress)),
      ],
    );
  }
}

class _TraceLayerPainter extends CustomPainter {
  _TraceLayerPainter(this.traces);

  final List<TelemetryTrace> traces;

  @override
  void paint(Canvas canvas, Size size) {
    kilnTrace('TelemetryDuel', 'paint', () {
      for (final trace in traces) {
        canvas.drawPath(
          trace.cachedPath(size),
          Paint()
            ..color = trace.color
            ..style = PaintingStyle.stroke
            ..strokeWidth = 2,
        );
      }
    });
  }

  @override
  bool shouldRepaint(_TraceLayerPainter oldDelegate) => oldDelegate.traces != traces;
}

class _CursorPainter extends CustomPainter {
  _CursorPainter(this.progress) : super(repaint: progress);

  final ValueListenable<double> progress;

  @override
  void paint(Canvas canvas, Size size) => paintLapCursor(canvas, size, progress.value);

  @override
  bool shouldRepaint(_CursorPainter oldDelegate) => oldDelegate.progress != progress;
}
