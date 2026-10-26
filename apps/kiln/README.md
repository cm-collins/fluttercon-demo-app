# Kiln

The single Flutter application for the Impeller talk demo. Android product flavors build
two separately installable profile APKs from the same Dart code and Flutter SDK.

```text
flutter run --profile --flavor impeller

flutter run --profile --flavor skia
```

The `impeller` flavor enables Impeller and owns `kiln://` deep links. Flutter uses Vulkan
when the phone's driver is valid and otherwise uses OpenGL ES. The `skia` flavor disables
Impeller, so Android renders with Skia on OpenGL ES. The display refresh rate is read at
runtime and sets the frame budget automatically.
