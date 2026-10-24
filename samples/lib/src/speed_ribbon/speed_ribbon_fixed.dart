import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import '../core/kiln_trace.dart';
import 'ribbon_geometry.dart';

/// Fix: the whole ribbon is one `drawVertices` call with per-vertex colours.
///
/// The mesh is built once per size and reused, so per frame the engine records
/// a single draw instead of thousands.
class SpeedRibbonFixed extends StatefulWidget {
  const SpeedRibbonFixed({super.key, required this.geometry, this.strokeWidth = 6});

  final RibbonGeometry geometry;
  final double strokeWidth;

  @override
  State<SpeedRibbonFixed> createState() => _SpeedRibbonFixedState();
}

class _SpeedRibbonFixedState extends State<SpeedRibbonFixed> {
  late final _RibbonMeshCache _cache = _RibbonMeshCache();

  @override
  void didUpdateWidget(SpeedRibbonFixed oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.geometry != widget.geometry || oldWidget.strokeWidth != widget.strokeWidth) {
      _cache.clear();
    }
  }

  @override
  void dispose() {
    _cache.clear();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.infinite,
      painter: _VerticesRibbonPainter(widget.geometry, widget.strokeWidth, _cache),
    );
  }
}

class _RibbonMeshCache {
  ui.Vertices? _mesh;
  Size? _size;

  ui.Vertices meshFor(RibbonGeometry geometry, Size size, double width) {
    if (_mesh == null || _size != size) {
      _mesh?.dispose();
      _mesh = buildRibbonVertices(geometry, size, width);
      _size = size;
    }
    return _mesh!;
  }

  void clear() {
    _mesh?.dispose();
    _mesh = null;
    _size = null;
  }
}

class _VerticesRibbonPainter extends CustomPainter {
  _VerticesRibbonPainter(this.geometry, this.strokeWidth, this.cache);

  final RibbonGeometry geometry;
  final double strokeWidth;
  final _RibbonMeshCache cache;

  @override
  void paint(Canvas canvas, Size size) {
    kilnTrace('SpeedRibbon', 'paint', () {
      canvas.drawVertices(
        cache.meshFor(geometry, size, strokeWidth),
        BlendMode.dst,
        Paint(),
      );
    });
  }

  @override
  bool shouldRepaint(_VerticesRibbonPainter oldDelegate) {
    return oldDelegate.geometry != geometry || oldDelegate.strokeWidth != strokeWidth;
  }
}
