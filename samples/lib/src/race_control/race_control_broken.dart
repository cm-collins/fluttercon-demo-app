import 'package:flutter/widgets.dart';

import '../core/kiln_trace.dart';
import 'race_control_message.dart';

/// Anti-pattern: raw JSON batches are decoded inside `build()`.
///
/// Every rebuild decodes every batch on the main thread (where Dart runs since
/// Flutter 3.29), so the UI bar goes red while the raster bar stays green.
class RaceControlFeedBroken extends StatelessWidget {
  const RaceControlFeedBroken({super.key, required this.rawBatches});

  final List<String> rawBatches;

  @override
  Widget build(BuildContext context) {
    final messages = kilnTrace('RaceControl', 'decode', () {
      return [for (final batch in rawBatches) ...parseRaceControlBatch(batch)];
    });
    return ListView.builder(
      itemCount: messages.length,
      itemBuilder: (context, index) =>
          RaceControlTile(message: messages[index]),
    );
  }
}
