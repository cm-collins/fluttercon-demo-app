import 'package:flutter_test/flutter_test.dart';
import 'package:kiln_samples/kiln_samples.dart';

void main() {
  const budget = 1000 / 120;

  group('FrameBudgetMonitor.classify', () {
    test('uses F1 timing colours at 120 Hz', () {
      expect(FrameBudgetMonitor.classify(5.9, budget), FrameState.best);
      expect(FrameBudgetMonitor.classify(8.3, budget), FrameState.inBudget);
      expect(FrameBudgetMonitor.classify(11.9, budget), FrameState.atRisk);
      expect(FrameBudgetMonitor.classify(16.7, budget), FrameState.dropped);
    });
  });

  group('FrameBudgetMonitor.computeStats', () {
    test('returns zero for an empty window', () {
      final stats = FrameBudgetMonitor.computeStats(const []);
      expect(stats.p50, 0);
      expect(stats.p99, 0);
    });

    test('computes percentiles over unsorted input', () {
      final values = [for (var i = 100; i >= 1; i--) i.toDouble()];
      final stats = FrameBudgetMonitor.computeStats(values);
      expect(stats.p50, closeTo(50.5, 1));
      expect(stats.p90, closeTo(90, 1));
      expect(stats.p99, closeTo(99, 1));
    });
  });
}
