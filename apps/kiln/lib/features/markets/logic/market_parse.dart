import 'package:shader_lab/shader_lab.dart';

/// Spot USDT markets from a full 24-hour ticker payload, busiest first.
List<MarketQuote> usdtWatchlist(Object? decoded) {
  final List<MarketQuote> quotes = <MarketQuote>[
    for (final MarketQuote quote in parseTickers(decoded))
      if (_isUsdtPair(quote.symbol)) quote,
  ];
  quotes.sort(
    (MarketQuote a, MarketQuote b) => b.quoteVolume.compareTo(a.quoteVolume),
  );
  return quotes;
}

bool _isUsdtPair(String symbol) {
  return symbol.endsWith('USDT') && symbol.length > 4;
}

List<MarketQuote> parseTickers(Object? decoded) {
  final List<dynamic> rows = decoded! as List<dynamic>;
  return <MarketQuote>[
    for (final dynamic row in rows)
      quoteFromTicker(row as Map<String, dynamic>),
  ];
}

MarketQuote quoteFromTicker(Map<String, dynamic> json) {
  final String symbol = json['symbol']! as String;
  return MarketQuote(
    symbol: symbol,
    base: _baseOf(symbol),
    quoteAsset: 'USDT',
    last: double.parse(json['lastPrice']! as String),
    changePercent: double.parse(json['priceChangePercent']! as String),
    high: double.parse(json['highPrice']! as String),
    low: double.parse(json['lowPrice']! as String),
    quoteVolume: double.parse(json['quoteVolume']! as String),
  );
}

List<Candle> parseCandles(Object? decoded) {
  final List<dynamic> rows = decoded! as List<dynamic>;
  return <Candle>[
    for (final dynamic row in rows)
      Candle(
        open: double.parse((row as List<dynamic>)[1] as String),
        high: double.parse(row[2] as String),
        low: double.parse(row[3] as String),
        close: double.parse(row[4] as String),
      ),
  ];
}

List<BookLevel> parseLevels(Object? decoded) {
  final List<dynamic> rows = decoded! as List<dynamic>;
  return <BookLevel>[
    for (final dynamic row in rows)
      BookLevel(
        double.parse((row as List<dynamic>)[0] as String),
        double.parse(row[1] as String),
      ),
  ];
}

String _baseOf(String symbol) {
  const String quote = 'USDT';
  if (symbol.endsWith(quote) && symbol.length > quote.length) {
    return symbol.substring(0, symbol.length - quote.length);
  }
  return symbol;
}
