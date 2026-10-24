import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:kiln_samples/kiln_samples.dart';

void main() {
  group('decimateMinMax', () {
    test('returns the input when it already fits the buckets', () {
      final values = Float32List.fromList([0.1, 0.5, 0.9]);
      expect(decimateMinMax(values, 10), same(values));
    });

    test('keeps two samples per bucket', () {
      final values = Float32List(4000);
      expect(decimateMinMax(values, 360).length, 720);
    });

    test('preserves the global minimum and maximum', () {
      final values = Float32List(4000)..fillRange(0, 4000, 0.5);
      values[1234] = 0.02;
      values[3210] = 0.98;
      final out = decimateMinMax(values, 100);
      expect(out.reduce((a, b) => a < b ? a : b), closeTo(0.02, 1e-6));
      expect(out.reduce((a, b) => a > b ? a : b), closeTo(0.98, 1e-6));
    });
  });
}
