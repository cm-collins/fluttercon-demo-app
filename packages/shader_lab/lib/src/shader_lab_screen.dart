import 'dart:developer' show Timeline;
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import 'budget_readout.dart';
import 'frame_timer.dart';
import 'frame_window.dart';
import 'lab_button.dart';
import 'lab_tokens.dart';
import 'lights_on_scene.dart';
import 'run_board.dart';
import 'run_board_view.dart';

/// Shader Lab: compare first-use shader cost between renderers.
///
/// The same widget runs in Kiln (Impeller) and Kiln Skia. Only [rendererLabel]
/// differs; it is supplied by each app because neither SDK exposes the active
/// renderer to Dart.
class ShaderLabScreen extends StatefulWidget {
  const ShaderLabScreen({
    super.key,
    required this.rendererLabel,
    required this.board,
    this.shaderAsset = 'packages/shader_lab/shaders/speed_ramp.frag',
  });

  final String rendererLabel;
  final RunBoard board;

  /// Asset key of the fragment shader; differs only when this package is the root app.
  final String shaderAsset;

  @override
  State<ShaderLabScreen> createState() => _ShaderLabScreenState();
}

class _ShaderLabScreenState extends State<ShaderLabScreen> {
  final FrameTimer _timer = FrameTimer();
  ui.FragmentProgram? _program;
  bool _lit = false;
  bool _measuring = false;

  @override
  void initState() {
    super.initState();
    Timeline.instantSync('KILN::ShaderLab::enter');
    // Loaded before Lights on so asset I/O is not part of the measured window.
    ui.FragmentProgram.fromAsset(widget.shaderAsset).then((program) {
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

  void _lightsOn() {
    Timeline.instantSync(
      'KILN::ShaderLab::lightsOn',
      arguments: <String, String>{'renderer': widget.rendererLabel},
    );
    _timer.arm(budget: _budget, onResult: _onResult);
    setState(() {
      _lit = true;
      _measuring = true;
    });
  }

  void _lightsOff() {
    _timer.cancel();
    setState(() {
      _lit = false;
      _measuring = false;
    });
  }

  void _onResult(FrameWindowResult result) {
    final LabRun run = widget.board.add(result);
    Timeline.instantSync(
      'KILN::ShaderLab::smooth',
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
  }

  @override
  Widget build(BuildContext context) {
    final ui.FragmentProgram? program = _program;
    final Duration budget = _budget;
    return ColoredBox(
      color: LabColors.bg,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              _Header(rendererLabel: widget.rendererLabel, budget: budget),
              const SizedBox(height: 12),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: _lit && program != null
                      ? LightsOnScene(program: program)
                      : const _DarkStage(),
                ),
              ),
              const SizedBox(height: 12),
              ListenableBuilder(
                listenable: widget.board,
                builder: (BuildContext context, Widget? _) => BudgetReadout(
                  latest: widget.board.latest,
                  measuring: _measuring,
                  budget: budget,
                ),
              ),
              const SizedBox(height: 12),
              RunBoardView(board: widget.board, onClear: widget.board.clear),
              const SizedBox(height: 12),
              LabButton(
                label: _lit ? 'LIGHTS OFF' : 'LIGHTS ON',
                primary: !_lit,
                onPressed: program == null
                    ? null
                    : (_lit ? _lightsOff : _lightsOn),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.rendererLabel, required this.budget});

  final String rendererLabel;
  final Duration budget;

  @override
  Widget build(BuildContext context) {
    final bool skia = rendererLabel.toLowerCase().contains('skia');
    final Color accent = skia ? LabColors.ember : LabColors.violet;
    final double hz = 1000000 / budget.inMicroseconds;
    return Row(
      children: <Widget>[
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Text('Shader Lab', style: LabText.title),
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

/// Plain stage before Lights on: solid fills only, so no scene effect is warmed up.
class _DarkStage extends StatelessWidget {
  const _DarkStage();

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: LabColors.surface,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                for (int i = 0; i < 5; i++)
                  Container(
                    width: 28,
                    height: 28,
                    margin: const EdgeInsets.symmetric(horizontal: 6),
                    decoration: const BoxDecoration(
                      color: LabColors.hairline,
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 20),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 24),
              child: Text(
                'Every effect behind Lights on is drawn for the first time.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: LabColors.textSecondary,
                  fontSize: 16,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
