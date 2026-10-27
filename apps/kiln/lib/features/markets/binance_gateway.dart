import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:shader_lab/shader_lab.dart';

/// Public market data. No API key and no trading endpoints.
abstract class MarketGateway {
  const MarketGateway();

  Future<List<MarketQuote>> watchlist();

  Future<MarketSnapshot> load(String symbol);

  /// Last-trade prices. The dashboard pauses this while a depth draw is measured.
  Stream<double> trades(String symbol);
}

class MarketDataException implements Exception {
  const MarketDataException(this.message);

  final String message;

  @override
  String toString() => message;
}

/// Binance public market-data host. This is not the signed trading API.
class BinanceGateway extends MarketGateway {
  const BinanceGateway({
    this.restHost = 'https://data-api.binance.vision',
    this.streamHost = 'wss://data-stream.binance.vision/ws',
  });

  final String restHost;
  final String streamHost;

  @override
  Future<List<MarketQuote>> watchlist() async {
    final Object? decoded = await _get('/api/v3/ticker/24hr');
    return usdtWatchlist(decoded);
  }

  @override
  Future<MarketSnapshot> load(String symbol) async {
    final List<Object?> parts = await Future.wait<Object?>(<Future<Object?>>[
      _get('/api/v3/ticker/24hr?symbol=$symbol'),
      _get('/api/v3/klines?symbol=$symbol&interval=1m&limit=60'),
      _get('/api/v3/depth?symbol=$symbol&limit=20'),
    ]);
    final Map<String, dynamic> depth = parts[2]! as Map<String, dynamic>;
    return MarketSnapshot(
      quote: quoteFromTicker(parts[0]! as Map<String, dynamic>),
      candles: parseCandles(parts[1]),
      bids: parseLevels(depth['bids']),
      asks: parseLevels(depth['asks']),
    );
  }

  @override
  Stream<double> trades(String symbol) {
    final StreamController<double> controller = StreamController<double>();
    WebSocket? socket;
    controller.onListen = () async {
      try {
        socket = await WebSocket.connect(
          '$streamHost/${symbol.toLowerCase()}@trade',
        );
        socket!.listen(
          (Object? event) {
            if (controller.isClosed) {
              return;
            }
            final Object? decoded = jsonDecode(event.toString());
            if (decoded is Map<String, dynamic>) {
              final double? price = double.tryParse('${decoded['p']}');
              if (price != null) {
                controller.add(price);
              }
            }
          },
          onError: (Object error, StackTrace stack) {
            if (!controller.isClosed) {
              controller.addError(error, stack);
            }
          },
          onDone: () {
            if (!controller.isClosed) {
              controller.close();
            }
          },
        );
      } on Object catch (error, stack) {
        if (!controller.isClosed) {
          controller.addError(error, stack);
        }
      }
    };
    controller.onCancel = () {
      socket?.close();
    };
    return controller.stream;
  }

  Future<Object?> _get(String pathAndQuery) async {
    final HttpClient client = HttpClient();
    try {
      final HttpClientRequest request = await client.getUrl(
        Uri.parse('$restHost$pathAndQuery'),
      );
      request.headers.set(HttpHeaders.userAgentHeader, 'kiln-demo');
      final HttpClientResponse response = await request.close();
      final String body = await utf8.decoder.bind(response).join();
      if (response.statusCode != 200) {
        throw MarketDataException('Binance returned ${response.statusCode}.');
      }
      return jsonDecode(body);
    } on MarketDataException {
      rethrow;
    } on Object catch (error) {
      throw MarketDataException('Could not reach Binance ($error).');
    } finally {
      client.close();
    }
  }
}

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
