import 'package:flutter/widgets.dart';

import '../logic/paint_ledger.dart';

/// Coupled mode adds one opacity layer. Isolated mode keeps a repaint boundary.
///
/// An opacity of exactly 1 is skipped by the framework, so the coupled layer
/// uses a value just under 1. On Impeller the boundary does not cache raster
/// work. It stops the candle picture from being recorded again.
class LayerFrame extends StatelessWidget {
  const LayerFrame({super.key, required this.mode, required this.child});

  final LayerMode mode;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    if (mode == LayerMode.isolated) {
      return RepaintBoundary(child: child);
    }
    return Opacity(opacity: 0.995, child: child);
  }
}
