import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:shader_lab/shader_lab.dart';

import '../../app/kiln_app.dart';
import '../../app/kiln_runtime.dart';
import 'binance_gateway.dart';

/// Lives for the whole process so measured runs survive leaving the book.
final RunBoard marketRuns = RunBoard();

/// Watchlist, then one instrument. The instrument times the depth shader.
class MarketsRoute extends StatefulWidget {
  const MarketsRoute({super.key});

  @override
  State<MarketsRoute> createState() => _MarketsRouteState();
}

class _MarketsRouteState extends State<MarketsRoute> {
  List<MarketQuote>? _quotes;
  MarketSnapshot? _snapshot;
  String? _selected;
  String? _error;
  double? _liveLast;
  bool _measuring = false;
  bool _loading = false;
  MarketGateway? _gateway;
  StreamSubscription<double>? _trades;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final MarketGateway gateway = KilnScope.gatewayOf(context);
    if (_gateway != gateway) {
      _gateway = gateway;
      _loadWatchlist();
    }
  }

  @override
  void dispose() {
    _trades?.cancel();
    super.dispose();
  }

  Future<void> _loadWatchlist() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final List<MarketQuote> quotes = await _gateway!.watchlist();
      if (!mounted) {
        return;
      }
      setState(() {
        _quotes = quotes;
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _loading = false;
        _error = '$error';
      });
    }
  }

  Future<void> _open(MarketQuote quote) async {
    await _trades?.cancel();
    _trades = null;
    setState(() {
      _selected = quote.symbol;
      _snapshot = null;
      _liveLast = null;
      _error = null;
      _loading = true;
    });
    try {
      final MarketSnapshot snapshot = await _gateway!.load(quote.symbol);
      if (!mounted || _selected != quote.symbol) {
        return;
      }
      setState(() {
        _snapshot = snapshot;
        _loading = false;
      });
      _trades = _gateway!.trades(quote.symbol).listen((double price) {
        if (_measuring) {
          _liveLast = price;
          return;
        }
        if (mounted) {
          setState(() => _liveLast = price);
        }
      });
    } on Object catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _loading = false;
        _error = '$error';
      });
    }
  }

  void _back() {
    _trades?.cancel();
    _trades = null;
    setState(() {
      _selected = null;
      _snapshot = null;
      _liveLast = null;
      _error = null;
    });
  }

  void _onMeasuring(bool measuring) {
    _measuring = measuring;
    if (!measuring && _liveLast != null && _snapshot != null && mounted) {
      setState(() {});
    }
  }

  @override
  Widget build(BuildContext context) {
    final KilnRuntime runtime = KilnScope.of(context);
    if (_selected == null) {
      return ColoredBox(
        color: LabColors.bg,
        child: _Watchlist(
          quotes: _quotes,
          loading: _loading,
          error: _error,
          onRetry: _loadWatchlist,
          onOpen: _open,
        ),
      );
    }
    final MarketSnapshot? snapshot = _snapshot;
    final MarketSnapshot? shown = snapshot == null || _liveLast == null
        ? snapshot
        : MarketSnapshot(
            quote: snapshot.quote.withLast(_liveLast!),
            candles: snapshot.candles,
            bids: snapshot.bids,
            asks: snapshot.asks,
          );
    if (_error != null) {
      return ColoredBox(
        color: LabColors.bg,
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: _back,
                  child: const Padding(
                    padding: EdgeInsets.only(bottom: 16),
                    child: Text('Markets', style: LabText.label),
                  ),
                ),
                Text(_error!, style: LabText.body),
              ],
            ),
          ),
        ),
      );
    }
    return ShaderLabScreen(
      rendererLabel: runtime.label,
      architectureNote: runtime.architectureNote,
      board: marketRuns,
      snapshot: _loading ? null : shown,
      onMeasuring: _onMeasuring,
      onBack: _back,
    );
  }
}

class _Watchlist extends StatelessWidget {
  const _Watchlist({
    required this.quotes,
    required this.loading,
    required this.error,
    required this.onRetry,
    required this.onOpen,
  });

  final List<MarketQuote>? quotes;
  final bool loading;
  final String? error;
  final VoidCallback onRetry;
  final ValueChanged<MarketQuote> onOpen;

  @override
  Widget build(BuildContext context) {
    final KilnRuntime runtime = KilnScope.of(context);
    final Duration budget = budgetFor(View.of(context).display.refreshRate);
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Expanded(child: Text('Markets', style: LabText.title)),
                const SizedBox(width: 12),
                LabBadge(label: runtime.label),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '${View.of(context).display.refreshRate.round()} Hz · ${formatMs(budget)} ms budget',
              style: LabText.label,
            ),
            const SizedBox(height: 4),
            const Text(
              'Public Binance prices. Open a book, then draw depth.',
              style: LabText.label,
            ),
            const SizedBox(height: 16),
            if (error != null) ...<Widget>[
              Text(error!, style: LabText.body),
              const SizedBox(height: 12),
              GestureDetector(
                onTap: onRetry,
                child: const Text('RETRY', style: LabText.body),
              ),
            ] else if (quotes == null || loading)
              const Text('Loading the Binance book…', style: LabText.body)
            else
              Expanded(
                child: ListView.separated(
                  itemCount: quotes!.length,
                  separatorBuilder: (BuildContext context, int index) =>
                      const SizedBox(height: 8),
                  itemBuilder: (BuildContext context, int index) {
                    final MarketQuote quote = quotes![index];
                    return GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onTap: () => onOpen(quote),
                      child: LabCard(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 14,
                        ),
                        child: Row(
                          children: <Widget>[
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text(
                                    quote.pair,
                                    style: LabText.body.copyWith(
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Vol ${formatVolume(quote.quoteVolume)}',
                                    style: LabText.label,
                                  ),
                                ],
                              ),
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: <Widget>[
                                Text(
                                  formatQuote(quote.last),
                                  style: LabText.number,
                                ),
                                const SizedBox(height: 6),
                                LabPercent(changePercent: quote.changePercent),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}
