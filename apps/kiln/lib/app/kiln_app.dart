import 'package:flutter/material.dart';
import 'package:shader_lab/shader_lab.dart';

import '../features/shader_lab/shader_lab_route.dart';
import 'home_screen.dart';

/// Routes match the path of `kiln://scenario/<name>` deep links.
abstract final class KilnRoutes {
  static const String home = '/';
  static const String shaderLab = '/shaderlab';
}

class KilnApp extends StatelessWidget {
  const KilnApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kiln',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: LabColors.bg,
        splashFactory: NoSplash.splashFactory,
      ),
      onGenerateRoute: (RouteSettings settings) {
        final Widget page = switch (settings.name) {
          KilnRoutes.shaderLab => const ShaderLabRoute(),
          _ => const HomeScreen(),
        };
        return MaterialPageRoute<void>(
          settings: settings,
          builder: (BuildContext context) => page,
        );
      },
    );
  }
}
