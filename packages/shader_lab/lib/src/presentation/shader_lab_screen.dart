import 'dart:developer' show Timeline;

import 'package:flutter/widgets.dart';

import '../logic/depth_session.dart';
import '../logic/frame_timer.dart';
import '../logic/market.dart';
import '../logic/paint_ledger.dart';
import '../logic/renderer_evidence.dart';
import '../logic/run_board.dart';
import '../widgets/book_ladder.dart';
import '../widgets/budget_readout.dart';
import '../widgets/candle_chart.dart';
import '../widgets/depth_chart.dart';
import '../widgets/lab_button.dart';
import '../widgets/lab_chip.dart';
import '../widgets/lab_chrome.dart';
import '../widgets/lab_header.dart';
import '../widgets/layer_frame.dart';
import '../widgets/lab_tokens.dart';
import '../widgets/run_board_view.dart';
import '../widgets/renderer_evidence_card.dart';
import '../widgets/shader_jank_panel.dart';

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
    this.evidence = const RendererEvidence(
      engine: 'Unspecified',
      backend: null,
      backendVerified: false,
    ),
    this.snapshot,
    this.shaderAsset = 'packages/shader_lab/shaders/depth_fill.frag',
    this.jankShaderAsset = 'packages/shader_lab/shaders/speed_ramp.frag',
    this.onMeasuring,
    this.onBack,
  });

  final String rendererLabel;
  final RunBoard board;
  final String? architectureNote;
  final RendererEvidence evidence;
  final MarketSnapshot? snapshot;

  /// Asset key of the depth shader. The package test uses its own asset path.
  final String shaderAsset;
  final String jankShaderAsset;

  /// Fired when a measured draw starts or finishes, so a live price socket can pause.
  final ValueChanged<bool>? onMeasuring;

  /// Returns to the watchlist. Omitted when this screen is the root of a test.
  final VoidCallback? onBack;

  @override
  State<ShaderLabScreen> createState() => _ShaderLabScreenState();
}

class _ShaderLabScreenState extends State<ShaderLabScreen> {
  late final DepthSession _session;
  final PaintLedger _ledger = PaintLedger();
  LayerMode _layers = LayerMode.isolated;

  @override
  void initState() {
    super.initState();
    _session = DepthSession(
      shaderAsset: widget.shaderAsset,
      board: widget.board,
      rendererLabel: widget.rendererLabel,
      onMeasuring: widget.onMeasuring,
    );
    _session.enter();
  }

  @override
  void dispose() {
    _session.dispose();
    _ledger.dispose();
    super.dispose();
  }

  Duration get _budget => budgetFor(View.of(context).display.refreshRate);

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _session,
      builder: (BuildContext context, Widget? _) => _build(context),
    );
  }

  Widget _build(BuildContext context) {
    final MarketSnapshot? snapshot = widget.snapshot;
    final program = _session.program;
    final Duration budget = _budget;
    final bool ready = snapshot != null && program != null;
    final bool showDepth =
        snapshot != null && program != null && _session.generation > 0;
    return ColoredBox(
      color: LabColors.bg,
      child: SafeArea(
        child: Column(
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: LabHeader(
                title: snapshot?.quote.pair ?? 'Markets',
                rendererLabel: widget.rendererLabel,
                budget: budget,
                backLabel: 'Markets',
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
                    RendererEvidenceCard(
                      evidence: widget.evidence,
                      rendererLabel: widget.rendererLabel,
                      budget: budget,
                    ),
                    const SizedBox(height: 16),
                    _QuoteHeader(quote: snapshot.quote),
                    const SizedBox(height: 16),
                    _StatRow(quote: snapshot.quote),
                    const SizedBox(height: 20),
                    const LabSectionTitle('1 minute'),
                    _LayerSwitch(
                      mode: _layers,
                      onChanged: (LayerMode mode) {
                        setState(() => _layers = mode);
                      },
                    ),
                    const SizedBox(height: 8),
                    LayerFrame(
                      mode: _layers,
                      child: LabCard(
                        padding: const EdgeInsets.fromLTRB(8, 12, 8, 8),
                        child: CandleChart(
                          candles: snapshot.candles,
                          mode: _layers,
                          ledger: _ledger,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    ListenableBuilder(
                      listenable: _ledger,
                      builder: (BuildContext context, Widget? _) => Text(
                        'Candle paints ${_ledger.candlePaints}',
                        style: LabText.label,
                      ),
                    ),
                    const SizedBox(height: 20),
                    const LabSectionTitle('Depth'),
                    LabCard(
                      padding: const EdgeInsets.all(12),
                      child: SizedBox(
                        height: 148,
                        child: showDepth
                            ? DepthChart(
                                key: ValueKey<int>(_session.generation),
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
                            measuring: _session.measuring,
                            budget: budget,
                            recoveryGap: widget.board.recoveryGap,
                          ),
                    ),
                    const SizedBox(height: 12),
                    RunBoardView(
                      board: widget.board,
                      onClear: widget.board.clear,
                    ),
                    const SizedBox(height: 20),
                    const LabSectionTitle('Shader first use'),
                    ShaderJankPanel(
                      shaderAsset: widget.jankShaderAsset,
                      budget: budget,
                      onMeasuring: widget.onMeasuring,
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
                primary: true,
                onPressed: ready ? () => _session.draw(_budget) : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuoteHeader extends StatelessWidget {
  const _QuoteHeader({required this.quote});

  final MarketQuote quote;

  @override
  Widget build(BuildContext context) {
    return Timeline.timeSync('KILN::Markets::quote', () {
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
    });
  }
}

class _LayerSwitch extends StatelessWidget {
  const _LayerSwitch({required this.mode, required this.onChanged});

  final LayerMode mode;
  final ValueChanged<LayerMode> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        LabChip(
          label: 'Coupled',
          selected: mode == LayerMode.coupled,
          onTap: () => onChanged(LayerMode.coupled),
        ),
        const SizedBox(width: 8),
        LabChip(
          label: 'Isolated',
          selected: mode == LayerMode.isolated,
          onTap: () => onChanged(LayerMode.isolated),
        ),
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
