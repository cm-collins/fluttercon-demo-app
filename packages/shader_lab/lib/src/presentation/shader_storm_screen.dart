import 'package:flutter/widgets.dart';

import '../logic/durations.dart';
import '../logic/frame_history.dart';
import '../logic/frame_timer.dart';
import '../logic/frame_window.dart';
import '../logic/storm_session.dart';
import '../widgets/frame_strip.dart';
import '../widgets/heartbeat_lane.dart';
import '../widgets/lab_button.dart';
import '../widgets/lab_chrome.dart';
import '../widgets/lab_tokens.dart';
import '../widgets/storm_grid.dart';

/// Shows where a renderer pays for shaders: during frames (Skia, JIT) or
/// before the app runs (Impeller, AOT).
///
/// REVEAL draws every storm tile in one frame. Each tile is a new combination
/// of built-in effects. A moving heartbeat and live per-thread frame bars make
/// any first-use stall visible, and the first and repeat reveals are compared
/// side by side.
class ShaderStormScreen extends StatefulWidget {
  const ShaderStormScreen({
    super.key,
    required this.rendererLabel,
    this.engineNote,
    this.record,
    this.tileCount = 48,
    this.onBack,
  });

  final String rendererLabel;

  /// One sentence on how this engine gets its shaders.
  final String? engineNote;

  /// Defaults to [processStormRecord], which lives as long as the shader cache.
  final StormRecord? record;
  final int tileCount;
  final VoidCallback? onBack;

  @override
  State<ShaderStormScreen> createState() => _ShaderStormScreenState();
}

class _ShaderStormScreenState extends State<ShaderStormScreen> {
  late final StormRecord _record = widget.record ?? processStormRecord;
  late final StormSession _session = StormSession(
    record: _record,
    tileCount: widget.tileCount,
  );
  final FrameHistory _history = FrameHistory();

  @override
  void initState() {
    super.initState();
    _history.start();
  }

  @override
  void dispose() {
    _session.dispose();
    _history.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final Duration budget = budgetFor(View.of(context).display.refreshRate);
    return ColoredBox(
      color: LabColors.bg,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: ListenableBuilder(
            listenable: Listenable.merge(<Listenable>[_session, _record]),
            builder: (BuildContext context, Widget? _) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  _Header(
                    rendererLabel: widget.rendererLabel,
                    budget: budget,
                    onBack: widget.onBack,
                  ),
                  if (widget.engineNote != null) ...<Widget>[
                    const SizedBox(height: 8),
                    Text(widget.engineNote!, style: LabText.label),
                  ],
                  const SizedBox(height: 12),
                  const LabCard(
                    padding: EdgeInsets.fromLTRB(12, 10, 12, 10),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'MOTION · a freeze leaves a red gap',
                          style: LabText.label,
                        ),
                        SizedBox(height: 4),
                        HeartbeatLane(),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                  LabCard(
                    padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
                    child: FrameStrip(history: _history, budget: budget),
                  ),
                  const SizedBox(height: 10),
                  _Scores(
                    record: _record,
                    measuring: _session.state == StormState.measuring,
                    budget: budget,
                  ),
                  const SizedBox(height: 10),
                  Expanded(
                    child: LabCard(
                      padding: const EdgeInsets.all(6),
                      child: _session.revealed
                          ? StormGrid(tiles: _session.tiles)
                          : Center(
                              child: Text(
                                '${_session.tiles.length} effects not drawn yet',
                                style: LabText.body.copyWith(
                                  color: LabColors.textSecondary,
                                ),
                              ),
                            ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _session.revealed
                      ? LabButton(
                          label: 'HIDE',
                          onPressed: _session.state == StormState.revealed
                              ? _session.hide
                              : null,
                        )
                      : LabButton(
                          label: 'REVEAL ${_session.tiles.length} EFFECTS',
                          primary: true,
                          onPressed: () {
                            _history.resetPeaks();
                            _session.reveal(budget);
                          },
                        ),
                ],
              );
            },
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
    required this.onBack,
  });

  final String rendererLabel;
  final Duration budget;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    final double hz = 1000000 / budget.inMicroseconds;
    return Row(
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
                    child: Text('Home', style: LabText.label),
                  ),
                ),
              const Text('Shader Storm', style: LabText.title),
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

/// Worst frame after the first reveal next to the worst after a repeat.
class _Scores extends StatelessWidget {
  const _Scores({
    required this.record,
    required this.measuring,
    required this.budget,
  });

  final StormRecord record;
  final bool measuring;
  final Duration budget;

  @override
  Widget build(BuildContext context) {
    return LabCard(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
      child: Row(
        children: <Widget>[
          Expanded(
            child: _Score(
              title: 'FIRST REVEAL',
              result: record.first,
              measuring: measuring && record.nextIsFirst,
              budget: budget,
            ),
          ),
          Container(width: 1, height: 64, color: LabColors.hairline),
          const SizedBox(width: 12),
          Expanded(
            child: _Score(
              title: 'REPEAT',
              result: record.repeat,
              measuring: measuring && !record.nextIsFirst,
              budget: budget,
            ),
          ),
        ],
      ),
    );
  }
}

class _Score extends StatelessWidget {
  const _Score({
    required this.title,
    required this.result,
    required this.measuring,
    required this.budget,
  });

  final String title;
  final FrameWindowResult? result;
  final bool measuring;
  final Duration budget;

  @override
  Widget build(BuildContext context) {
    final FrameWindowResult? shown = measuring ? null : result;
    final String value = measuring
        ? '···'
        : shown == null
        ? '–'
        : formatMs(shown.worst);
    final Color tint = shown == null
        ? LabColors.textSecondary
        : frameColor(shown.worst, budget);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text('$title · WORST FRAME', style: LabText.label),
        const SizedBox(height: 4),
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: <Widget>[
            Flexible(
              child: FittedBox(
                fit: BoxFit.scaleDown,
                alignment: Alignment.centerLeft,
                child: Text(
                  value,
                  style: LabText.lapTime.copyWith(color: tint, fontSize: 36),
                ),
              ),
            ),
            const SizedBox(width: 4),
            Text(
              'ms',
              style: LabText.number.copyWith(color: LabColors.textSecondary),
            ),
          ],
        ),
        Text(
          shown == null
              ? ' '
              : '${shown.overBudgetFrames}/${shown.frames} frames over budget',
          style: LabText.label,
        ),
      ],
    );
  }
}
