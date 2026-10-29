/// Facts shown beside a renderer comparison run.
///
/// [backend] is deliberately nullable: an Android flavor declares the engine
/// family, but the selected graphics API must be verified from engine startup
/// evidence. The UI must not turn an unverified Impeller run into a Vulkan claim.
class RendererEvidence {
  const RendererEvidence({
    required this.engine,
    required this.backend,
    required this.backendVerified,
    this.androidApi,
    this.device,
    this.flutterVersion,
    this.buildMode = 'profile',
  });

  final String engine;
  final String? backend;
  final bool backendVerified;
  final int? androidApi;
  final String? device;
  final String? flutterVersion;
  final String buildMode;

  String get backendLabel {
    if (backendVerified && backend != null) {
      return backend!;
    }
    return 'Unverified · adb logcat';
  }
}
