import 'package:flutter/widgets.dart';
import 'package:flutter/scheduler.dart';

import 'lab_tokens.dart';

/// A dot that sweeps across the lane on every frame.
///
/// At 120 Hz the trail is a smooth comet. When a frame is late the dot jumps,
/// and the jump is drawn as a red bar that stays on screen for a few seconds,
/// so a freeze is visible from the back of the room.
class HeartbeatLane extends StatefulWidget {
  const HeartbeatLane({
    super.key,
    this.period = const Duration(milliseconds: 1600),
    this.height = 44,
  });

  final Duration period;
  final double height;

  @override
  State<HeartbeatLane> createState() => _HeartbeatLaneState();
}

class _HeartbeatLaneState extends State<HeartbeatLane>
    with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  final ValueNotifier<int> _repaint = ValueNotifier<int>(0);
  final List<double> _trail = <double>[];
  final List<_Gap> _gaps = <_Gap>[];
  Duration _last = Duration.zero;

  /// Movement that takes longer than this between two frames is a freeze.
  static const Duration _freeze = Duration(milliseconds: 50);
  static const Duration _gapLife = Duration(seconds: 4);

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_tick)..start();
  }

  void _tick(Duration elapsed) {
    final double position = _position(elapsed);
    final Duration step = elapsed - _last;
    if (_last != Duration.zero && step >= widget.period) {
      // The dot would have gone round at least once; mark the whole lane
      // rather than the leftover sliver.
      _gaps.add(_Gap(from: 0, to: 1, at: elapsed, length: step));
    } else if (_last != Duration.zero && step > _freeze) {
      _gaps.add(
        _Gap(from: _position(_last), to: position, at: elapsed, length: step),
      );
    }
    _gaps.removeWhere((_Gap gap) => elapsed - gap.at > _gapLife);
    _last = elapsed;
    _trail.add(position);
    if (_trail.length > 24) {
      _trail.removeAt(0);
    }
    _repaint.value++;
  }

  double _position(Duration elapsed) {
    final int period = widget.period.inMicroseconds;
    return (elapsed.inMicroseconds % period) / period;
  }

  @override
  void dispose() {
    _ticker.dispose();
    _repaint.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: SizedBox(
        height: widget.height,
        width: double.infinity,
        child: CustomPaint(
          painter: _HeartbeatPainter(
            trail: _trail,
            gaps: _gaps,
            now: () => _last,
            gapLife: _gapLife,
            repaint: _repaint,
          ),
        ),
      ),
    );
  }
}

class _Gap {
  const _Gap({
    required this.from,
    required this.to,
    required this.at,
    required this.length,
  });

  final double from;
  final double to;
  final Duration at;
  final Duration length;
}

class _HeartbeatPainter extends CustomPainter {
  _HeartbeatPainter({
    required this.trail,
    required this.gaps,
    required this.now,
    required this.gapLife,
    required Listenable repaint,
  }) : super(repaint: repaint);

  final List<double> trail;
  final List<_Gap> gaps;
  final Duration Function() now;
  final Duration gapLife;

  @override
  void paint(Canvas canvas, Size size) {
    final double mid = size.height / 2;
    canvas.drawLine(
      Offset(0, mid),
      Offset(size.width, mid),
      Paint()
        ..color = LabColors.hairline
        ..strokeWidth = 2,
    );

    final Duration current = now();
    for (final _Gap gap in gaps) {
      final double fade =
          1 - (current - gap.at).inMicroseconds / gapLife.inMicroseconds;
      final Paint paint = Paint()
        ..color = LabColors.red.withValues(alpha: fade.clamp(0.0, 1.0));
      _drawSpan(canvas, size, gap.from, gap.to, paint);
    }

    final Paint dot = Paint();
    for (int i = 0; i < trail.length; i++) {
      final double age = (i + 1) / trail.length;
      dot.color = LabColors.aurora.withValues(alpha: age * age);
      canvas.drawCircle(Offset(trail[i] * size.width, mid), 3 + 5 * age, dot);
    }
  }

  /// Draws the jump, splitting it in two if the dot wrapped to the start.
  void _drawSpan(Canvas canvas, Size size, double from, double to, Paint p) {
    final double top = size.height * 0.15;
    final double bottom = size.height * 0.85;
    if (to >= from) {
      canvas.drawRect(
        Rect.fromLTRB(from * size.width, top, to * size.width, bottom),
        p,
      );
    } else {
      canvas.drawRect(
        Rect.fromLTRB(from * size.width, top, size.width, bottom),
        p,
      );
      canvas.drawRect(Rect.fromLTRB(0, top, to * size.width, bottom), p);
    }
  }

  @override
  bool shouldRepaint(_HeartbeatPainter oldDelegate) => false;
}
