import 'package:flutter/material.dart';
import 'package:shader_lab/shader_lab.dart';

final RunBoard _runs = RunBoard();

void main() => runApp(const KilnSkiaApp());

class KilnSkiaApp extends StatelessWidget {
  const KilnSkiaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kiln Skia',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: LabColors.bg,
        splashFactory: NoSplash.splashFactory,
      ),
      home: Scaffold(
        body: ShaderLabScreen(rendererLabel: 'Skia · OpenGL ES', board: _runs),
      ),
    );
  }
}
