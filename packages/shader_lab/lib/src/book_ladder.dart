import 'package:flutter/widgets.dart';

import 'lab_tokens.dart';
import 'market.dart';

/// Visible bid and ask prices. Text and solid colour only.
class BookLadder extends StatelessWidget {
  const BookLadder({super.key, required this.bids, required this.asks});

  final List<BookLevel> bids;
  final List<BookLevel> asks;

  @override
  Widget build(BuildContext context) {
    final int available = bids.length > asks.length ? bids.length : asks.length;
    final int rows = available > 8 ? 8 : available;
    final double maxQty = _maxQuantity(rows);
    return Column(
      children: <Widget>[
        const Row(
          children: <Widget>[
            Expanded(child: Text('BID', style: LabText.label)),
            SizedBox(width: 12),
            Expanded(
              child: Text(
                'ASK',
                textAlign: TextAlign.right,
                style: LabText.label,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        for (int i = 0; i < rows; i++)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Row(
              children: <Widget>[
                Expanded(child: _side(i, bids, maxQty, LabColors.green, true)),
                const SizedBox(width: 8),
                Expanded(child: _side(i, asks, maxQty, LabColors.red, false)),
              ],
            ),
          ),
      ],
    );
  }

  double _maxQuantity(int rows) {
    double max = 0;
    for (final List<BookLevel> levels in <List<BookLevel>>[bids, asks]) {
      for (int i = 0; i < rows && i < levels.length; i++) {
        if (levels[i].quantity > max) {
          max = levels[i].quantity;
        }
      }
    }
    return max == 0 ? 1 : max;
  }

  Widget _side(
    int index,
    List<BookLevel> levels,
    double maxQty,
    Color color,
    bool bid,
  ) {
    if (index >= levels.length) {
      return const SizedBox(height: 28);
    }
    final BookLevel level = levels[index];
    final double fraction = (level.quantity / maxQty).clamp(0.08, 1.0);
    final Widget qty = Text(
      level.quantity.toStringAsFixed(3),
      style: LabText.number.copyWith(
        color: LabColors.textSecondary,
        fontSize: 13,
      ),
    );
    final Widget price = Text(
      formatQuote(level.price),
      style: LabText.number.copyWith(color: color, fontSize: 14),
    );
    return SizedBox(
      height: 28,
      child: Stack(
        alignment: bid ? Alignment.centerRight : Alignment.centerLeft,
        children: <Widget>[
          FractionallySizedBox(
            widthFactor: fraction,
            heightFactor: 1,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.16),
                borderRadius: BorderRadius.circular(6),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 6),
            child: FittedBox(
              fit: BoxFit.scaleDown,
              alignment: bid ? Alignment.centerRight : Alignment.centerLeft,
              child: Row(
                children: bid
                    ? <Widget>[qty, const SizedBox(width: 8), price]
                    : <Widget>[price, const SizedBox(width: 8), qty],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
