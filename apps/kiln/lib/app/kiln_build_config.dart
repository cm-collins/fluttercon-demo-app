abstract final class KilnBuildConfig {
  // This label describes the requested flavor configuration. Confirm the
  // renderer actually selected by the device from adb logcat before a demo.
  static const String rendererLabel = String.fromEnvironment(
    'KILN_RENDERER',
    defaultValue: 'Impeller · Vulkan',
  );

  static const bool isSkia = rendererLabel == 'Skia · OpenGL ES';

  static const String appLabel = isSkia ? 'Kiln Skia' : 'Kiln Impeller';
}
