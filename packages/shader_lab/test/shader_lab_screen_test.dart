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
      shaderAsset: 'shaders/speed_ramp.frag',
    ),
  ),
);

void main() {
  testWidgets('shows the renderer badge and an empty lap before any run', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(host(RunBoard()));

    expect(find.text('Skia · OpenGL ES'), findsOneWidget);
    expect(find.text('LIGHTS ON'), findsOneWidget);
    expect(find.text('RECOVERY TIME · PRESS LIGHTS ON'), findsOneWidget);
    expect(find.text('ACCUMULATED OVERRUN'), findsOneWidget);
    expect(find.text('SLOWEST FRAME'), findsOneWidget);
    expect(find.text('FIRST − REPEAT'), findsOneWidget);
    expect(find.text('–.–––'), findsOneWidget);
  });

  testWidgets('Lights on reveals the scene once the shader has loaded', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(host(RunBoard()));
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 200)),
    );
    await tester.pump();

    await tester.tap(find.text('LIGHTS ON'));
    await tester.pump();

    expect(find.text('LIGHTS OFF'), findsOneWidget);
    expect(find.text('·.···'), findsOneWidget);

    await tester.tap(find.text('LIGHTS OFF'));
    await tester.pump();
    expect(find.text('LIGHTS ON'), findsOneWidget);
  });
}
