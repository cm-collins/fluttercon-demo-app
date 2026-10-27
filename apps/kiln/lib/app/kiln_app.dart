import 'package:flutter/material.dart';
import 'package:shader_lab/shader_lab.dart';

import '../features/markets/data/binance_gateway.dart';
import '../features/markets/logic/market_gateway.dart';
import '../features/markets/presentation/markets_route.dart';
import 'home_screen.dart';
import 'kiln_runtime.dart';

/// Routes match the path of `kiln://scenario/<name>` deep links.
abstract final class KilnRoutes {
  static const String home = '/';
  static const String shaderLab = '/shaderlab';
}

class KilnApp extends StatelessWidget {
  const KilnApp({
    super.key,
    this.runtime = KilnRuntime.impeller,
    this.gateway = const BinanceGateway(),
  });

  final KilnRuntime runtime;
  final MarketGateway gateway;

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
        return KilnScope(
          runtime: runtime,
          gateway: gateway,
          child: child ?? const SizedBox(),
        );
      },
      onGenerateRoute: (RouteSettings settings) {
        final Widget page = switch (settings.name) {
          KilnRoutes.shaderLab => MarketsRoute(
            runtime: runtime,
            gateway: gateway,
          ),
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
  const KilnScope({
    super.key,
    required this.runtime,
    required this.gateway,
    required super.child,
  });

  final KilnRuntime runtime;
  final MarketGateway gateway;

  static KilnScope _scope(BuildContext context) {
    final KilnScope? scope = context
        .dependOnInheritedWidgetOfExactType<KilnScope>();
    assert(scope != null, 'KilnScope was not found');
    return scope!;
  }

  static KilnRuntime of(BuildContext context) => _scope(context).runtime;

  static MarketGateway gatewayOf(BuildContext context) =>
      _scope(context).gateway;

  @override
  bool updateShouldNotify(KilnScope oldWidget) {
    return runtime != oldWidget.runtime || gateway != oldWidget.gateway;
  }
}
