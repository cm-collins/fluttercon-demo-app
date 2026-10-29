import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import '../logic/storm_tiles.dart';
import 'lab_tokens.dart';

const List<Color> _stormColors = <Color>[
  LabColors.aurora,
  LabColors.violet,
  LabColors.ember,
  LabColors.purple,
  LabColors.green,
];

/// Every tile in one grid, behind its own repaint boundary so the moving
/// heartbeat does not re-record it.
class StormGrid extends StatelessWidget {
  const StormGrid({super.key, required this.tiles, this.columns = 8});

  final List<StormTileSpec> tiles;
  final int columns;

  @override
  Widget build(BuildContext context) {
    final int rows = (tiles.length / columns).ceil();
    return RepaintBoundary(
      child: Column(
        children: <Widget>[
          for (int row = 0; row < rows; row++)
            Expanded(
              child: Row(
                children: <Widget>[
                  for (int col = 0; col < columns; col++)
                    Expanded(
                      child: row * columns + col < tiles.length
                          ? Padding(
                              padding: const EdgeInsets.all(2),
                              child: CustomPaint(
                                key: ValueKey<String>(
                                  'storm-tile-${row * columns + col}',
                                ),
                                painter: StormTilePainter(
                                  tiles[row * columns + col],
                                ),
                                size: Size.infinite,
                              ),
                            )
                          : const SizedBox(),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

/// Paints one effect combination over a two-tone backdrop, so blend modes
/// have something to blend with.
class StormTilePainter extends CustomPainter {
  const StormTilePainter(this.spec);

  final StormTileSpec spec;

  @override
  void paint(Canvas canvas, Size size) {
    final Rect rect = Offset.zero & size;
    canvas.drawRect(rect, Paint()..color = LabColors.surfaceElevated);
    canvas.drawRect(
      Rect.fromLTRB(0, size.height / 2, size.width, size.height),
      Paint()..color = LabColors.hairline,
    );

    final Rect inner = rect.deflate(math.min(size.width, size.height) * 0.12);
    final Paint paint = _paintFor(inner);
    switch (spec.shape) {
      case StormShape.rect:
        canvas.drawRect(inner, paint);
      case StormShape.rrect:
        canvas.drawRRect(
          RRect.fromRectAndRadius(inner, Radius.circular(inner.width * 0.25)),
          paint,
        );
      case StormShape.circle:
        canvas.drawOval(inner, paint);
      case StormShape.star:
        canvas.drawPath(_star(inner), paint);
    }
  }

  Paint _paintFor(Rect rect) {
    final List<Color> colors = <Color>[
      for (int i = 0; i < spec.stops; i++)
        _stormColors[i % _stormColors.length],
    ];
    final List<double> positions = <double>[
      for (int i = 0; i < spec.stops; i++) i / (spec.stops - 1),
    ];
    final Paint paint = Paint()
      ..color = _stormColors[spec.stops % _stormColors.length]
      ..blendMode = spec.blendMode;
    if (spec.stroke) {
      paint
        ..style = PaintingStyle.stroke
        ..strokeWidth = rect.shortestSide * 0.12
        ..strokeJoin = StrokeJoin.round;
    }
    paint.shader = switch (spec.fill) {
      StormFill.linear => ui.Gradient.linear(
        rect.topLeft,
        rect.center,
        colors,
        positions,
        spec.tileMode,
      ),
      StormFill.radial => ui.Gradient.radial(
        rect.center,
        rect.shortestSide / 3,
        colors,
        positions,
        spec.tileMode,
      ),
      StormFill.sweep => ui.Gradient.sweep(
        rect.center,
        colors,
        positions,
        spec.tileMode,
        0,
        math.pi,
      ),
      StormFill.solid => null,
    };
    paint.maskFilter = switch (spec.blur) {
      StormBlur.none => null,
      StormBlur.normal => const MaskFilter.blur(BlurStyle.normal, 3),
      StormBlur.outer => const MaskFilter.blur(BlurStyle.outer, 4),
      StormBlur.inner => const MaskFilter.blur(BlurStyle.inner, 4),
    };
    paint.colorFilter = switch (spec.filter) {
      StormFilter.none => null,
      StormFilter.matrix => const ColorFilter.matrix(<double>[
        0.39, 0.77, 0.19, 0, 0, //
        0.35, 0.69, 0.17, 0, 0, //
        0.27, 0.53, 0.13, 0, 0, //
        0, 0, 0, 1, 0, //
      ]),
      StormFilter.mode => const ColorFilter.mode(
        LabColors.aurora,
        BlendMode.modulate,
      ),
    };
    return paint;
  }

  Path _star(Rect rect) {
    final Path path = Path();
    final Offset c = rect.center;
    final double outer = rect.shortestSide / 2;
    for (int i = 0; i < 10; i++) {
      final double r = i.isEven ? outer : outer * 0.45;
      final double a = -math.pi / 2 + i * math.pi / 5;
      final Offset p = c + Offset(math.cos(a) * r, math.sin(a) * r);
      if (i == 0) {
        path.moveTo(p.dx, p.dy);
      } else {
        path.lineTo(p.dx, p.dy);
      }
    }
    return path..close();
  }

  @override
  bool shouldRepaint(StormTilePainter oldDelegate) =>
      oldDelegate.spec.key != spec.key;
}
