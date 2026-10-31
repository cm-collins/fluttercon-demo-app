import 'dart:async';
import 'dart:developer' show Timeline;

import 'package:flutter/widgets.dart';

import '../logic/durations.dart';
import '../logic/frame_history.dart';
import '../logic/frame_timer.dart';
import '../logic/frame_window.dart';
import '../logic/thrash_ledger.dart';
import '../logic/thrash_scene.dart';
import '../widgets/frame_strip.dart';
import '../widgets/lab_chip.dart';
import '../widgets/lab_chrome.dart';
import '../widgets/lab_header.dart';
import '../widgets/lab_tokens.dart';
import '../widgets/thrash_canvas.dart';
import '../widgets/xray_lens.dart';

/// A live canvas thrashed until frames go red, then fixed one cause at a time.
///
/// The thrash dial multiplies the work. Each fix swaps one drawing pattern for
/// a cheaper one that looks the same, and the UI and raster lanes show which
/// thread got relief. X-ray shows the triangles the price lines turn into.
class CanvasThrashScreen extends StatefulWidget {
  const CanvasThrashScreen({
    super.key,
    required this.rendererLabel,
    this.onBack,
  });

  final String rendererLabel;
  final VoidCallback? onBack;

  @override
  State<CanvasThrashScreen> createState() => _CanvasThrashScreenState();
}

/// Counters shown under the controls, refreshed a few times a second.
@immutable
class _Counters {
  const _Counters({
    this.draws = 0,
    this.layers = 0,
    this.pathPoints = 0,
    this.gridPaintsPerSecond = 0,
    this.lines = XrayCounts.zero,
    this.framesPerSecond = 0,
  });

  final int draws;
  final int layers;
  final int pathPoints;
  final int gridPaintsPerSecond;

  /// Only counted while X-ray is on: the model costs Dart time to run.
  final XrayCounts lines;
  final int framesPerSecond;
}

class _CanvasThrashScreenState extends State<CanvasThrashScreen> {
  final GlobalKey<ThrashCanvasState> _canvas = GlobalKey<ThrashCanvasState>();
  final FrameHistory _history = FrameHistory();
  final ThrashLedger _ledger = ThrashLedger();
  final ValueNotifier<_Counters> _counters = ValueNotifier<_Counters>(
    const _Counters(),
  );
  final Stopwatch _sinceChange = Stopwatch()..start();
  late ThrashScene _scene = ThrashScene(thrashLevels.first);
  Set<ThrashFix> _fixes = <ThrashFix>{};
  bool _xray = false;
  Timer? _countTimer;
  Timer? _logTimer;
  int _lastGridPaints = 0;

  static const Duration _countEvery = Duration(milliseconds: 250);

  @override
  void initState() {
    super.initState();
    _history.start();
    _countTimer = Timer.periodic(_countEvery, (_) => _count());
    _logTimer = Timer.periodic(const Duration(seconds: 1), (_) => _log());
  }

  @override
  void dispose() {
    _countTimer?.cancel();
    _logTimer?.cancel();
    _history.dispose();
    _counters.dispose();
    super.dispose();
  }

  void _setLevel(int level) {
    if (level == _scene.level) {
      return;
    }
    setState(() => _scene = ThrashScene(level));
    _configChanged();
  }

  void _toggle(ThrashFix fix) {
    setState(() {
      _fixes = <ThrashFix>{..._fixes};
      if (!_fixes.remove(fix)) {
        _fixes.add(fix);
      }
    });
    _configChanged();
  }

  void _toggleXray() {
    setState(() => _xray = !_xray);
    _configChanged();
  }

  void _configChanged() {
    _history.resetPeaks();
    _sinceChange.reset();
    Timeline.instantSync(
      'KILN::Thrash::config',
      arguments: <String, String>{
        'level': '${_scene.level}',
        'fixes': _fixKeys,
        'xray': '$_xray',
      },
    );
  }

  String get _fixKeys => _fixes.isEmpty
      ? 'none'
      : (ThrashFix.values.where(_fixes.contains).map((ThrashFix f) => f.name))
            .join(',');

  void _count() {
    final ThrashCanvasState? canvas = _canvas.currentState;
    final RenderBox? box = canvas?.context.findRenderObject() as RenderBox?;
    final int gridPaints = _ledger.gridPaints;
    final double perSecond =
        (gridPaints - _lastGridPaints) *
        Duration.millisecondsPerSecond /
        _countEvery.inMilliseconds;
    _lastGridPaints = gridPaints;
    XrayCounts lines = XrayCounts.zero;
    if (_xray && canvas != null && box != null && box.hasSize) {
      lines = countLineTriangles(
        _scene,
        ThrashLayout(box.size),
        canvas.cache,
        ThrashScene.scrollAt(canvas.seconds),
        simplified: _fixes.contains(ThrashFix.simplifyPaths),
        scale: View.of(context).devicePixelRatio,
      );
    }
    _counters.value = _Counters(
      draws: _ledger.draws,
      layers: _ledger.layers,
      pathPoints: _ledger.pathPoints,
      gridPaintsPerSecond: perSecond.round(),
      lines: lines,
      framesPerSecond: _framesInLastSecond(),
    );
  }

  int _framesInLastSecond() {
    final List<FrameSample> frames = _history.frames;
    if (frames.isEmpty) {
      return 0;
    }
    final int newest = frames.last.vsyncStartMicros;
    return frames
        .where(
          (FrameSample f) =>
              newest - f.vsyncStartMicros < Duration.microsecondsPerSecond,
        )
        .length;
  }

  /// One logcat line a second once the frame history only holds frames drawn
  /// with the current settings, so benchmark scripts can read steady numbers.
  void _log() {
    if (_sinceChange.elapsed < const Duration(milliseconds: 2500) ||
        _history.frames.isEmpty) {
      return;
    }
    debugPrint(
      'KILN::Thrash::sample '
      'level=${_scene.level} '
      'fixes=$_fixKeys '
      'xray=$_xray '
      'uiP90Ms=${formatMs(_history.percentile(0.9, (FrameSample s) => s.build))} '
      'rasterP90Ms=${formatMs(_history.percentile(0.9, (FrameSample s) => s.raster))} '
      'frames=${_history.frames.length}',
    );
  }

  @override
  Widget build(BuildContext context) {
    final Duration budget = budgetFor(View.of(context).display.refreshRate);
    return ColoredBox(
      color: LabColors.bg,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              LabHeader(
                title: 'Canvas Thrash',
                rendererLabel: widget.rendererLabel,
                budget: budget,
                onBack: widget.onBack,
              ),
              const SizedBox(height: 10),
              Expanded(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: LabColors.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: LabColors.hairline),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: ThrashCanvas(
                      key: _canvas,
                      scene: _scene,
                      fixes: _fixes,
                      ledger: _ledger,
                      xray: _xray,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              LabCard(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 10),
                child: FrameStrip(
                  history: _history,
                  budget: budget,
                  laneHeight: 30,
                ),
              ),
              const SizedBox(height: 8),
              _Dial(level: _scene.level, onChanged: _setLevel),
              const SizedBox(height: 8),
              LabCard(
                padding: const EdgeInsets.fromLTRB(12, 4, 12, 4),
                child: Column(
                  children: <Widget>[
                    for (final ThrashFix fix in ThrashFix.values)
                      _Toggle(
                        label: fix.label,
                        tag: fix.lane,
                        on: _fixes.contains(fix),
                        onTap: () => _toggle(fix),
                      ),
                    _Toggle(
                      label: 'X-ray',
                      tag: 'model',
                      on: _xray,
                      onTap: _toggleXray,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              ValueListenableBuilder<_Counters>(
                valueListenable: _counters,
                builder: (BuildContext context, _Counters c, Widget? _) =>
                    _CounterLine(counters: c, xray: _xray),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Dial extends StatelessWidget {
  const _Dial({required this.level, required this.onChanged});

  final int level;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        const SizedBox(width: 4),
        const Expanded(child: Text('THRASH', style: LabText.label)),
        for (final int value in thrashLevels) ...<Widget>[
          const SizedBox(width: 8),
          LabChip(
            label: '$value×',
            selected: value == level,
            onTap: () => onChanged(value),
          ),
        ],
      ],
    );
  }
}

class _Toggle extends StatelessWidget {
  const _Toggle({
    required this.label,
    required this.tag,
    required this.on,
    required this.onTap,
  });

  final String label;
  final String tag;
  final bool on;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      toggled: on,
      label: label,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        child: SizedBox(
          height: 34,
          child: Row(
            children: <Widget>[
              DecoratedBox(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: on ? LabColors.violet : null,
                  border: Border.all(
                    color: on ? LabColors.violet : LabColors.textSecondary,
                    width: 2,
                  ),
                ),
                child: const SizedBox(width: 14, height: 14),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  label,
                  style: LabText.body.copyWith(
                    color: on ? LabColors.textPrimary : LabColors.textSecondary,
                    fontWeight: on ? FontWeight.w600 : FontWeight.w400,
                  ),
                ),
              ),
              Text(tag, style: LabText.label),
            ],
          ),
        ),
      ),
    );
  }
}

class _CounterLine extends StatelessWidget {
  const _CounterLine({required this.counters, required this.xray});

  final _Counters counters;
  final bool xray;

  @override
  Widget build(BuildContext context) {
    final _Counters c = counters;
    final String grid = '${c.gridPaintsPerSecond}/s';
    final String main =
        'draws ${_group(c.draws)} · layers ${c.layers} · '
        'path points ${_group(c.pathPoints)} · grid repaints $grid';
    final List<Widget> lines = <Widget>[Text(main, style: LabText.label)];
    if (xray) {
      final int perSecond = c.lines.triangles * c.framesPerSecond;
      lines.add(
        Text(
          'line triangles ${_group(c.lines.triangles)}/frame · '
          '${_millions(perSecond)} M/s at ${c.framesPerSecond} fps',
          style: LabText.label.copyWith(color: LabColors.aurora),
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: lines,
    );
  }

  static String _group(int value) => value.toString().replaceAllMapped(
    RegExp(r'\B(?=(\d{3})+(?!\d))'),
    (Match _) => ',',
  );

  static String _millions(int value) => (value / 1e6).toStringAsFixed(1);
}
