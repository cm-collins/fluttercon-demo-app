import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kiln/app/kiln_app.dart';
import 'package:kiln/app/kiln_runtime.dart';
import 'package:kiln/features/markets/logic/market_gateway.dart';
import 'package:shader_lab/shader_lab.dart';

class FakeGateway extends MarketGateway {
  const FakeGateway();

  @override
  Future<List<MarketQuote>> watchlist() async {
    return <MarketQuote>[MarketSnapshot.sample.quote];
  }

  @override
  Future<MarketSnapshot> load(String symbol) async => MarketSnapshot.sample;

  @override
  Stream<double> trades(String symbol) => const Stream<double>.empty();
}

void main() {
  testWidgets('impeller flavor opens the Binance book', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      const KilnApp(runtime: KilnRuntime.impeller, gateway: FakeGateway()),
    );
    expect(find.text('Kiln Markets'), findsOneWidget);
    expect(find.text('Impeller'), findsOneWidget);
    expect(find.textContaining('Hz ·'), findsOneWidget);

    await tester.tap(find.text('Markets'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('BTC/USDT'));
    await tester.pumpAndSettle();

    expect(find.text('Impeller'), findsWidgets);
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
    await tester.scrollUntilVisible(
      find.textContaining('Flutter uses Vulkan when this phone'),
      200,
    );
    expect(
      find.textContaining('Flutter uses Vulkan when this phone'),
      findsOneWidget,
    );
  });

  testWidgets('skia flavor identifies Skia on OpenGL ES', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      const KilnApp(runtime: KilnRuntime.skia, gateway: FakeGateway()),
    );
    await tester.tap(find.text('Markets'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('BTC/USDT'));
    await tester.pumpAndSettle();

    expect(find.text('Skia · OpenGL ES'), findsWidgets);
    await tester.scrollUntilVisible(
      find.textContaining('Skia on OpenGL ES'),
      200,
    );
    expect(find.textContaining('Skia on OpenGL ES'), findsOneWidget);
  });
}
