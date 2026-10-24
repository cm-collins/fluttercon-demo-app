import 'dart:typed_data';
import 'dart:ui';

import '../core/kiln_colors.dart';

/// Circuit centre line with a speed value at every point.
class RibbonGeometry {
  RibbonGeometry({required this.points, required this.speeds})
      : assert(points.length == speeds.length * 2);

  /// Interleaved `x, y` pairs normalised to 0..1.
  final Float32List points;

  /// Normalised speed (0..1) at each point.
  final Float32List speeds;

  int get length => speeds.length;

  Offset pointAt(int index, Size size) {
    return Offset(points[index * 2] * size.width, points[index * 2 + 1] * size.height);
  }
}

/// Builds the whole ribbon as one triangle mesh with a colour per vertex.
///
/// Each segment becomes a quad (two triangles) offset by half of [width] on
/// either side of the centre line.
Vertices buildRibbonVertices(RibbonGeometry geometry, Size size, double width) {
  final segments = geometry.length - 1;
  final positions = Float32List(segments * 12);
  final colors = Int32List(segments * 6);
  var p = 0;
  var c = 0;
  for (var i = 0; i < segments; i++) {
    final a = geometry.pointAt(i, size);
    final b = geometry.pointAt(i + 1, size);
    final direction = b - a;
    final length = direction.distance;
    final normal = length == 0
        ? Offset.zero
        : Offset(-direction.dy, direction.dx) / length * (width / 2);

    final a0 = a + normal;
    final a1 = a - normal;
    final b0 = b + normal;
    final b1 = b - normal;
    for (final v in [a0, a1, b0, b0, a1, b1]) {
      positions[p++] = v.dx;
      positions[p++] = v.dy;
    }

    final argb = KilnColors.speed(geometry.speeds[i]).toARGB32();
    for (var k = 0; k < 6; k++) {
      colors[c++] = argb;
    }
  }
  return Vertices.raw(VertexMode.triangles, positions, colors: colors);
}
