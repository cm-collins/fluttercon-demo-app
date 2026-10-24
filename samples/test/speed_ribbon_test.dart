import 'dart:typed_data';
import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:kiln_samples/kiln_samples.dart';

void main() {
  test('KilnColors.speed maps the ends of the ramp', () {
    expect(KilnColors.speed(0), KilnColors.speedSlow);
    expect(KilnColors.speed(0.45), KilnColors.speedMid);
    expect(KilnColors.speed(1), KilnColors.speedFast);
  });

  test('buildRibbonVertices builds one mesh for the whole circuit', () {
    final geometry = RibbonGeometry(
      points: Float32List.fromList([0, 0, 0.5, 0, 1, 0.5, 0.5, 1]),
      speeds: Float32List.fromList([0, 0.3, 0.7, 1]),
    );
    final mesh = buildRibbonVertices(geometry, const Size(200, 100), 6);
    expect(mesh.debugDisposed, isFalse);
    mesh.dispose();
  });
}
