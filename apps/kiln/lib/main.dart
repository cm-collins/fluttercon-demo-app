import 'package:flutter/widgets.dart';

import 'app/kiln_app.dart';
import 'app/kiln_runtime.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final KilnRuntime runtime = await KilnRuntime.load();
  runApp(KilnApp(runtime: runtime));
}
