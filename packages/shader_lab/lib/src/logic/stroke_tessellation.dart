import 'dart:math' as math;
import 'dart:typed_data';

/// A model of how Impeller tessellates a stroked polyline, used by X-ray mode.
///
/// It follows `StrokePathSegmentReceiver` in
/// `engine/src/flutter/impeller/entity/geometry/stroke_path_geometry.cc` for
/// straight segments with bevel joins and butt caps:
///
/// * the first point adds two vertices, half the stroke width either side;
/// * the end of every segment adds two more;
/// * a corner adds two more, unless the turn moves the stroke edge by less
///   than [joinPixelThreshold] device pixels;
/// * zero-length segments are skipped.
///
/// The vertices form one triangle strip per contour, so a contour of `v`
/// vertices is `v - 2` triangles. The engine does this on the raster thread
/// for every stroked path, every frame. This is a model built from the same
/// points the app draws, not the engine's own output.
const double joinPixelThreshold = 0.25;

/// The cosine between two segment normals above which no join is added.
double maximumJoinCosine(double scale, double halfWidth) {
  final double hypotenuse = scale * halfWidth;
  if (hypotenuse <= joinPixelThreshold) {
    return -1.1;
  }
  final double bisector = math.sqrt(
    hypotenuse * hypotenuse - joinPixelThreshold * joinPixelThreshold,
  );
  final double halfCosine = bisector / hypotenuse;
  return 2 * halfCosine * halfCosine - 1;
}

/// Triangle-strip vertex count for the contour in [xy] (x, y pairs, logical
/// pixels). [scale] is device pixels per logical pixel.
int strokeStripVertexCount(
  Float32List xy, {
  required double halfWidth,
  required double scale,
}) => _walk(xy, halfWidth, scale, null);

/// Triangle-strip vertices for the contour in [xy], as x, y pairs.
Float32List strokeStrip(
  Float32List xy, {
  required double halfWidth,
  required double scale,
}) {
  final List<double> out = <double>[];
  _walk(xy, halfWidth, scale, out);
  return Float32List.fromList(out);
}

/// Triangles in a strip of [vertices] vertices.
int stripTriangles(int vertices) => math.max(0, vertices - 2);

int _walk(Float32List xy, double halfWidth, double scale, List<double>? out) {
  final double maxCosine = maximumJoinCosine(scale, halfWidth);
  int count = 0;
  void append(double x, double y, double nx, double ny) {
    count += 2;
    out
      ?..add(x + nx)
      ..add(y + ny)
      ..add(x - nx)
      ..add(y - ny);
  }

  bool hasSegment = false;
  double lastNx = 0;
  double lastNy = 0;
  for (int i = 2; i + 1 < xy.length; i += 2) {
    final double x1 = xy[i - 2];
    final double y1 = xy[i - 1];
    final double x2 = xy[i];
    final double y2 = xy[i + 1];
    final double dx = x2 - x1;
    final double dy = y2 - y1;
    final double length = math.sqrt(dx * dx + dy * dy);
    if (length == 0) {
      continue;
    }
    // Unit normal of this segment.
    final double nx = -dy / length;
    final double ny = dx / length;
    if (!hasSegment) {
      hasSegment = true;
      append(x1, y1, nx * halfWidth, ny * halfWidth);
    } else if (lastNx * nx + lastNy * ny < maxCosine) {
      // Bevel join at the shared point.
      append(x1, y1, nx * halfWidth, ny * halfWidth);
    }
    append(x2, y2, nx * halfWidth, ny * halfWidth);
    lastNx = nx;
    lastNy = ny;
  }
  return count;
}
