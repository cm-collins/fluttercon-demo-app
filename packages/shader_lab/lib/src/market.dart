/// One public-book price level. Quantity is base-asset size.
class BookLevel {
  const BookLevel(this.price, this.quantity);

  final double price;
  final double quantity;
}

/// One OHLC bucket from the public kline endpoint.
class Candle {
  const Candle({
    required this.open,
    required this.high,
    required this.low,
    required this.close,
  });

  final double open;
  final double high;
  final double low;
  final double close;

  bool get up => close >= open;
}

/// A 24-hour ticker for one symbol.
class MarketQuote {
  const MarketQuote({
    required this.symbol,
    required this.base,
    required this.quoteAsset,
    required this.last,
    required this.changePercent,
    required this.high,
    required this.low,
    required this.quoteVolume,
  });

  final String symbol;
  final String base;
  final String quoteAsset;
  final double last;
  final double changePercent;
  final double high;
  final double low;
  final double quoteVolume;

  String get pair => '$base/$quoteAsset';

  MarketQuote withLast(double last) {
    return MarketQuote(
      symbol: symbol,
      base: base,
      quoteAsset: quoteAsset,
      last: last,
      changePercent: changePercent,
      high: high,
      low: low,
      quoteVolume: quoteVolume,
    );
  }
}

/// The book and candles already on screen before the depth shader is drawn.
class MarketSnapshot {
  const MarketSnapshot({
    required this.quote,
    required this.candles,
    required this.bids,
    required this.asks,
  });

  final MarketQuote quote;
  final List<Candle> candles;
  final List<BookLevel> bids;
  final List<BookLevel> asks;

  /// Offline book used by widget tests. The shape matches a small Binance snapshot.
  static const MarketSnapshot sample = MarketSnapshot(
    quote: MarketQuote(
      symbol: 'BTCUSDT',
      base: 'BTC',
      quoteAsset: 'USDT',
      last: 79806.2,
      changePercent: -0.783,
      high: 80844.7,
      low: 79368.67,
      quoteVolume: 1823456789,
    ),
    candles: <Candle>[
      Candle(open: 80400, high: 80520, low: 80110, close: 80240),
      Candle(open: 80240, high: 80380, low: 80090, close: 80310),
      Candle(open: 80310, high: 80440, low: 80150, close: 80180),
      Candle(open: 80180, high: 80260, low: 79940, close: 80010),
      Candle(open: 80010, high: 80120, low: 79780, close: 79840),
      Candle(open: 79840, high: 79990, low: 79660, close: 79920),
      Candle(open: 79920, high: 80040, low: 79710, close: 79806),
    ],
    bids: <BookLevel>[
      BookLevel(79806.19, 0.91),
      BookLevel(79806.01, 0.42),
      BookLevel(79800.00, 1.20),
      BookLevel(79790.50, 2.40),
    ],
    asks: <BookLevel>[
      BookLevel(79806.20, 1.10),
      BookLevel(79806.82, 0.35),
      BookLevel(79812.00, 1.80),
      BookLevel(79820.40, 3.10),
    ],
  );
}

String formatQuote(double value) {
  final int digits = value >= 100 ? 2 : 4;
  final String raw = value.toStringAsFixed(digits);
  final List<String> parts = raw.split('.');
  final String whole = parts.first;
  final StringBuffer buffer = StringBuffer();
  for (int i = 0; i < whole.length; i++) {
    final int fromEnd = whole.length - i;
    if (i > 0 && fromEnd % 3 == 0) {
      buffer.write(',');
    }
    buffer.write(whole[i]);
  }
  if (parts.length > 1) {
    buffer
      ..write('.')
      ..write(parts[1]);
  }
  return buffer.toString();
}

String formatPercent(double value) {
  final String sign = value > 0 ? '+' : '';
  return '$sign${value.toStringAsFixed(2)}%';
}

String formatVolume(double quoteVolume) {
  if (quoteVolume >= 1000000000) {
    return '${(quoteVolume / 1000000000).toStringAsFixed(2)}B';
  }
  if (quoteVolume >= 1000000) {
    return '${(quoteVolume / 1000000).toStringAsFixed(1)}M';
  }
  if (quoteVolume >= 1000) {
    return '${(quoteVolume / 1000).toStringAsFixed(1)}K';
  }
  return quoteVolume.toStringAsFixed(0);
}
