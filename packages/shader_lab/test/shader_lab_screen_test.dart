import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shader_lab/shader_lab.dart';

Widget host(RunBoard board) => Directionality(
  textDirection: TextDirection.ltr,
  child: MediaQuery(
    data: const MediaQueryData(size: Size(412, 915)),
    child: ShaderLabScreen(
      key: const ValueKey<String>('lab'),
      rendererLabel: 'Skia · OpenGL ES',
      board: board,
      snapshot: MarketSnapshot.sample,
      shaderAsset: 'shaders/depth_fill.frag',
    ),
  ),
);

void main() {
  testWidgets('shows the book before the depth shader is drawn', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(host(RunBoard()));

    expect(find.text('BTC/USDT'), findsOneWidget);
    // Once in the header badge and once in the renderer evidence card.
    expect(find.text('Skia · OpenGL ES'), findsNWidgets(2));
    expect(find.text('RENDERER EVIDENCE'), findsOneWidget);
    expect(find.text('DRAW DEPTH'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Depth shader has not been drawn.'),
      200,
    );
    expect(find.text('Depth shader has not been drawn.'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('RECOVERY TIME · PRESS DRAW DEPTH'),
      200,
    );
    expect(find.text('RECOVERY TIME · PRESS DRAW DEPTH'), findsOneWidget);
    expect(find.text('ACCUMULATED OVERRUN'), findsOneWidget);
    expect(find.text('SLOWEST FRAME'), findsOneWidget);
    expect(find.text('FIRST − REPEAT'), findsOneWidget);
    expect(find.text('–.–––'), findsOneWidget);
  });

  testWidgets('Draw depth mounts the shader once it has loaded', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(host(RunBoard()));
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 200)),
    );
    await tester.pump();

    await tester.tap(find.text('DRAW DEPTH'));
    await tester.pump();
    await tester.scrollUntilVisible(find.text('Depth'), 200);
    expect(find.text('Depth shader has not been drawn.'), findsNothing);
    await tester.scrollUntilVisible(find.textContaining('RECOVERY TIME'), 200);
    expect(find.text('RECOVERY TIME · PRESS DRAW DEPTH'), findsNothing);
  });

  testWidgets(
    'an isolated chart does not repaint when only the price changes',
    (WidgetTester tester) async {
      await tester.binding.setSurfaceSize(const Size(412, 915));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      final RunBoard board = RunBoard();
      await tester.pumpWidget(host(board));
      await tester.pump();
      expect(find.text('Candle paints 1'), findsOneWidget);

      await tester.pumpWidget(
        _host(board, _priced(MarketSnapshot.sample, 80000)),
      );
      await tester.pump();
      expect(find.text('Candle paints 1'), findsOneWidget);
    },
  );

  testWidgets('a coupled chart repaints when only the price changes', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    final RunBoard board = RunBoard();
    await tester.pumpWidget(host(board));
    await tester.pump();
    await tester.scrollUntilVisible(find.text('Coupled'), 200);
    await tester.tap(find.text('Coupled'));
    await tester.pump();
    await tester.pump();
    final int afterToggle = _paintCount(tester);

    await tester.pumpWidget(
      _host(board, _priced(MarketSnapshot.sample, 81000)),
    );
    await tester.pump();
    await tester.pump();
    expect(_paintCount(tester), greaterThan(afterToggle));
  });
}

Widget _host(RunBoard board, MarketSnapshot snapshot) {
  return Directionality(
    textDirection: TextDirection.ltr,
    child: MediaQuery(
      data: const MediaQueryData(size: Size(412, 915)),
      child: ShaderLabScreen(
        key: const ValueKey<String>('lab'),
        rendererLabel: 'Skia · OpenGL ES',
        board: board,
        snapshot: snapshot,
        shaderAsset: 'shaders/depth_fill.frag',
      ),
    ),
  );
}

MarketSnapshot _priced(MarketSnapshot snapshot, double last) {
  return MarketSnapshot(
    quote: snapshot.quote.withLast(last),
    candles: snapshot.candles,
    bids: snapshot.bids,
    asks: snapshot.asks,
  );
}

int _paintCount(WidgetTester tester) {
  final String text = tester
      .widget<Text>(find.textContaining('Candle paints'))
      .data!;
  return int.parse(text.replaceAll('Candle paints ', ''));
}
