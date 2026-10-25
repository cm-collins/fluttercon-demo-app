import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kiln/app/kiln_app.dart';

void main() {
  testWidgets('home opens Shader Lab with the Impeller badge',
      (WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(const KilnApp());
    expect(find.text('Kiln: Pit Wall'), findsOneWidget);

    await tester.tap(find.text('Shader Lab'));
    await tester.pumpAndSettle();

    expect(find.text('Impeller · Vulkan'), findsOneWidget);
    expect(find.text('LIGHTS ON'), findsOneWidget);
  });
}
