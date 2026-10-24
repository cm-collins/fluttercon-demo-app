import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

/// Loads `shaders/speed_ramp.frag`.
///
/// The shader is compiled by `impellerc` when the app is built, so loading it
/// never triggers shader compilation on the device.
Future<ui.FragmentShader> loadSpeedRampShader({
  String assetKey = 'packages/kiln_samples/shaders/speed_ramp.frag',
}) async {
  final program = await ui.FragmentProgram.fromAsset(assetKey);
  return program.fragmentShader();
}

/// Fills its area with the animated speed ramp in a single draw.
class SpeedRampPainter extends CustomPainter {
  SpeedRampPainter({required this.shader, required this.time}) : super(repaint: time);

  final ui.FragmentShader shader;

  /// Seconds; drives the shimmer.
  final ValueListenable<double> time;

  @override
  void paint(Canvas canvas, Size size) {
    shader
      ..setFloat(0, size.width)
      ..setFloat(1, size.height)
      ..setFloat(2, time.value);
    canvas.drawRect(Offset.zero & size, Paint()..shader = shader);
  }

  @override
  bool shouldRepaint(SpeedRampPainter oldDelegate) {
    return oldDelegate.shader != shader || oldDelegate.time != time;
  }
}
