import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:kiln/features/markets/binance_gateway.dart';
import 'package:shader_lab/shader_lab.dart';

void main() {
  test('parses a public ticker, klines, and depth book', () {
    final List<MarketQuote> quotes = parseTickers(
      jsonDecode(
        '[{"symbol":"BTCUSDT","lastPrice":"79806.20","priceChangePercent":"-0.783",'
        '"highPrice":"80844.70","lowPrice":"79368.67","quoteVolume":"1823456789.00"}]',
      ),
    );
    expect(quotes.single.pair, 'BTC/USDT');
    expect(quotes.single.last, 79806.20);

    final List<Candle> candles = parseCandles(
      jsonDecode('[[0,"80400","80520","80110","80240","12"]]'),
    );
    expect(candles.single.close, 80240);

    final List<BookLevel> bids = parseLevels(
      jsonDecode('[["79806.19","0.910"]]'),
    );
    expect(bids.single.quantity, 0.91);
  });

  test('keeps USDT pairs and ranks them by quote volume', () {
    final List<MarketQuote> quotes = usdtWatchlist(
      jsonDecode(
        '[{"symbol":"ETHBTC","lastPrice":"0.02","priceChangePercent":"1",'
        '"highPrice":"0.03","lowPrice":"0.01","quoteVolume":"999"},'
        '{"symbol":"ADAUSDT","lastPrice":"0.20","priceChangePercent":"1",'
        '"highPrice":"0.30","lowPrice":"0.10","quoteVolume":"10"},'
        '{"symbol":"BTCUSDT","lastPrice":"80000","priceChangePercent":"1",'
        '"highPrice":"81000","lowPrice":"79000","quoteVolume":"50"}]',
      ),
    );
    expect(quotes.map((MarketQuote quote) => quote.symbol), <String>[
      'BTCUSDT',
      'ADAUSDT',
    ]);
  });
}
