import 'dart:math' as math;
import 'dart:typed_data';

/// The four fixes on the Canvas Thrash screen, each swapping one drawing
/// pattern for a cheaper one that looks the same.
enum ThrashFix {
  simplifyPaths('Simplify paths', 'raster'),
  batchDraws('Batch draws', 'raster'),
  glowWithoutLayers('Glow without layers', 'raster'),
  isolateRepaints('Isolate repaints', 'UI');

  const ThrashFix(this.label, this.lane);

  final String label;

  /// The frame lane this fix is meant to relieve.
  final String lane;
}

/// Thrash dial settings.
const List<int> thrashLevels = <int>[1, 2, 4, 8];

/// How much the canvas draws at one thrash level, and the made-up market data
/// it draws. Everything is derived from [level], so every run is identical.
class ThrashScene {
  ThrashScene(this.level) : assert(thrashLevels.contains(level));

  final int level;

  int get lineCount => 2 * level;
  int get pointsPerLine => 1000 * level;
  int get dotsPerLine => 4;
  int get dotCount => lineCount * dotsPerLine;
  int get stripSegments => 60 * level;

  /// Seconds for a price line to scroll across the whole canvas once.
  static const double scrollSeconds = 12;

  /// Seconds for one cycle of the heat strip.
  static const double heatSeconds = 2;

  /// One price series per line, each between 0 and 1, ending where it starts
  /// so it can scroll forever without a jump.
  late final List<Float32List> series = <Float32List>[
    for (int i = 0; i < lineCount; i++)
      periodicWalk(pointsPerLine, seed: i + 1),
  ];

  /// Fraction of the canvas width the lines have scrolled left at [seconds].
  static double scrollAt(double seconds) => (seconds / scrollSeconds) % 1;

  /// Height of heat strip segment [k] of [count] at [seconds], between 0.1
  /// and 0.9. Three slow waves across the strip with finer ripples on top;
  /// the shape depends on the position across the strip, not on [count], so
  /// the dial adds detail without changing the picture.
  static double heatAt(int k, int count, double seconds) {
    final double across = k / count;
    final double phase = seconds / heatSeconds * 2 * math.pi;
    return 0.5 +
        0.25 * math.sin(across * 6 * math.pi + phase) +
        0.15 * math.sin(across * 40 * math.pi - phase * 1.7);
  }
}

/// A seeded random walk of [length] values scaled to 0..1, with its drift
/// removed so the last value meets the first.
Float32List periodicWalk(int length, {required int seed}) {
  final math.Random random = math.Random(seed);
  final Float32List values = Float32List(length);
  double value = 0;
  for (int i = 0; i < length; i++) {
    value += random.nextDouble() - 0.5;
    values[i] = value;
  }
  final double drift = length > 1 ? (values[length - 1] - values[0]) : 0;
  double low = double.infinity;
  double high = double.negativeInfinity;
  for (int i = 0; i < length; i++) {
    values[i] -= drift * i / math.max(1, length - 1);
    low = math.min(low, values[i]);
    high = math.max(high, values[i]);
  }
  final double range = high - low;
  for (int i = 0; i < length; i++) {
    values[i] = range == 0 ? 0.5 : (values[i] - low) / range;
  }
  return values;
}

/// Keeps at most two values per pixel column: the lowest and the highest, in
/// the order they occur, so the line keeps its shape on screen.
///
/// Returns x, value pairs with x in 0..[width] for an unscrolled line.
Float32List decimate(Float32List series, double width) {
  final int n = series.length;
  final int columns = math.max(1, width.ceil());
  if (n <= 2 * columns) {
    final Float32List all = Float32List(2 * n);
    for (int i = 0; i < n; i++) {
      all[2 * i] = width * i / n;
      all[2 * i + 1] = series[i];
    }
    return all;
  }
  final List<double> out = <double>[];
  int i = 0;
  for (int column = 0; column < columns && i < n; column++) {
    final int end = math.min(n, ((column + 1) * n / columns).ceil());
    int lowAt = i;
    int highAt = i;
    for (int j = i; j < end; j++) {
      if (series[j] < series[lowAt]) {
        lowAt = j;
      }
      if (series[j] > series[highAt]) {
        highAt = j;
      }
    }
    final int first = math.min(lowAt, highAt);
    final int second = math.max(lowAt, highAt);
    out
      ..add(width * first / n)
      ..add(series[first]);
    if (second != first) {
      out
        ..add(width * second / n)
        ..add(series[second]);
    }
    i = end;
  }
  return Float32List.fromList(out);
}
