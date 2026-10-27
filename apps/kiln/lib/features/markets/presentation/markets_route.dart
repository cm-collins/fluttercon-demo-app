import 'package:flutter/widgets.dart';
import 'package:shader_lab/shader_lab.dart';

import '../../../app/kiln_runtime.dart';
import '../logic/market_gateway.dart';
import '../logic/markets_session.dart';
import 'watchlist_view.dart';

/// Binds a [MarketsSession] to the watchlist and the instrument.
class MarketsRoute extends StatefulWidget {
  const MarketsRoute({super.key, required this.runtime, required this.gateway});

  final KilnRuntime runtime;
  final MarketGateway gateway;

  @override
  State<MarketsRoute> createState() => _MarketsRouteState();
}

class _MarketsRouteState extends State<MarketsRoute> {
  late MarketsSession _session = MarketsSession(widget.gateway);

  @override
  void initState() {
    super.initState();
    _session.loadWatchlist();
  }

  @override
  void didUpdateWidget(MarketsRoute oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.gateway != widget.gateway) {
      _session.dispose();
      _session = MarketsSession(widget.gateway)..loadWatchlist();
    }
  }

  @override
  void dispose() {
    _session.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _session,
      builder: (BuildContext context, Widget? _) {
        final MarketsSession session = _session;
        if (session.selected == null) {
          return WatchlistView(
            rendererLabel: widget.runtime.label,
            quotes: session.quotes,
            loading: session.loading,
            error: session.error,
            onRetry: () {
              session.loadWatchlist();
            },
            onOpen: (MarketQuote quote) {
              session.open(quote);
            },
          );
        }
        if (session.error != null) {
          return _LoadError(message: session.error!, onBack: session.back);
        }
        return ShaderLabScreen(
          rendererLabel: widget.runtime.label,
          architectureNote: widget.runtime.architectureNote,
          board: marketRuns,
          snapshot: session.loading ? null : session.shown,
          onMeasuring: session.setMeasuring,
          onBack: session.back,
        );
      },
    );
  }
}

class _LoadError extends StatelessWidget {
  const _LoadError({required this.message, required this.onBack});

  final String message;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
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
                onTap: onBack,
                child: const Padding(
                  padding: EdgeInsets.only(bottom: 16),
                  child: Text('Markets', style: LabText.label),
                ),
              ),
              Text(message, style: LabText.body),
            ],
          ),
        ),
      ),
    );
  }
}
