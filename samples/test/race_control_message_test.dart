import 'package:flutter_test/flutter_test.dart';
import 'package:kiln_samples/kiln_samples.dart';

void main() {
  test('parseRaceControlBatch decodes OpenF1 race_control entries', () {
    const raw = '''
[
  {"date": "2024-03-02T15:03:12+00:00", "category": "Flag", "flag": "YELLOW",
   "message": "YELLOW IN TRACK SECTOR 4", "lap_number": 12},
  {"date": "2024-03-02T15:10:40+00:00", "category": "Drs",
   "message": "DRS ENABLED", "lap_number": null}
]
''';
    final messages = parseRaceControlBatch(raw);
    expect(messages, hasLength(2));
    expect(messages.first.flag, 'YELLOW');
    expect(messages.first.lapNumber, 12);
    expect(messages.last.flag, isNull);
    expect(messages.last.message, 'DRS ENABLED');
  });
}
