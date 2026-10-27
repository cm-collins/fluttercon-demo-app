String formatLap(Duration d) => (d.inMicroseconds / 1000000).toStringAsFixed(3);

String formatSignedLap(Duration d) {
  if (d == Duration.zero) {
    return '0.000';
  }
  final String sign = d.isNegative ? '−' : '+';
  return '$sign${formatLap(d.abs())}';
}

String formatMs(Duration d) => (d.inMicroseconds / 1000).toStringAsFixed(1);
