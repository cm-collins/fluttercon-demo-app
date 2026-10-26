import 'dart:developer' show Timeline;
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import 'book_ladder.dart';
import 'budget_readout.dart';
import 'candle_chart.dart';
import 'depth_chart.dart';
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
  });

  final String rendererLabel;
  final RunBoard board;
  final String? architectureNote;
  final MarketSnapshot? snapshot;

  /// Asset key of the depth shader. The package test uses its own asset path.
  final String shaderAsset;

  /// Fired when a measured draw starts or finishes, so a live price socket can pause.
  final ValueChanged<bool>? onMeasuring;

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
    return ColoredBox(
      color: LabColors.bg,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              _Header(
                rendererLabel: widget.rendererLabel,
                budget: budget,
                pair: snapshot?.quote.pair,
              ),
              const SizedBox(height: 12),
              Expanded(
                child: ListView(
                  children: <Widget>[
                    if (widget.architectureNote != null) ...<Widget>[
                      Text(widget.architectureNote!, style: LabText.label),
                      const SizedBox(height: 12),
                    ],
                    if (snapshot == null)
                      const Text(
                        'Waiting for the Binance book.',
                        style: LabText.body,
                      )
                    else ...<Widget>[
                      _QuoteHeader(quote: snapshot.quote),
                      const SizedBox(height: 12),
                      CandleChart(candles: snapshot.candles),
                      const SizedBox(height: 8),
                      const Text(
                        'Candles and the ladder use solid paints already on screen.',
                        style: LabText.label,
                      ),
                      const SizedBox(height: 16),
                      BookLadder(bids: snapshot.bids, asks: snapshot.asks),
                      const SizedBox(height: 16),
                      RunBoardView(
                        board: widget.board,
                        onClear: widget.board.clear,
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                height: 120,
                child: snapshot == null || _generation == 0 || program == null
                    ? const DecoratedBox(
                        decoration: BoxDecoration(
                          color: LabColors.surface,
                          borderRadius: BorderRadius.all(Radius.circular(12)),
                        ),
                        child: Center(
                          child: Padding(
                            padding: EdgeInsets.all(16),
                            child: Text(
                              'Depth shader has not been drawn.',
                              textAlign: TextAlign.center,
                              style: LabText.body,
                            ),
                          ),
                        ),
                      )
                    : DepthChart(
                        key: ValueKey<int>(_generation),
                        program: program,
                        bids: snapshot.bids,
                        asks: snapshot.asks,
                      ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Draw depth times the first use of one fragment shader. The file is already loaded.',
                style: LabText.label,
              ),
              const SizedBox(height: 12),
              ListenableBuilder(
                listenable: widget.board,
                builder: (BuildContext context, Widget? _) => BudgetReadout(
                  latest: widget.board.latest,
                  measuring: _measuring,
                  budget: budget,
                  recoveryGap: widget.board.recoveryGap,
                ),
              ),
              const SizedBox(height: 12),
              LabButton(
                label: 'DRAW DEPTH',
                primary: _generation == 0,
                onPressed: ready ? _drawDepth : null,
              ),
            ],
          ),
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
  });

  final String rendererLabel;
  final Duration budget;
  final String? pair;

  @override
  Widget build(BuildContext context) {
    final bool skia = rendererLabel.toLowerCase().contains('skia');
    final Color accent = skia ? LabColors.ember : LabColors.violet;
    final double hz = 1000000 / budget.inMicroseconds;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(pair ?? 'Markets', style: LabText.title),
              Text(
                '${hz.round()} Hz · ${formatMs(budget)} ms budget',
                style: LabText.label,
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: LabColors.surfaceElevated,
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: accent, width: 1.5),
          ),
          child: Text(
            rendererLabel,
            style: LabText.body.copyWith(
              color: accent,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }
}

class _QuoteHeader extends StatelessWidget {
  const _QuoteHeader({required this.quote});

  final MarketQuote quote;

  @override
  Widget build(BuildContext context) {
    final bool up = quote.changePercent >= 0;
    final Color tint = up ? LabColors.green : LabColors.red;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: <Widget>[
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                formatQuote(quote.last),
                style: LabText.lapTime.copyWith(fontSize: 36),
              ),
              const SizedBox(height: 4),
              Text(
                'H ${formatQuote(quote.high)}   L ${formatQuote(quote.low)}   Vol ${formatVolume(quote.quoteVolume)}',
                style: LabText.label,
              ),
            ],
          ),
        ),
        Text(
          formatPercent(quote.changePercent),
          style: LabText.number.copyWith(color: tint),
        ),
      ],
    );
  }
}
