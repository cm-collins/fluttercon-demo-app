import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import '../logic/durations.dart';
import '../logic/frame_window.dart';
import '../logic/shader_jank_session.dart';
import 'lab_button.dart';
import 'lab_chrome.dart';
import 'lab_tokens.dart';

/// Controls and evidence for the cold/warm first-use shader experiment.
class ShaderJankPanel extends StatefulWidget {
  const ShaderJankPanel({
    super.key,
    required this.shaderAsset,
    required this.budget,
    this.onMeasuring,
  });

  final String shaderAsset;
  final Duration budget;
  final ValueChanged<bool>? onMeasuring;

  @override
  State<ShaderJankPanel> createState() => _ShaderJankPanelState();
}

class _ShaderJankPanelState extends State<ShaderJankPanel>
    with SingleTickerProviderStateMixin {
  late final ShaderJankSession _session = ShaderJankSession(
    shaderAsset: widget.shaderAsset,
    onMeasuring: widget.onMeasuring,
    onComplete: _animation.stop,
  );
  late final AnimationController _animation = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 700),
  );

  @override
  void dispose() {
    _animation.dispose();
    _session.dispose();
    super.dispose();
  }

  Future<void> _run({required bool cold}) async {
    await _session.run(budget: widget.budget, cold: cold);
    if (!mounted) {
      return;
    }
    if (_session.active) {
      _animation
        ..reset()
        ..repeat();
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _session,
      builder: (BuildContext context, Widget? _) {
        final ShaderJankSession session = _session;
        final bool active = session.active;
        final FrameResultView result = FrameResultView(
          result: session.result,
          loadDuration: session.loadDuration,
          budget: widget.budget,
          cold: session.lastRunWasCold,
        );
        return LabCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Text('SHADER COMPILATION JANK', style: LabText.label),
              const SizedBox(height: 8),
              const Text(
                'First use can do extra engine or driver work inside a frame. '
                'A warm run shows the steady-state path.',
                style: LabText.body,
              ),
              const SizedBox(height: 12),
              if (active)
                _ShaderJankSurface(
                  key: ValueKey<int>(session.generation),
                  program: session.program!,
                  animation: _animation,
                )
              else
                const SizedBox(
                  height: 92,
                  child: Center(
                    child: Text(
                      'No shader animation is running.',
                      style: LabText.label,
                    ),
                  ),
                ),
              const SizedBox(height: 12),
              Row(
                children: <Widget>[
                  Expanded(
                    child: LabButton(
                      label: 'COLD ATTEMPT',
                      primary: true,
                      onPressed:
                          session.state == ShaderJankState.loading || active
                          ? null
                          : () => _run(cold: true),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: LabButton(
                      label: 'WARM RUN',
                      onPressed:
                          session.state == ShaderJankState.loading || active
                          ? null
                          : () => _run(cold: false),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              result,
              if (session.error != null) ...<Widget>[
                const SizedBox(height: 8),
                Text(
                  session.error!,
                  style: LabText.label.copyWith(color: LabColors.red),
                ),
              ],
              const SizedBox(height: 10),
              Text(
                'A true cold cache state requires an app restart and may require clearing the flavor data. '
                'The size of a first-use spike is device and driver dependent.',
                style: LabText.label,
              ),
            ],
          ),
        );
      },
    );
  }
}

class FrameResultView extends StatelessWidget {
  const FrameResultView({
    super.key,
    required this.result,
    required this.loadDuration,
    required this.budget,
    required this.cold,
  });

  final FrameWindowResult? result;
  final Duration? loadDuration;
  final Duration budget;
  final bool cold;

  @override
  Widget build(BuildContext context) {
    final FrameWindowResult? value = result;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _Metric(
          label: 'RUN',
          value: value == null
              ? '–'
              : cold
              ? 'COLD ATTEMPT'
              : 'WARM',
        ),
        _Metric(
          label: 'PROGRAM LOAD',
          value: loadDuration == null ? '–' : '${formatMs(loadDuration!)} ms',
        ),
        _Metric(
          label: 'WORST FRAME',
          value: value == null ? '–' : '${formatMs(value.worst)} ms',
          color: value == null ? null : frameColor(value.worst, budget),
        ),
        _Metric(
          label: 'OVER BUDGET',
          value: value == null
              ? '–'
              : '${value.overBudgetFrames}/${value.frames}',
          color: value == null || value.overBudgetFrames == 0
              ? LabColors.green
              : LabColors.red,
        ),
        _Metric(
          label: 'RECOVERY',
          value: value == null ? '–' : '${formatMs(value.timeToSmooth)} ms',
        ),
      ],
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value, this.color});

  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: Row(
        children: <Widget>[
          Expanded(child: Text(label, style: LabText.label)),
          Text(value, style: LabText.number.copyWith(color: color)),
        ],
      ),
    );
  }
}

class _ShaderJankSurface extends StatefulWidget {
  const _ShaderJankSurface({
    super.key,
    required this.program,
    required this.animation,
  });

  final ui.FragmentProgram program;
  final Animation<double> animation;

  @override
  State<_ShaderJankSurface> createState() => _ShaderJankSurfaceState();
}

class _ShaderJankSurfaceState extends State<_ShaderJankSurface> {
  late final ui.FragmentShader _shader = widget.program.fragmentShader();

  @override
  void dispose() {
    _shader.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 92,
      width: double.infinity,
      child: AnimatedBuilder(
        animation: widget.animation,
        builder: (BuildContext context, Widget? child) {
          return CustomPaint(
            painter: _ShaderJankPainter(
              shader: _shader,
              time: widget.animation.value,
            ),
          );
        },
      ),
    );
  }
}

class _ShaderJankPainter extends CustomPainter {
  const _ShaderJankPainter({required this.shader, required this.time});

  final ui.FragmentShader shader;
  final double time;

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) {
      return;
    }
    shader
      ..setFloat(0, size.width)
      ..setFloat(1, size.height)
      ..setFloat(2, time * 6.283185);
    canvas.drawRect(Offset.zero & size, Paint()..shader = shader);
  }

  @override
  bool shouldRepaint(_ShaderJankPainter oldDelegate) =>
      oldDelegate.time != time;
}
