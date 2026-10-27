import 'package:flutter/foundation.dart';
import 'package:flutter/scheduler.dart';

/// How a price tick treats the candle chart.
enum LayerMode {
  /// The chart repaints with the price, inside its own opacity layer.
  coupled,

  /// The chart keeps its picture. The price is a separate widget.
  isolated,
}

/// Counts candle paints without rebuilding the chart during paint.
class PaintLedger extends ChangeNotifier {
  int candlePaints = 0;
  bool _scheduled = false;
  bool _disposed = false;

  void noteCandlePaint() {
    candlePaints++;
    if (_scheduled) {
      return;
    }
    _scheduled = true;
    SchedulerBinding.instance.addPostFrameCallback((_) {
      _scheduled = false;
      if (!_disposed) {
        notifyListeners();
      }
    });
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
