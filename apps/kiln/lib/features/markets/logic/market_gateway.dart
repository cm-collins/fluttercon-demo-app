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
