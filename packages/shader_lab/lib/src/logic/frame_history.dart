import 'package:flutter/foundation.dart';
import 'package:flutter/scheduler.dart';

import 'frame_timer.dart';
import 'frame_window.dart';

/// The most recent engine frame timings, oldest first.
///
/// The engine reports timings in batches, so the history updates a few times a
/// second rather than on every frame.
class FrameHistory extends ChangeNotifier {
  FrameHistory({this.capacity = 120});

  final int capacity;
  final List<FrameSample> _frames = <FrameSample>[];
  bool _listening = false;

  /// Slowest build and raster times since [resetPeaks]. They outlive the
  /// frames themselves, which scroll out of [frames] after about a second.
  Duration peakBuild = Duration.zero;
  Duration peakRaster = Duration.zero;

  List<FrameSample> get frames => List<FrameSample>.unmodifiable(_frames);

  void resetPeaks() {
    peakBuild = Duration.zero;
    peakRaster = Duration.zero;
    notifyListeners();
  }

  void start() {
    if (!_listening) {
      SchedulerBinding.instance.addTimingsCallback(_handleTimings);
      _listening = true;
    }
  }

  void add(Iterable<FrameSample> samples) {
    for (final FrameSample sample in samples) {
      _frames.add(sample);
      if (sample.build > peakBuild) {
        peakBuild = sample.build;
      }
      if (sample.raster > peakRaster) {
        peakRaster = sample.raster;
      }
    }
    if (_frames.length > capacity) {
      _frames.removeRange(0, _frames.length - capacity);
    }
    notifyListeners();
  }

  void _handleTimings(List<FrameTiming> timings) {
    add(timings.map(sampleFrom));
  }

  @override
  void dispose() {
    if (_listening) {
      SchedulerBinding.instance.removeTimingsCallback(_handleTimings);
      _listening = false;
    }
    super.dispose();
  }
}
