import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shader_lab/shader_lab.dart';

Widget host(RunBoard board) => Directionality(
  textDirection: TextDirection.ltr,
  child: MediaQuery(
    data: const MediaQueryData(size: Size(412, 915)),
    child: ShaderLabScreen(
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
    expect(find.text('Skia · OpenGL ES'), findsOneWidget);
    expect(find.text('DRAW DEPTH'), findsOneWidget);
    expect(find.text('Depth shader has not been drawn.'), findsOneWidget);
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

    expect(find.text('Depth shader has not been drawn.'), findsNothing);
    expect(find.text('·.···'), findsOneWidget);
  });
}
