import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shader_lab/shader_lab.dart';

FrameWindowResult result(int worstMs) => FrameWindowResult(
  timeToSmooth: Duration.zero,
  stall: Duration.zero,
  worst: Duration(milliseconds: worstMs),
  frames: 16,
  overBudgetFrames: 0,
  timedOut: false,
);

FrameSample sample(int i) => FrameSample(
  vsyncStartMicros: i,
  rasterFinishMicros: i,
  build: Duration.zero,
  raster: Duration.zero,
);

Widget host(StormRecord record) => Directionality(
  textDirection: TextDirection.ltr,
  child: MediaQuery(
    data: const MediaQueryData(size: Size(412, 915)),
    child: ShaderStormScreen(rendererLabel: 'Skia · OpenGL ES', record: record),
  ),
);

void main() {
  test('every storm tile is a different effect combination', () {
    final List<StormTileSpec> tiles = stormTiles(48);

    expect(tiles, hasLength(48));
    expect(tiles.map((StormTileSpec t) => t.key).toSet(), hasLength(48));
    expect(
      stormTiles(48).map((StormTileSpec t) => t.key),
      tiles.map((StormTileSpec t) => t.key),
    );
  });

  test('the storm uses every fill, blur, filter and shape', () {
    final List<StormTileSpec> tiles = stormTiles(48);

    expect(
      tiles.map((StormTileSpec t) => t.fill).toSet(),
      StormFill.values.toSet(),
    );
    expect(
      tiles.map((StormTileSpec t) => t.blur).toSet(),
      StormBlur.values.toSet(),
    );
    expect(
      tiles.map((StormTileSpec t) => t.filter).toSet(),
      StormFilter.values.toSet(),
    );
    expect(
      tiles.map((StormTileSpec t) => t.shape).toSet(),
      StormShape.values.toSet(),
    );
  });

  test('only the first reveal of the process is recorded as first', () {
    final StormRecord record = StormRecord();
    expect(record.nextIsFirst, isTrue);

    record.add(result(300));
    record.add(result(12));
    record.add(result(9));

    expect(record.first!.worst, const Duration(milliseconds: 300));
    expect(record.repeat!.worst, const Duration(milliseconds: 9));
    expect(record.nextIsFirst, isFalse);
  });

  test('frame history keeps the newest frames up to capacity', () {
    final FrameHistory history = FrameHistory(capacity: 3);
    history.add(<FrameSample>[for (int i = 1; i <= 5; i++) sample(i)]);

    expect(history.frames.map((FrameSample s) => s.vsyncStartMicros), <int>[
      3,
      4,
      5,
    ]);
    history.dispose();
  });

  testWidgets('reveal draws every tile at once', (WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(host(StormRecord()));

    expect(find.text('Shader Storm'), findsOneWidget);
    expect(find.text('48 effects not drawn yet'), findsOneWidget);
    expect(find.text('FIRST REVEAL · WORST FRAME'), findsOneWidget);
    expect(find.text('REPEAT · WORST FRAME'), findsOneWidget);

    await tester.tap(find.text('REVEAL 48 EFFECTS'));
    await tester.pump();

    expect(find.byKey(const ValueKey<String>('storm-tile-0')), findsOneWidget);
    expect(find.byKey(const ValueKey<String>('storm-tile-47')), findsOneWidget);
    expect(find.text('···'), findsOneWidget);

    // The heartbeat never settles; unmount it before the test ends.
    await tester.pumpWidget(const SizedBox());
  });
}
