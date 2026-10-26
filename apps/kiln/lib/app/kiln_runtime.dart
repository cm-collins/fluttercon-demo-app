import 'package:flutter/services.dart';

enum KilnRendererFamily { impeller, skia }

/// Renderer identity selected by the Android product flavor.
///
/// The display refresh rate is read separately from the Flutter view. It sets
/// the frame budget, but it does not choose Vulkan or OpenGL ES. Flutter
/// selects Vulkan for the Impeller flavor when the phone's driver is valid and
/// otherwise uses OpenGL ES. The Skia flavor disables Impeller, which uses
/// OpenGL ES on Android. Confirm the selected backend in `adb logcat`.
class KilnRuntime {
  const KilnRuntime(this.family);

  static const KilnRuntime impeller = KilnRuntime(KilnRendererFamily.impeller);
  static const KilnRuntime skia = KilnRuntime(KilnRendererFamily.skia);
  static const MethodChannel _channel = MethodChannel(
    'dev.fluttercon.kiln/runtime',
  );

  final KilnRendererFamily family;

  static Future<KilnRuntime> load() async {
    try {
      final String? family = await _channel.invokeMethod<String>(
        'rendererFamily',
      );
      return family == 'skia' ? skia : impeller;
    } on MissingPluginException {
      return impeller;
    } on PlatformException {
      return impeller;
    }
  }

  String get label => switch (family) {
    KilnRendererFamily.skia => 'Skia · OpenGL ES',
    KilnRendererFamily.impeller => 'Impeller',
  };

  String get appLabel => switch (family) {
    KilnRendererFamily.skia => 'Kiln Skia',
    KilnRendererFamily.impeller => 'Kiln Impeller',
  };

  String get architectureNote => switch (family) {
    KilnRendererFamily.skia =>
      'Impeller is disabled, so this app renders with Skia on OpenGL ES.',
    KilnRendererFamily.impeller => 'Flutter uses Vulkan when this phone\'s driver is valid; otherwise OpenGL ES.',
  };
}
