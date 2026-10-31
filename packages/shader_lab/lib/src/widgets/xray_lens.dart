import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart' show ValueListenable;
import 'package:flutter/widgets.dart';

import '../logic/stroke_tessellation.dart';
import '../logic/thrash_scene.dart';
import 'lab_tokens.dart';
import 'thrash_canvas.dart';

/// The contours of [line] exactly as the canvas draws them this frame, as
/// x, y pairs in canvas coordinates.
///
/// A full-detail line wraps at the seam into two contours. A simplified line
/// is drawn twice, translated, to cover the wrap. With [within], only the runs
/// of points inside that rectangle (plus a small margin) are returned.
List<Float32List> drawnContours(
  ThrashScene scene,
  ThrashLayout layout,
  ThrashLineCache cache,
  int line,
  double scroll, {
  required bool simplified,
  Rect? within,
}) {
  final Rect? region = within?.inflate(2);
  final List<Float32List> contours = <Float32List>[];
  final List<double> run = <double>[];
  void flush() {
    if (run.length >= 4) {
      contours.add(Float32List.fromList(run));
    }
    run.clear();
  }

  void take(double x, double y) {
    if (region != null && (x < region.left || x > region.right)) {
      flush();
      return;
    }
    run
      ..add(x)
      ..add(y);
  }

  if (simplified) {
    final Float32List xy = cache.points(scene, layout)[line];
    final double shift = -scroll * layout.plot.width;
    for (final double dx in <double>[shift, shift + layout.plot.width]) {
      for (int i = 0; i < xy.length; i += 2) {
        take(xy[i] + dx, xy[i + 1]);
      }
      flush();
    }
  } else {
    final int n = scene.pointsPerLine;
    final Float32List series = scene.series[line];
    double previousX = double.infinity;
    for (int k = 0; k < n; k++) {
      final double x = layout.x(k, n, scroll);
      if (x < previousX) {
        flush();
      }
      take(x, layout.y(scene, line, series[k]));
      previousX = x;
    }
    flush();
  }
  return contours;
}

/// Points and modelled triangles for every price line the canvas draws in
/// one frame.
class XrayCounts {
  const XrayCounts({required this.points, required this.triangles});

  static const XrayCounts zero = XrayCounts(points: 0, triangles: 0);

  final int points;
  final int triangles;
}

/// Counts what the tessellation model says the price lines cost this frame.
/// The engine tessellates whole paths, including parts the clip hides, so
/// nothing is filtered out here.
XrayCounts countLineTriangles(
  ThrashScene scene,
  ThrashLayout layout,
  ThrashLineCache cache,
  double scroll, {
  required bool simplified,
  required double scale,
}) {
  int points = 0;
  int triangles = 0;
  for (int line = 0; line < scene.lineCount; line++) {
    for (final Float32List contour in drawnContours(
      scene,
      layout,
      cache,
      line,
      scroll,
      simplified: simplified,
    )) {
      points += contour.length ~/ 2;
      triangles += stripTriangles(
        strokeStripVertexCount(
          contour,
          halfWidth: thrashLineWidth / 2,
          scale: scale,
        ),
      );
    }
  }
  return XrayCounts(points: points, triangles: triangles);
}

/// A magnified view of the middle of the plot, showing the triangle strips the
/// tessellation model builds for the price lines there.
///
/// It is a model of what Impeller's tessellator does with the same points, not
/// the engine's output. Drawing it adds raster work of its own.
class XrayLensPainter extends CustomPainter {
  XrayLensPainter({
    required this.scene,
    required this.simplified,
    required this.cache,
    required this.seconds,
    required this.scale,
  }) : super(repaint: seconds);

  final ThrashScene scene;
  final bool simplified;
  final ThrashLineCache cache;
  final ValueListenable<double> seconds;

  /// Device pixels per logical pixel, which decides where joins are added.
  final double scale;

  @override
  void paint(Canvas canvas, Size size) {
    final ThrashLayout layout = ThrashLayout(size);
    final Rect plot = layout.plot;
    final Rect source = Rect.fromCenter(
      center: plot.center,
      width: plot.width * 0.12,
      height: plot.width * 0.08,
    );
    final Rect lens = Rect.fromLTWH(
      plot.left + 6,
      plot.top + 6,
      plot.width * 0.5,
      plot.width * 0.5 / 1.5,
    );
    final double zoom = lens.width / source.width;
    final double scroll = ThrashScene.scrollAt(seconds.value);

    canvas.drawRect(
      source,
      Paint()
        ..style = PaintingStyle.stroke
        ..color = LabColors.textPrimary
        ..strokeWidth = 1,
    );
    canvas.drawRect(
      lens,
      Paint()..color = LabColors.bg.withValues(alpha: 0.94),
    );

    canvas
      ..save()
      ..clipRect(lens);
    final Paint edges = Paint()..strokeWidth = 1;
    for (int line = 0; line < scene.lineCount; line++) {
      final List<double> segments = <double>[];
      for (final Float32List contour in drawnContours(
        scene,
        layout,
        cache,
        line,
        scroll,
        simplified: simplified,
        within: source,
      )) {
        final Float32List v = strokeStrip(
          contour,
          halfWidth: thrashLineWidth / 2,
          scale: scale,
        );
        final int count = v.length ~/ 2;
        // Every triangle (i, i+1, i+2) of the strip contributes the edges
        // i to i+1 and i to i+2.
        for (int i = 0; i + 1 < count; i++) {
          for (final int j in <int>[i + 1, i + 2]) {
            if (j >= count) {
              continue;
            }
            segments
              ..add(lens.left + (v[2 * i] - source.left) * zoom)
              ..add(lens.top + (v[2 * i + 1] - source.top) * zoom)
              ..add(lens.left + (v[2 * j] - source.left) * zoom)
              ..add(lens.top + (v[2 * j + 1] - source.top) * zoom);
          }
        }
      }
      if (segments.isNotEmpty) {
        canvas.drawRawPoints(
          ui.PointMode.lines,
          Float32List.fromList(segments),
          edges..color = thrashLineColor(line).withValues(alpha: 0.9),
        );
      }
    }
    canvas.restore();

    canvas.drawRect(
      lens,
      Paint()
        ..style = PaintingStyle.stroke
        ..color = LabColors.aurora
        ..strokeWidth = 1.5,
    );
    final TextPainter label = TextPainter(
      text: TextSpan(
        text: 'X-RAY ×${zoom.round()} · model',
        style: LabText.label.copyWith(
          fontSize: 11,
          color: LabColors.textPrimary,
        ),
      ),
      textDirection: TextDirection.ltr,
      maxLines: 1,
      ellipsis: '…',
    )..layout(maxWidth: lens.width - 12);
    label.paint(canvas, Offset(lens.left + 6, lens.bottom - label.height - 4));
  }

  @override
  bool shouldRepaint(XrayLensPainter oldDelegate) =>
      oldDelegate.scene != scene ||
      oldDelegate.simplified != simplified ||
      oldDelegate.scale != scale;
}
