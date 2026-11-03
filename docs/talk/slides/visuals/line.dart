import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import '/home/sparrow/dev/mobile/fluttercon-demo-app/packages/shader_lab/lib/src/logic/thrash_scene.dart';
void main() {
  final scene = ThrashScene(8);
  final lines = <List<double>>[];
  for (final s in scene.series) { lines.add(s.map((v) => double.parse(v.toStringAsFixed(5))).toList()); }
  final dec = <List<double>>[];
  for (final s in scene.series) { dec.add(decimate(s, 316).map((v) => double.parse(v.toStringAsFixed(4))).toList()); }
  File('line.json').writeAsStringSync(jsonEncode({'lines': lines.sublist(0, 16), 'dec': dec, 'n': scene.pointsPerLine}));
  print('ok ${lines.length} lines, ${lines[0].length} points, decimated ${dec[0].length ~/ 2}');
}
