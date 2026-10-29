import 'package:flutter/widgets.dart';

import 'app/kiln_app.dart';
import 'app/kiln_runtime.dart';
import 'features/markets/data/binance_gateway.dart';
import 'features/markets/data/fixture_gateway.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final KilnRuntime runtime = await KilnRuntime.load();
  const bool benchmarkMode = bool.fromEnvironment('KILN_BENCHMARK');
  runApp(
    KilnApp(
      runtime: runtime,
      benchmarkMode: benchmarkMode,
      gateway: benchmarkMode ? const FixtureGateway() : const BinanceGateway(),
    ),
  );
}
