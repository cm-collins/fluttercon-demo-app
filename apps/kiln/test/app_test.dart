import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kiln/app/kiln_app.dart';
import 'package:kiln/app/kiln_runtime.dart';

void main() {
  testWidgets('impeller flavor opens Shader Lab with its architecture', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(const KilnApp(runtime: KilnRuntime.impeller));
    expect(find.text('Kiln: Pit Wall'), findsOneWidget);
    expect(find.textContaining('Impeller ·'), findsOneWidget);

    await tester.tap(find.text('Shader Lab'));
    await tester.pumpAndSettle();

    expect(find.text('Impeller'), findsWidgets);
    expect(
      find.textContaining('Flutter uses Vulkan when this phone'),
      findsOneWidget,
    );
    expect(find.text('RECOVERY TIME · PRESS LIGHTS ON'), findsOneWidget);
    expect(find.text('LIGHTS ON'), findsOneWidget);
  });

  testWidgets('skia flavor identifies Skia on OpenGL ES', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(const KilnApp(runtime: KilnRuntime.skia));
    await tester.tap(find.text('Shader Lab'));
    await tester.pumpAndSettle();

    expect(find.text('Skia · OpenGL ES'), findsWidgets);
    expect(find.textContaining('Skia on OpenGL ES'), findsOneWidget);
  });
}
