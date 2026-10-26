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
    final int rows = bids.length > asks.length ? bids.length : asks.length;
    return Column(
      children: <Widget>[
        const Row(
          children: <Widget>[
            Expanded(child: Text('BID QTY', style: LabText.label)),
            Expanded(
              child: Text(
                'BID',
                textAlign: TextAlign.right,
                style: LabText.label,
              ),
            ),
            SizedBox(width: 12),
            Expanded(child: Text('ASK', style: LabText.label)),
            Expanded(
              child: Text(
                'ASK QTY',
                textAlign: TextAlign.right,
                style: LabText.label,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        for (int i = 0; i < rows; i++)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(
              children: <Widget>[
                Expanded(child: _qty(i, bids, LabColors.green)),
                Expanded(
                  child: _price(i, bids, LabColors.green, TextAlign.right),
                ),
                const SizedBox(width: 12),
                Expanded(child: _price(i, asks, LabColors.red, TextAlign.left)),
                Expanded(child: _qty(i, asks, LabColors.red, TextAlign.right)),
              ],
            ),
          ),
      ],
    );
  }

  Widget _qty(
    int index,
    List<BookLevel> levels,
    Color color, [
    TextAlign align = TextAlign.left,
  ]) {
    final String text = index < levels.length
        ? levels[index].quantity.toStringAsFixed(3)
        : '';
    return Text(
      text,
      textAlign: align,
      style: LabText.number.copyWith(color: color, fontSize: 13),
    );
  }

  Widget _price(
    int index,
    List<BookLevel> levels,
    Color color,
    TextAlign align,
  ) {
    final String text = index < levels.length
        ? formatQuote(levels[index].price)
        : '';
    return Text(
      text,
      textAlign: align,
      style: LabText.number.copyWith(color: color, fontSize: 13),
    );
  }
}
