import 'dart:typed_data';
import 'dart:ui';

import '../core/kiln_colors.dart';

/// One telemetry channel (for example speed) for one driver over one lap.
class TelemetryTrace {
  TelemetryTrace({required this.label, required this.values, required this.color});

  final String label;

  /// Normalised samples in the range 0..1, evenly spaced over the lap.
  final Float32List values;

  final Color color;

  Path? _cachedPath;
  Size? _cachedSize;

  /// A path reduced to screen resolution, rebuilt only when [size] changes.
  Path cachedPath(Size size) {
    if (_cachedPath == null || _cachedSize != size) {
      _cachedPath = buildTracePath(decimateMinMax(values, size.width.ceil()), size);
      _cachedSize = size;
    }
    return _cachedPath!;
  }
}

/// Straight-line path through evenly spaced [values], scaled to [size].
Path buildTracePath(Float32List values, Size size) {
  final path = Path();
  if (values.isEmpty) {
    return path;
  }
  final dx = values.length > 1 ? size.width / (values.length - 1) : 0.0;
  path.moveTo(0, size.height * (1 - values[0]));
  for (var i = 1; i < values.length; i++) {
    path.lineTo(i * dx, size.height * (1 - values[i]));
  }
  return path;
}

/// Reduces [values] to at most two samples per bucket (its minimum and maximum,
/// in their original order) so peaks such as braking points survive.
///
/// With one bucket per logical pixel the trace looks the same but the engine
/// tessellates a fraction of the segments.
Float32List decimateMinMax(Float32List values, int buckets) {
  if (buckets <= 0 || values.length <= buckets * 2) {
    return values;
  }
  final out = Float32List(buckets * 2);
  final step = values.length / buckets;
  for (var b = 0; b < buckets; b++) {
    final start = (b * step).floor();
    final end = ((b + 1) * step).floor().clamp(start + 1, values.length);
    var minIndex = start;
    var maxIndex = start;
    for (var i = start + 1; i < end; i++) {
      if (values[i] < values[minIndex]) {
        minIndex = i;
      }
      if (values[i] > values[maxIndex]) {
        maxIndex = i;
      }
    }
    final first = minIndex <= maxIndex ? minIndex : maxIndex;
    final second = minIndex <= maxIndex ? maxIndex : minIndex;
    out[b * 2] = values[first];
    out[b * 2 + 1] = values[second];
  }
  return out;
}

/// Vertical cursor showing the replay position within the lap.
void paintLapCursor(Canvas canvas, Size size, double progress) {
  final x = size.width * progress.clamp(0.0, 1.0);
  canvas.drawLine(
    Offset(x, 0),
    Offset(x, size.height),
    Paint()
      ..color = KilnColors.textPrimary
      ..strokeWidth = 1.5,
  );
}
