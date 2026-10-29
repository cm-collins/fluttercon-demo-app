import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:shader_lab/shader_lab.dart';

enum KilnRendererFamily { impeller, skia }

/// Renderer identity selected by the Android product flavor.
///
/// The display refresh rate is read separately from the Flutter view. It sets
/// the frame budget, but it does not choose Vulkan or OpenGL ES. Flutter
/// selects Vulkan for the Impeller flavor when the phone's driver is valid and
/// otherwise uses OpenGL ES. The Skia flavor disables Impeller, which uses
/// OpenGL ES on Android. Confirm the selected backend in `adb logcat`.
class KilnRuntime {
  const KilnRuntime(this.family, {this.evidence = _defaultEvidence});

  static const KilnRuntime impeller = KilnRuntime(KilnRendererFamily.impeller);
  static const KilnRuntime skia = KilnRuntime(
    KilnRendererFamily.skia,
    evidence: _skiaEvidence,
  );
  static const RendererEvidence _defaultEvidence = RendererEvidence(
    engine: 'Impeller',
    backend: null,
    backendVerified: false,
  );
  static const RendererEvidence _skiaEvidence = RendererEvidence(
    engine: 'Skia',
    backend: 'OpenGL ES',
    backendVerified: false,
  );
  static const MethodChannel _channel = MethodChannel(
    'dev.fluttercon.kiln/runtime',
  );

  final KilnRendererFamily family;
  final RendererEvidence evidence;

  static Future<KilnRuntime> load() async {
    try {
      final dynamic raw = await _channel.invokeMethod<dynamic>(
        'rendererEvidence',
      );
      if (raw is Map) {
        final String familyName = '${raw['family']}';
        final KilnRendererFamily selected = familyName == 'skia'
            ? KilnRendererFamily.skia
            : KilnRendererFamily.impeller;
        return KilnRuntime(
          selected,
          evidence: RendererEvidence(
            engine: selected == KilnRendererFamily.skia ? 'Skia' : 'Impeller',
            backend: raw['backend'] as String?,
            backendVerified: raw['backendVerified'] == true,
            androidApi: raw['androidApi'] as int?,
            device: raw['device'] as String?,
            flutterVersion: raw['flutterVersion'] as String?,
            buildMode: kProfileMode
                ? 'profile'
                : kReleaseMode
                ? 'release'
                : 'debug',
          ),
        );
      }
      final String? family = raw as String?;
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
