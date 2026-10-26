import 'package:flutter/material.dart';
import 'package:shader_lab/shader_lab.dart';

import '../../app/kiln_build_config.dart';

/// Lives for the whole process so runs survive leaving and re-entering the screen.
final RunBoard shaderLabRuns = RunBoard();

/// Thin wrapper: all Shader Lab UI lives in `packages/shader_lab`.
class ShaderLabRoute extends StatelessWidget {
  const ShaderLabRoute({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ShaderLabScreen(
        rendererLabel: KilnBuildConfig.rendererLabel,
        board: shaderLabRuns,
      ),
    );
  }
}
