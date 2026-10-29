import 'package:shader_lab/shader_lab.dart';

import '../logic/market_gateway.dart';

/// Deterministic market data for renderer benchmark runs.
class FixtureGateway extends MarketGateway {
  const FixtureGateway();

  @override
  Future<List<MarketQuote>> watchlist() async {
    return <MarketQuote>[
      MarketSnapshot.sample.quote,
      MarketQuote(
        symbol: 'ETHUSDT',
        base: 'ETH',
        quoteAsset: 'USDT',
        last: 4102.18,
        changePercent: 0.42,
        high: 4160,
        low: 4022.14,
        quoteVolume: 824000000,
      ),
      MarketQuote(
        symbol: 'SOLUSDT',
        base: 'SOL',
        quoteAsset: 'USDT',
        last: 182.44,
        changePercent: -1.12,
        high: 188.20,
        low: 178.90,
        quoteVolume: 410000000,
      ),
    ];
  }

  @override
  Future<MarketSnapshot> load(String symbol) async => MarketSnapshot.sample;

  @override
  Stream<double> trades(String symbol) => const Stream<double>.empty();
}
