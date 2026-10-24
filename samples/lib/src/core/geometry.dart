import 'dart:typed_data';
import 'dart:ui';

/// Builds a polyline from interleaved, normalised `x, y` pairs scaled to [size].
Path polylinePath(Float32List xy, Size size, {bool close = false}) {
  final path = Path();
  if (xy.length < 2) {
    return path;
  }
  path.moveTo(xy[0] * size.width, xy[1] * size.height);
  for (var i = 2; i + 1 < xy.length; i += 2) {
    path.lineTo(xy[i] * size.width, xy[i + 1] * size.height);
  }
  if (close) {
    path.close();
  }
  return path;
}
