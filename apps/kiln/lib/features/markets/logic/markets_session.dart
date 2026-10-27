import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:shader_lab/shader_lab.dart';

import 'market_gateway.dart';

/// Process-wide runs. Leaving the book does not clear a measured first draw.
final RunBoard marketRuns = RunBoard();

/// Watchlist, open book, and the live price. The screen only listens.
class MarketsSession extends ChangeNotifier {
  MarketsSession(this.gateway);

  final MarketGateway gateway;

  List<MarketQuote>? quotes;
  MarketSnapshot? snapshot;
  String? selected;
  String? error;
  double? liveLast;
  bool measuring = false;
  bool loading = false;
  bool _disposed = false;
  StreamSubscription<double>? _trades;

  /// The book on screen. A trade that arrived during a measurement is applied
  /// only after the window closes.
  MarketSnapshot? get shown {
    final MarketSnapshot? current = snapshot;
    final double? last = liveLast;
    if (current == null || last == null) {
      return current;
    }
    return MarketSnapshot(
      quote: current.quote.withLast(last),
      candles: current.candles,
      bids: current.bids,
      asks: current.asks,
    );
  }

  Future<void> loadWatchlist() async {
    loading = true;
    error = null;
    _notify();
    try {
      final List<MarketQuote> next = await gateway.watchlist();
      quotes = next;
      loading = false;
    } on Object catch (error) {
      loading = false;
      this.error = '$error';
    }
    _notify();
  }

  Future<void> open(MarketQuote quote) async {
    await _trades?.cancel();
    _trades = null;
    selected = quote.symbol;
    snapshot = null;
    liveLast = null;
    error = null;
    loading = true;
    _notify();
    try {
      final MarketSnapshot next = await gateway.load(quote.symbol);
      if (_disposed || selected != quote.symbol) {
        return;
      }
      snapshot = next;
      loading = false;
      _notify();
      _trades = gateway.trades(quote.symbol).listen((double price) {
        if (measuring) {
          liveLast = price;
          return;
        }
        liveLast = price;
        _notify();
      });
    } on Object catch (error) {
      if (_disposed) {
        return;
      }
      loading = false;
      this.error = '$error';
      _notify();
    }
  }

  void back() {
    _trades?.cancel();
    _trades = null;
    selected = null;
    snapshot = null;
    liveLast = null;
    error = null;
    _notify();
  }

  /// The instrument calls this around the measured tap. A true value does not
  /// rebuild, so the watchlist price cannot dirty the frame window.
  void setMeasuring(bool value) {
    measuring = value;
    if (!value && liveLast != null && snapshot != null) {
      _notify();
    }
  }

  void _notify() {
    if (!_disposed) {
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _trades?.cancel();
    super.dispose();
  }
}
