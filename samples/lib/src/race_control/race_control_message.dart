import 'dart:convert';

import 'package:flutter/widgets.dart';

import '../core/kiln_colors.dart';

/// One message from the OpenF1 `race_control` endpoint.
@immutable
class RaceControlMessage {
  const RaceControlMessage({
    required this.date,
    required this.category,
    required this.message,
    this.flag,
    this.lapNumber,
  });

  factory RaceControlMessage.fromJson(Map<String, Object?> json) {
    return RaceControlMessage(
      date: DateTime.parse(json['date']! as String),
      category: json['category']! as String,
      message: json['message']! as String,
      flag: json['flag'] as String?,
      lapNumber: json['lap_number'] as int?,
    );
  }

  final DateTime date;
  final String category;
  final String message;
  final String? flag;
  final int? lapNumber;
}

/// Decodes one batch (a JSON array) of race control messages.
List<RaceControlMessage> parseRaceControlBatch(String raw) {
  final decoded = jsonDecode(raw) as List<Object?>;
  return [
    for (final entry in decoded)
      RaceControlMessage.fromJson(entry! as Map<String, Object?>),
  ];
}

class RaceControlTile extends StatelessWidget {
  const RaceControlTile({super.key, required this.message});

  final RaceControlMessage message;

  @override
  Widget build(BuildContext context) {
    final lap = message.lapNumber == null ? '' : 'Lap ${message.lapNumber} · ';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$lap${message.flag ?? message.category}',
            style: const TextStyle(
              fontSize: 13,
              color: KilnColors.textSecondary,
            ),
          ),
          Text(
            message.message,
            style: const TextStyle(fontSize: 16, color: KilnColors.textPrimary),
          ),
        ],
      ),
    );
  }
}
