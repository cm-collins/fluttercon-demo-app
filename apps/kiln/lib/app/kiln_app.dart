import 'package:flutter/material.dart';
import 'package:shader_lab/shader_lab.dart';

import '../features/shader_lab/shader_lab_route.dart';
import 'home_screen.dart';
import 'kiln_runtime.dart';

/// Routes match the path of `kiln://scenario/<name>` deep links.
abstract final class KilnRoutes {
  static const String home = '/';
  static const String shaderLab = '/shaderlab';
}

class KilnApp extends StatelessWidget {
  const KilnApp({super.key, this.runtime = KilnRuntime.impeller});

  final KilnRuntime runtime;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: runtime.appLabel,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: LabColors.bg,
        splashFactory: NoSplash.splashFactory,
      ),
      builder: (BuildContext context, Widget? child) {
        return KilnScope(runtime: runtime, child: child ?? const SizedBox());
      },
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

class KilnScope extends InheritedWidget {
  const KilnScope({super.key, required this.runtime, required super.child});

  final KilnRuntime runtime;

  static KilnRuntime of(BuildContext context) {
    final KilnScope? scope = context
        .dependOnInheritedWidgetOfExactType<KilnScope>();
    assert(scope != null, 'KilnScope was not found');
    return scope!.runtime;
  }

  @override
  bool updateShouldNotify(KilnScope oldWidget) => runtime != oldWidget.runtime;
}
