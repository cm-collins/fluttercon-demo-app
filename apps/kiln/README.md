# Kiln

The single Flutter application for the Impeller talk demo. Android product flavors build
two separately installable profile APKs from the same Dart code and Flutter SDK.

```text
flutter run --profile --flavor impeller \
  --dart-define='KILN_RENDERER=Impeller · Vulkan'

flutter run --profile --flavor skia \
  --dart-define='KILN_RENDERER=Skia · OpenGL ES'
```

The `impeller` flavor explicitly enables Impeller and owns `kiln://` deep links. The `skia`
flavor disables Impeller, uses the `dev.fluttercon.kiln.skia` package ID and does not
register the deep-link scheme.
