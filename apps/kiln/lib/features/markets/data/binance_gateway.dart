import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:shader_lab/shader_lab.dart';

import '../logic/market_gateway.dart';
import '../logic/market_parse.dart';

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
