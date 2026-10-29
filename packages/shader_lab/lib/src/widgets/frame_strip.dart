import 'dart:ui' show VertexMode, Vertices;

import 'package:flutter/widgets.dart';

import '../logic/durations.dart';
import '../logic/frame_history.dart';
import '../logic/frame_window.dart';
import 'lab_tokens.dart';

/// Recent frames as two lanes of bars: UI thread on top, raster thread below.
///
/// Bars are scaled to four frame budgets and clipped above that, with a white
/// cap marking a clipped bar. Each lane title carries the peak since the last
/// [FrameHistory.resetPeaks], so a spike stays readable after it scrolls off.
/// A first-use shader compile on Skia lands in the raster lane.
class FrameStrip extends StatelessWidget {
  const FrameStrip({
    super.key,
    required this.history,
    required this.budget,
    this.laneHeight = 52,
  });

  final FrameHistory history;
  final Duration budget;
  final double laneHeight;

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          _LaneTitle(
            title: 'UI THREAD · build',
            history: history,
            budget: budget,
            peak: () => history.peakBuild,
          ),
          const SizedBox(height: 4),
          _Lane(
            history: history,
            budget: budget,
            height: laneHeight,
            pick: (FrameSample s) => s.build,
          ),
          const SizedBox(height: 10),
          _LaneTitle(
            title: 'RASTER THREAD · draw',
            history: history,
            budget: budget,
            peak: () => history.peakRaster,
          ),
          const SizedBox(height: 4),
          _Lane(
            history: history,
            budget: budget,
            height: laneHeight,
            pick: (FrameSample s) => s.raster,
          ),
        ],
      ),
    );
  }
}

class _LaneTitle extends StatelessWidget {
  const _LaneTitle({
    required this.title,
    required this.history,
    required this.budget,
    required this.peak,
  });

  final String title;
  final FrameHistory history;
  final Duration budget;
  final Duration Function() peak;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Expanded(child: Text(title, style: LabText.label)),
        ListenableBuilder(
          listenable: history,
          builder: (BuildContext context, Widget? _) {
            final Duration value = peak();
            return Text(
              value == Duration.zero ? ' ' : 'peak ${formatMs(value)} ms',
              style: LabText.label.copyWith(
                color: value > budget ? LabColors.red : LabColors.green,
                fontWeight: FontWeight.w700,
              ),
            );
          },
        ),
      ],
    );
  }
}

class _Lane extends StatelessWidget {
  const _Lane({
    required this.history,
    required this.budget,
    required this.height,
    required this.pick,
  });

  final FrameHistory history;
  final Duration budget;
  final double height;
  final Duration Function(FrameSample sample) pick;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
      width: double.infinity,
      child: CustomPaint(
        painter: _LanePainter(history: history, budget: budget, pick: pick),
      ),
    );
  }
}

class _LanePainter extends CustomPainter {
  _LanePainter({
    required this.history,
    required this.budget,
    required this.pick,
  }) : super(repaint: history);

  final FrameHistory history;
  final Duration budget;
  final Duration Function(FrameSample sample) pick;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(
      Offset.zero & size,
      Paint()..color = LabColors.surfaceElevated,
    );
    final double scale = budget.inMicroseconds * 4.0;
    final double budgetY =
        size.height - size.height * budget.inMicroseconds / scale;

    // Every bar is two triangles in one drawVertices call, so the meter adds
    // little to the raster time it reports. A Path of many rectangles would
    // also be one call, but Skia renders it through its slow general path
    // code and the meter itself went over budget.
    final List<Offset> points = <Offset>[];
    final List<Color> colors = <Color>[];
    void bar(Rect r, Color color) {
      points.addAll(<Offset>[
        r.topLeft,
        r.topRight,
        r.bottomRight,
        r.topLeft,
        r.bottomRight,
        r.bottomLeft,
      ]);
      colors.addAll(List<Color>.filled(6, color));
    }

    final List<FrameSample> frames = history.frames;
    final int slots = history.capacity;
    final double slot = size.width / slots;
    final int offset = slots - frames.length;
    for (int i = 0; i < frames.length; i++) {
      final Duration cost = pick(frames[i]);
      final double fraction = cost.inMicroseconds / scale;
      final double h = size.height * fraction.clamp(0.0, 1.0);
      final double left = (offset + i) * slot;
      bar(
        Rect.fromLTWH(left, size.height - h, slot * 0.7, h),
        cost > budget ? LabColors.red : LabColors.green,
      );
      if (fraction > 1) {
        bar(Rect.fromLTWH(left, 0, slot * 0.7, 3), LabColors.textPrimary);
      }
    }
    if (points.isNotEmpty) {
      canvas.drawVertices(
        Vertices(VertexMode.triangles, points, colors: colors),
        BlendMode.dst,
        Paint(),
      );
    }

    canvas.drawLine(
      Offset(0, budgetY),
      Offset(size.width, budgetY),
      Paint()
        ..color = LabColors.ember
        ..strokeWidth = 1.5,
    );
  }

  @override
  bool shouldRepaint(_LanePainter oldDelegate) =>
      oldDelegate.history != history || oldDelegate.budget != budget;
}
