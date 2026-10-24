import 'dart:isolate';

import 'package:flutter/widgets.dart';

import 'race_control_message.dart';

/// Fix: batches are decoded once, on a background isolate, and the list only
/// reads already-decoded messages.
class RaceControlFeedController extends ValueNotifier<List<RaceControlMessage>> {
  RaceControlFeedController() : super(const []);

  Future<void> ingest(String rawBatch) async {
    final parsed = await _decode(rawBatch);
    value = [...value, ...parsed];
  }

  // Static so the isolate closure captures only the string, never `this`.
  static Future<List<RaceControlMessage>> _decode(String raw) {
    return Isolate.run(() => parseRaceControlBatch(raw));
  }
}

class RaceControlFeedFixed extends StatelessWidget {
  const RaceControlFeedFixed({super.key, required this.controller});

  final RaceControlFeedController controller;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<List<RaceControlMessage>>(
      valueListenable: controller,
      builder: (context, messages, _) => ListView.builder(
        itemCount: messages.length,
        itemBuilder: (context, index) => RaceControlTile(message: messages[index]),
      ),
    );
  }
}
