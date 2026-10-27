import 'dart:developer' show Timeline;
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import 'book_ladder.dart';
import 'budget_readout.dart';
import 'candle_chart.dart';
import 'depth_chart.dart';
import 'lab_chrome.dart';
import 'frame_timer.dart';
import 'frame_window.dart';
import 'lab_button.dart';
import 'lab_tokens.dart';
import 'market.dart';
import 'run_board.dart';
import 'run_board_view.dart';

/// Market dashboard used to time the first draw of one fragment shader.
///
/// Candles and the ladder are ordinary solid paints. They are on screen before
/// the tap. [snapshot] comes from the public Binance book. The depth fill is
/// loaded before the tap so file I/O is outside the clock; the clock starts
/// when that shader is drawn.
class ShaderLabScreen extends StatefulWidget {
  const ShaderLabScreen({
    super.key,
    required this.rendererLabel,
    required this.board,
    this.architectureNote,
    this.snapshot,
    this.shaderAsset = 'packages/shader_lab/shaders/depth_fill.frag',
    this.onMeasuring,
    this.onBack,
  });

  final String rendererLabel;
  final RunBoard board;
  final String? architectureNote;
  final MarketSnapshot? snapshot;

  /// Asset key of the depth shader. The package test uses its own asset path.
  final String shaderAsset;

  /// Fired when a measured draw starts or finishes, so a live price socket can pause.
  final ValueChanged<bool>? onMeasuring;

  /// Returns to the watchlist. Omitted when this screen is the root of a test.
  final VoidCallback? onBack;

  @override
  State<ShaderLabScreen> createState() => _ShaderLabScreenState();
}

class _ShaderLabScreenState extends State<ShaderLabScreen> {
  final FrameTimer _timer = FrameTimer();
  ui.FragmentProgram? _program;
  int _generation = 0;
  bool _measuring = false;

  @override
  void initState() {
    super.initState();
    Timeline.instantSync('KILN::Markets::enter');
    ui.FragmentProgram.fromAsset(widget.shaderAsset)
        .then((ui.FragmentProgram program) {
          if (mounted) {
            setState(() => _program = program);
          }
        });
  }

  @override
  void dispose() {
    _timer.dispose();
    super.dispose();
  }

  Duration get _budget => budgetFor(View.of(context).display.refreshRate);

  void _drawDepth() {
    Timeline.instantSync(
      'KILN::Markets::drawDepth',
      arguments: <String, String>{'renderer': widget.rendererLabel},
    );
    _timer.arm(budget: _budget, onResult: _onResult);
    widget.onMeasuring?.call(true);
    setState(() {
      _generation += 1;
      _measuring = true;
    });
  }

  void _onResult(FrameWindowResult result) {
    final LabRun run = widget.board.add(result);
    Timeline.instantSync(
      'KILN::Markets::smooth',
      arguments: <String, String>{
        'renderer': widget.rendererLabel,
        'run': '${run.number}',
        'timeToSmoothMs': formatMs(result.timeToSmooth),
        'stallMs': formatMs(result.stall),
        'worstMs': formatMs(result.worst),
      },
    );
    if (mounted) {
      setState(() => _measuring = false);
    }
    widget.onMeasuring?.call(false);
  }

  @override
  Widget build(BuildContext context) {
    final MarketSnapshot? snapshot = widget.snapshot;
    final ui.FragmentProgram? program = _program;
    final Duration budget = _budget;
    final bool ready = snapshot != null && program != null;
    final bool showDepth =
        snapshot != null && program != null && _generation > 0;
    return ColoredBox(
      color: LabColors.bg,
      child: SafeArea(
        child: Column(
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: _Header(
                rendererLabel: widget.rendererLabel,
                budget: budget,
                pair: snapshot?.quote.pair,
                onBack: widget.onBack,
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                children: <Widget>[
                  if (snapshot == null)
                    const LabCard(
                      child: Text(
                        'Waiting for the Binance book.',
                        style: LabText.body,
                      ),
                    )
                  else ...<Widget>[
                    _QuoteHeader(quote: snapshot.quote),
                    const SizedBox(height: 16),
                    _StatRow(quote: snapshot.quote),
                    const SizedBox(height: 20),
                    const LabSectionTitle('1 minute'),
                    LabCard(
                      padding: const EdgeInsets.fromLTRB(8, 12, 8, 8),
                      child: CandleChart(candles: snapshot.candles),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Candles and the ladder use solid paints already on screen.',
                      style: LabText.label,
                    ),
                    const SizedBox(height: 20),
                    const LabSectionTitle('Depth'),
                    LabCard(
                      padding: const EdgeInsets.all(12),
                      child: SizedBox(
                        height: 148,
                        child: showDepth
                            ? DepthChart(
                                key: ValueKey<int>(_generation),
                                program: program,
                                bids: snapshot.bids,
                                asks: snapshot.asks,
                              )
                            : const Center(
                                child: Text(
                                  'Depth shader has not been drawn.',
                                  textAlign: TextAlign.center,
                                  style: LabText.body,
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Draw depth times the first use of one fragment shader. The file is already loaded.',
                      style: LabText.label,
                    ),
                    const SizedBox(height: 20),
                    const LabSectionTitle('Book'),
                    LabCard(
                      child: BookLadder(
                        bids: snapshot.bids,
                        asks: snapshot.asks,
                      ),
                    ),
                    const SizedBox(height: 20),
                    const LabSectionTitle('Timing'),
                    ListenableBuilder(
                      listenable: widget.board,
                      builder: (BuildContext context, Widget? _) =>
                          BudgetReadout(
                            latest: widget.board.latest,
                            measuring: _measuring,
                            budget: budget,
                            recoveryGap: widget.board.recoveryGap,
                          ),
                    ),
                    const SizedBox(height: 12),
                    RunBoardView(
                      board: widget.board,
                      onClear: widget.board.clear,
                    ),
                    if (widget.architectureNote != null) ...<Widget>[
                      const SizedBox(height: 16),
                      Text(widget.architectureNote!, style: LabText.label),
                    ],
                  ],
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: LabButton(
                label: 'DRAW DEPTH',
                primary: _generation == 0,
                onPressed: ready ? _drawDepth : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({
    required this.rendererLabel,
    required this.budget,
    required this.pair,
    required this.onBack,
  });

  final String rendererLabel;
  final Duration budget;
  final String? pair;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    final double hz = 1000000 / budget.inMicroseconds;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: <Widget>[
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              if (onBack != null)
                GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: onBack,
                  child: const Padding(
                    padding: EdgeInsets.only(bottom: 4),
                    child: Text('Markets', style: LabText.label),
                  ),
                ),
              Text(pair ?? 'Markets', style: LabText.title),
              Text(
                '${hz.round()} Hz · ${formatMs(budget)} ms budget',
                style: LabText.label,
              ),
            ],
          ),
        ),
        const SizedBox(width: 12),
        LabBadge(label: rendererLabel),
      ],
    );
  }
}

class _QuoteHeader extends StatelessWidget {
  const _QuoteHeader({required this.quote});

  final MarketQuote quote;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: <Widget>[
        Expanded(
          child: Text(
            formatQuote(quote.last),
            style: LabText.lapTime.copyWith(
              fontSize: 36,
              color: LabColors.textPrimary,
            ),
          ),
        ),
        LabPercent(changePercent: quote.changePercent),
      ],
    );
  }
}

class _StatRow extends StatelessWidget {
  const _StatRow({required this.quote});

  final MarketQuote quote;

  @override
  Widget build(BuildContext context) {
    return LabCard(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      child: Row(
        children: <Widget>[
          _Stat(label: 'High', value: formatQuote(quote.high)),
          _Stat(label: 'Low', value: formatQuote(quote.low)),
          _Stat(label: 'Volume', value: formatVolume(quote.quoteVolume)),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(label, style: LabText.label),
          const SizedBox(height: 4),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: LabText.number.copyWith(fontSize: 16),
          ),
        ],
      ),
    );
  }
}
