import 'dart:developer';

/// Runs [body] inside a timeline span named `KILN::<scenario>::<phase>`.
///
/// The span shows up in DevTools Timeline Events and, when the app runs with
/// `--trace-systrace`, in Perfetto next to the engine's own events.
T kilnTrace<T>(String scenario, String phase, T Function() body) {
  return Timeline.timeSync('KILN::$scenario::$phase', body);
}
