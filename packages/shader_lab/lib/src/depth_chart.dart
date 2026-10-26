import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import 'lab_tokens.dart';
import 'market.dart';

/// Depth fill drawn with one fragment shader.
///
/// Bids and asks share that shader. The only uniform that changes is which
/// side is being filled. Creating the widget is the first use of the shader.
class DepthChart extends StatefulWidget {
  const DepthChart({
    super.key,
    required this.program,
    required this.bids,
    required this.asks,
  });

  final ui.FragmentProgram program;
  final List<BookLevel> bids;
  final List<BookLevel> asks;

  @override
  State<DepthChart> createState() => _DepthChartState();
}

class _DepthChartState extends State<DepthChart> {
  late final ui.FragmentShader _shader = widget.program.fragmentShader();

  @override
  void dispose() {
    _shader.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _DepthPainter(
        shader: _shader,
        bids: widget.bids,
        asks: widget.asks,
      ),
      child: const SizedBox.expand(),
    );
  }
}

class _DepthPainter extends CustomPainter {
  const _DepthPainter({
    required this.shader,
    required this.bids,
    required this.asks,
  });

  final ui.FragmentShader shader;
  final List<BookLevel> bids;
  final List<BookLevel> asks;

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) {
      return;
    }
    final Paint paint = Paint()..shader = shader;
    final Rect left = Rect.fromLTWH(0, 0, size.width / 2, size.height);
    final Rect right = Rect.fromLTWH(
      size.width / 2,
      0,
      size.width / 2,
      size.height,
    );
    _fill(canvas, paint, _path(bids, left, fromRight: true), left, bid: true);
    _fill(
      canvas,
      paint,
      _path(asks, right, fromRight: false),
      right,
      bid: false,
    );
    canvas.drawLine(
      Offset(size.width / 2, 0),
      Offset(size.width / 2, size.height),
      Paint()
        ..color = LabColors.hairline
        ..strokeWidth = 1,
    );
  }

  void _fill(
    Canvas canvas,
    Paint paint,
    Path path,
    Rect side, {
    required bool bid,
  }) {
    shader
      ..setFloat(0, side.width)
      ..setFloat(1, side.height)
      ..setFloat(2, bid ? 1 : 0);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(_DepthPainter oldDelegate) {
    return oldDelegate.bids != bids || oldDelegate.asks != asks;
  }
}

Path _path(List<BookLevel> levels, Rect side, {required bool fromRight}) {
  final Path path = Path()
    ..moveTo(fromRight ? side.right : side.left, side.bottom);
  if (levels.isEmpty) {
    path
      ..lineTo(fromRight ? side.left : side.right, side.bottom)
      ..close();
    return path;
  }
  double cumulative = 0;
  final List<double> totals = <double>[];
  for (final BookLevel level in levels) {
    cumulative += level.quantity;
    totals.add(cumulative);
  }
  final double maxQuantity = cumulative == 0 ? 1 : cumulative;
  final int last = levels.length - 1;
  for (int i = 0; i < levels.length; i++) {
    final double t = last == 0 ? 1 : i / last;
    final double x = fromRight
        ? side.right - t * side.width
        : side.left + t * side.width;
    final double y =
        side.bottom - (totals[i] / maxQuantity) * (side.height - 8);
    path.lineTo(x, y);
  }
  path
    ..lineTo(fromRight ? side.left : side.right, side.bottom)
    ..close();
  return path;
}
