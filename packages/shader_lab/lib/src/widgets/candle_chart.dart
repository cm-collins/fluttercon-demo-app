import 'dart:developer' show Timeline;

import 'package:flutter/widgets.dart';

import '../logic/market.dart';
import '../logic/paint_ledger.dart';
import 'lab_tokens.dart';

/// Solid candle bodies and wicks. No fragment shader and no blur.
///
/// [mode] decides whether a parent rebuild records this picture again.
/// The paint is wrapped in `KILN::Markets::candles` so DevTools and Perfetto
/// show the slice only when the chart actually paints.
class CandleChart extends StatelessWidget {
  const CandleChart({
    super.key,
    required this.candles,
    required this.mode,
    required this.ledger,
  });

  final List<Candle> candles;
  final LayerMode mode;
  final PaintLedger ledger;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 168,
      child: CustomPaint(
        painter: _CandlePainter(
          candles: candles,
          coupled: mode == LayerMode.coupled,
          ledger: ledger,
        ),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _CandlePainter extends CustomPainter {
  const _CandlePainter({
    required this.candles,
    required this.coupled,
    required this.ledger,
  });

  final List<Candle> candles;
  final bool coupled;
  final PaintLedger ledger;

  @override
  void paint(Canvas canvas, Size size) {
    Timeline.timeSync('KILN::Markets::candles', () {
      ledger.noteCandlePaint();
      _paint(canvas, size);
    });
  }

  void _paint(Canvas canvas, Size size) {
    if (candles.isEmpty || size.isEmpty) {
      return;
    }
    double low = candles.first.low;
    double high = candles.first.high;
    for (final Candle candle in candles) {
      if (candle.low < low) {
        low = candle.low;
      }
      if (candle.high > high) {
        high = candle.high;
      }
    }
    final double span = (high - low).abs() < 0.0000001 ? 1 : high - low;
    final Paint grid = Paint()
      ..color = LabColors.hairline
      ..strokeWidth = 1;
    for (int i = 1; i <= 3; i++) {
      final double y = size.height * i / 4;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }

    final double slot = size.width / candles.length;
    final double bodyWidth = slot * 0.62;
    for (int i = 0; i < candles.length; i++) {
      final Candle candle = candles[i];
      final double x = slot * i + slot / 2;
      double yOf(double price) => (high - price) / span * size.height;
      final Paint paint = Paint()
        ..color = candle.up ? LabColors.green : LabColors.red;
      canvas.drawLine(
        Offset(x, yOf(candle.high)),
        Offset(x, yOf(candle.low)),
        paint..strokeWidth = 1.5,
      );
      final double top = yOf(
        candle.open > candle.close ? candle.open : candle.close,
      );
      final double bottom = yOf(
        candle.open > candle.close ? candle.close : candle.open,
      );
      canvas.drawRect(
        Rect.fromLTRB(x - bodyWidth / 2, top, x + bodyWidth / 2, bottom + 1),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(_CandlePainter oldDelegate) {
    if (coupled != oldDelegate.coupled) {
      return true;
    }
    if (coupled) {
      return true;
    }
    return oldDelegate.candles != candles;
  }
}
