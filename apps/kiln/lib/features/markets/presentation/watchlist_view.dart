import 'package:flutter/widgets.dart';
import 'package:shader_lab/shader_lab.dart';

/// The price list. It does not fetch, and it does not know which flavor is running
/// except for the label it is given.
class WatchlistView extends StatelessWidget {
  const WatchlistView({
    super.key,
    required this.rendererLabel,
    required this.quotes,
    required this.loading,
    required this.error,
    required this.onRetry,
    required this.onOpen,
  });

  final String rendererLabel;
  final List<MarketQuote>? quotes;
  final bool loading;
  final String? error;
  final VoidCallback onRetry;
  final ValueChanged<MarketQuote> onOpen;

  @override
  Widget build(BuildContext context) {
    final Duration budget = budgetFor(View.of(context).display.refreshRate);
    final List<MarketQuote>? rows = quotes;
    return ColoredBox(
      color: LabColors.bg,
      child: SafeArea(
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
                  LabBadge(label: rendererLabel),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                '${View.of(context).display.refreshRate.round()} Hz · ${formatMs(budget)} ms budget',
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
              ] else if (rows == null || loading)
                const Text('Loading the Binance book…', style: LabText.body)
              else
                Expanded(
                  child: _QuoteList(quotes: rows, onOpen: onOpen),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuoteList extends StatelessWidget {
  const _QuoteList({required this.quotes, required this.onOpen});

  final List<MarketQuote> quotes;
  final ValueChanged<MarketQuote> onOpen;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: LabColors.hairline),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(15),
        child: ColoredBox(
          color: LabColors.surface,
          child: ListView.separated(
            itemCount: quotes.length,
            separatorBuilder: (BuildContext context, int index) =>
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: ColoredBox(
                    color: LabColors.hairline,
                    child: SizedBox(height: 1, width: double.infinity),
                  ),
                ),
            itemBuilder: (BuildContext context, int index) {
              final MarketQuote quote = quotes[index];
              return GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () => onOpen(quote),
                child: Padding(
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
                            const SizedBox(height: 2),
                            Text(
                              'Vol ${formatVolume(quote.quoteVolume)}',
                              style: LabText.label,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: <Widget>[
                          Text(formatQuote(quote.last), style: LabText.number),
                          const SizedBox(height: 4),
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
      ),
    );
  }
}
