import 'package:flutter/material.dart';
import 'package:shader_lab/shader_lab.dart';

/// Lives for the whole process so runs survive leaving and re-entering the screen.
final RunBoard shaderLabRuns = RunBoard();

/// Thin wrapper: all Shader Lab UI lives in `packages/shader_lab`.
class ShaderLabRoute extends StatelessWidget {
  const ShaderLabRoute({super.key});

  // Neither SDK exposes the active backend to Dart; confirm with
  // `adb logcat` in rehearsal (TRD 9.3) and change if the phone falls back.
  static const String rendererLabel = 'Impeller · Vulkan';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ShaderLabScreen(rendererLabel: rendererLabel, board: shaderLabRuns),
    );
  }
}
