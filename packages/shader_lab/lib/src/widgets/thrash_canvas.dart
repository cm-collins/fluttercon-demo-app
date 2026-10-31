import 'dart:developer' show Timeline;
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart' show ValueListenable, setEquals;
import 'package:flutter/scheduler.dart';
import 'package:flutter/widgets.dart';

import '../logic/thrash_ledger.dart';
import '../logic/thrash_scene.dart';
import 'lab_tokens.dart';
import 'xray_lens.dart';

const List<Color> _lineColors = <Color>[
  LabColors.aurora,
  LabColors.violet,
  LabColors.ember,
  LabColors.green,
  LabColors.purple,
];

Color thrashLineColor(int line) => _lineColors[line % _lineColors.length];

/// Stroke width of a price line, in logical pixels.
const double thrashLineWidth = 1.5;

/// Where each part of the canvas goes, and how a price maps to a position.
class ThrashLayout {
  ThrashLayout(this.size)
    : plot = Rect.fromLTRB(axisWidth, 8, size.width - 8, size.height * 0.78),
      strip = Rect.fromLTRB(
        axisWidth,
        size.height * 0.82,
        size.width - 8,
        size.height - 8,
      );

  static const double axisWidth = 52;

  final Size size;
  final Rect plot;
  final Rect strip;

  /// X of point [k] of [n] after the lines have scrolled left by [scroll].
  double x(int k, int n, double scroll) =>
      plot.left + ((k / n - scroll) % 1) * plot.width;

  /// Y of [value] (0..1) on [line]. Each line has its own band; bands overlap.
  double y(ThrashScene scene, int line, double value) {
    final double centre = 0.2 + 0.6 * (line + 0.5) / scene.lineCount;
    return plot.top + plot.height * (centre + 0.35 * (0.5 - value));
  }
}

/// The simplified lines, built once per size and thrash level.
///
/// They are built for an unscrolled frame and moved with a translation, so no
/// path is rebuilt while the canvas animates.
class ThrashLineCache {
  Size? _size;
  int? _level;
  List<Float32List> _points = const <Float32List>[];
  List<ui.Path> _paths = const <ui.Path>[];

  /// Points of every simplified line in canvas coordinates, as x, y pairs.
  List<Float32List> points(ThrashScene scene, ThrashLayout layout) {
    _ensure(scene, layout);
    return _points;
  }

  List<ui.Path> paths(ThrashScene scene, ThrashLayout layout) {
    _ensure(scene, layout);
    return _paths;
  }

  void _ensure(ThrashScene scene, ThrashLayout layout) {
    if (layout.size == _size && scene.level == _level) {
      return;
    }
    _size = layout.size;
    _level = scene.level;
    _points = <Float32List>[
      for (int line = 0; line < scene.lineCount; line++)
        _place(scene, layout, line),
    ];
    _paths = <ui.Path>[for (final Float32List xy in _points) _pathFrom(xy)];
  }

  Float32List _place(ThrashScene scene, ThrashLayout layout, int line) {
    final Float32List xy = decimate(scene.series[line], layout.plot.width);
    for (int i = 0; i < xy.length; i += 2) {
      xy[i] += layout.plot.left;
      xy[i + 1] = layout.y(scene, line, xy[i + 1]);
    }
    return xy;
  }

  ui.Path _pathFrom(Float32List xy) {
    final ui.Path path = ui.Path();
    for (int i = 0; i < xy.length; i += 2) {
      if (i == 0) {
        path.moveTo(xy[i], xy[i + 1]);
      } else {
        path.lineTo(xy[i], xy[i + 1]);
      }
    }
    return path;
  }
}

/// The animated market canvas that the thrash dial and the fixes act on.
class ThrashCanvas extends StatefulWidget {
  const ThrashCanvas({
    super.key,
    required this.scene,
    required this.fixes,
    required this.ledger,
    this.xray = false,
  });

  final ThrashScene scene;
  final Set<ThrashFix> fixes;
  final ThrashLedger ledger;
  final bool xray;

  @override
  State<ThrashCanvas> createState() => ThrashCanvasState();
}

class ThrashCanvasState extends State<ThrashCanvas>
    with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  final ValueNotifier<double> _seconds = ValueNotifier<double>(0);
  final ThrashLineCache cache = ThrashLineCache();

  /// Seconds since the canvas started animating.
  double get seconds => _seconds.value;

  @override
  void initState() {
    super.initState();
    _ticker = createTicker((Duration elapsed) {
      _seconds.value = elapsed.inMicroseconds / Duration.microsecondsPerSecond;
    })..start();
  }

  @override
  void dispose() {
    _ticker.dispose();
    _seconds.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool isolated = widget.fixes.contains(ThrashFix.isolateRepaints);
    return RepaintBoundary(
      child: Stack(
        fit: StackFit.expand,
        children: <Widget>[
          if (isolated)
            RepaintBoundary(
              child: CustomPaint(painter: ThrashGridPainter(widget.ledger)),
            ),
          CustomPaint(
            painter: ThrashScenePainter(
              scene: widget.scene,
              fixes: widget.fixes,
              ledger: widget.ledger,
              cache: cache,
              seconds: _seconds,
            ),
          ),
          if (widget.xray)
            CustomPaint(
              painter: XrayLensPainter(
                scene: widget.scene,
                simplified: widget.fixes.contains(ThrashFix.simplifyPaths),
                cache: cache,
                seconds: _seconds,
                scale: View.of(context).devicePixelRatio,
              ),
            ),
        ],
      ),
    );
  }
}

/// The static grid and price axis, on its own layer.
///
/// Used when repaints are isolated. Nothing it draws depends on time, so it
/// only repaints when its size changes.
class ThrashGridPainter extends CustomPainter {
  ThrashGridPainter(this.ledger);

  final ThrashLedger ledger;

  @override
  void paint(Canvas canvas, Size size) {
    paintThrashGrid(canvas, ThrashLayout(size), ledger);
  }

  @override
  bool shouldRepaint(ThrashGridPainter oldDelegate) => false;
}

/// Grid lines and price labels. Lays out its text on every call, as a naive
/// painter would.
void paintThrashGrid(Canvas canvas, ThrashLayout layout, ThrashLedger ledger) {
  Timeline.timeSync('KILN::Thrash::grid', () {
    ledger.gridPaints++;
    final Paint line = Paint()
      ..color = LabColors.hairline
      ..strokeWidth = 1;
    final Rect plot = layout.plot;
    for (int i = 0; i <= 5; i++) {
      final double y = plot.top + plot.height * i / 5;
      canvas.drawLine(Offset(plot.left, y), Offset(plot.right, y), line);
      final TextPainter label = TextPainter(
        text: TextSpan(
          text: (64800 - i * 120).toString(),
          style: LabText.label.copyWith(fontSize: 11),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      label.paint(
        canvas,
        Offset(plot.left - label.width - 8, y - label.height / 2),
      );
    }
    for (int i = 0; i <= 6; i++) {
      final double x = plot.left + plot.width * i / 6;
      canvas.drawLine(Offset(x, plot.top), Offset(x, plot.bottom), line);
    }
  });
}

/// Heat strip, price lines and glowing dots, broken or fixed per [fixes].
///
/// When repaints are not isolated it also paints the grid, so the grid is
/// recorded again on every animation frame.
class ThrashScenePainter extends CustomPainter {
  ThrashScenePainter({
    required this.scene,
    required this.fixes,
    required this.ledger,
    required this.cache,
    required this.seconds,
  }) : super(repaint: seconds);

  final ThrashScene scene;
  final Set<ThrashFix> fixes;
  final ThrashLedger ledger;
  final ThrashLineCache cache;
  final ValueListenable<double> seconds;

  @override
  void paint(Canvas canvas, Size size) {
    final ThrashLayout layout = ThrashLayout(size);
    final double t = seconds.value;
    ledger.beginScene();
    if (!fixes.contains(ThrashFix.isolateRepaints)) {
      paintThrashGrid(canvas, layout, ledger);
    }
    Timeline.timeSync('KILN::Thrash::strip', () {
      if (fixes.contains(ThrashFix.batchDraws)) {
        _stripBatched(canvas, layout, t);
      } else {
        _stripPerSegment(canvas, layout, t);
      }
    });
    Timeline.timeSync('KILN::Thrash::lines', () {
      if (fixes.contains(ThrashFix.simplifyPaths)) {
        _linesSimplified(canvas, layout, t);
      } else {
        _linesFull(canvas, layout, t);
      }
    });
    Timeline.timeSync('KILN::Thrash::dots', () {
      _dots(
        canvas,
        layout,
        t,
        layered: !fixes.contains(ThrashFix.glowWithoutLayers),
      );
    });
  }

  /// Broken: a new path through every point of every line, every frame.
  void _linesFull(Canvas canvas, ThrashLayout layout, double t) {
    final double scroll = ThrashScene.scrollAt(t);
    final int n = scene.pointsPerLine;
    final Paint stroke = _lineStroke();
    for (int line = 0; line < scene.lineCount; line++) {
      final Float32List series = scene.series[line];
      final ui.Path path = ui.Path();
      double previousX = double.infinity;
      for (int k = 0; k < n; k++) {
        final double x = layout.x(k, n, scroll);
        final double y = layout.y(scene, line, series[k]);
        // The line wraps at the seam: start a new contour there.
        if (x < previousX) {
          path.moveTo(x, y);
        } else {
          path.lineTo(x, y);
        }
        previousX = x;
      }
      canvas.drawPath(path, stroke..color = thrashLineColor(line));
      ledger
        ..draws += 1
        ..pathPoints += n;
    }
  }

  /// Fixed: the cached simplified paths, moved by a translation. Two copies
  /// cover the wrap; the clip hides what falls outside the plot.
  void _linesSimplified(Canvas canvas, ThrashLayout layout, double t) {
    final double shift = -ThrashScene.scrollAt(t) * layout.plot.width;
    final List<ui.Path> paths = cache.paths(scene, layout);
    final List<Float32List> points = cache.points(scene, layout);
    final Paint stroke = _lineStroke();
    canvas
      ..save()
      ..clipRect(layout.plot);
    for (int line = 0; line < paths.length; line++) {
      stroke.color = thrashLineColor(line);
      for (final double dx in <double>[shift, shift + layout.plot.width]) {
        canvas
          ..translate(dx, 0)
          ..drawPath(paths[line], stroke)
          ..translate(-dx, 0);
      }
      ledger
        ..draws += 2
        ..pathPoints += points[line].length;
    }
    canvas.restore();
  }

  Paint _lineStroke() => Paint()
    ..style = PaintingStyle.stroke
    ..strokeWidth = thrashLineWidth
    ..strokeJoin = StrokeJoin.bevel
    ..strokeCap = StrokeCap.butt;

  void _dots(
    Canvas canvas,
    ThrashLayout layout,
    double t, {
    required bool layered,
  }) {
    final double scroll = ThrashScene.scrollAt(t);
    final int n = scene.pointsPerLine;
    const double glow = 10;
    const double core = 2.5;
    final Paint corePaint = Paint()..color = LabColors.textPrimary;
    for (int dot = 0; dot < scene.dotCount; dot++) {
      final int line = dot % scene.lineCount;
      final int slot = dot ~/ scene.lineCount;
      final double fraction =
          ((slot + 0.5) / scene.dotsPerLine + line * 0.013) % 1;
      final int k = (fraction * n).floor() % n;
      final Offset centre = Offset(
        layout.x(k, n, scroll),
        layout.y(scene, line, scene.series[line][k]),
      );
      final Color color = thrashLineColor(line);
      if (layered) {
        // Broken: an offscreen layer per dot, blurred when it is composited.
        canvas.saveLayer(
          Rect.fromCircle(center: centre, radius: glow * 1.6),
          Paint()..imageFilter = ui.ImageFilter.blur(sigmaX: 5, sigmaY: 5),
        );
        canvas
          ..drawCircle(centre, glow * 0.6, Paint()..color = color)
          ..restore();
        ledger.layers += 1;
      } else {
        // Fixed: a radial gradient gives the same soft edge in one draw.
        canvas.drawCircle(
          centre,
          glow,
          Paint()
            ..shader = ui.Gradient.radial(centre, glow, <Color>[
              color.withValues(alpha: 0.85),
              color.withValues(alpha: 0),
            ]),
        );
      }
      canvas.drawCircle(centre, core, corePaint);
      ledger.draws += 2;
    }
  }

  /// Broken: one path and one paint per heat strip segment.
  void _stripPerSegment(Canvas canvas, ThrashLayout layout, double t) {
    final Rect strip = layout.strip;
    final int count = scene.stripSegments;
    final double width = strip.width / count;
    for (int k = 0; k < count; k++) {
      final double heat = ThrashScene.heatAt(k, count, t);
      final double x0 = strip.left + k * width;
      final double top = strip.bottom - heat * strip.height;
      final ui.Path segment = ui.Path()
        ..moveTo(x0, strip.bottom)
        ..lineTo(x0 + width, strip.bottom)
        ..lineTo(x0 + width * 1.3, top)
        ..lineTo(x0 + width * 0.3, top)
        ..close();
      canvas.drawPath(segment, Paint()..color = _heatColor(heat));
      ledger
        ..draws += 1
        ..pathPoints += 4;
    }
  }

  /// Fixed: every segment as two triangles in one drawVertices call.
  void _stripBatched(Canvas canvas, ThrashLayout layout, double t) {
    final Rect strip = layout.strip;
    final int count = scene.stripSegments;
    final double width = strip.width / count;
    final Float32List positions = Float32List(count * 12);
    final Int32List colors = Int32List(count * 6);
    for (int k = 0; k < count; k++) {
      final double heat = ThrashScene.heatAt(k, count, t);
      final double x0 = strip.left + k * width;
      final double top = strip.bottom - heat * strip.height;
      final double x1 = x0 + width;
      final double tx0 = x0 + width * 0.3;
      final double tx1 = x0 + width * 1.3;
      positions.setAll(k * 12, <double>[
        x0, strip.bottom, x1, strip.bottom, tx1, top, //
        x0, strip.bottom, tx1, top, tx0, top, //
      ]);
      colors.fillRange(k * 6, k * 6 + 6, _heatColor(heat).toARGB32());
    }
    canvas.drawVertices(
      ui.Vertices.raw(ui.VertexMode.triangles, positions, colors: colors),
      BlendMode.dst,
      Paint(),
    );
    ledger.draws += 1;
  }

  Color _heatColor(double heat) =>
      Color.lerp(LabColors.violet, LabColors.ember, heat)!;

  @override
  bool shouldRepaint(ThrashScenePainter oldDelegate) =>
      oldDelegate.scene != scene ||
      !setEquals(oldDelegate.fixes, fixes) ||
      oldDelegate.cache != cache;
}
