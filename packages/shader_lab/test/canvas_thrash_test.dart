import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shader_lab/shader_lab.dart';

const Size canvasSize = Size(400, 300);

ThrashLedger paintScene(ThrashScene scene, Set<ThrashFix> fixes) {
  final ThrashLedger ledger = ThrashLedger();
  final ui.PictureRecorder recorder = ui.PictureRecorder();
  ThrashScenePainter(
    scene: scene,
    fixes: fixes,
    ledger: ledger,
    cache: ThrashLineCache(),
    seconds: ValueNotifier<double>(1.5),
  ).paint(Canvas(recorder), canvasSize);
  recorder.endRecording().dispose();
  return ledger;
}

Float32List points(List<double> xy) => Float32List.fromList(xy);

FrameSample raster(int ms) => FrameSample(
  vsyncStartMicros: ms,
  rasterFinishMicros: ms,
  build: Duration.zero,
  raster: Duration(milliseconds: ms),
);

Widget host() => const Directionality(
  textDirection: TextDirection.ltr,
  child: MediaQuery(
    data: MediaQueryData(size: Size(412, 915)),
    child: CanvasThrashScreen(rendererLabel: 'Impeller'),
  ),
);

void main() {
  group('scene', () {
    test('the dial multiplies every workload', () {
      final ThrashScene one = ThrashScene(1);
      final ThrashScene eight = ThrashScene(8);

      expect(eight.lineCount, 8 * one.lineCount);
      expect(eight.pointsPerLine, 8 * one.pointsPerLine);
      expect(eight.dotCount, 8 * one.dotCount);
      expect(eight.stripSegments, 8 * one.stripSegments);
    });

    test('a price series spans 0 to 1, ends where it starts and repeats', () {
      final Float32List a = periodicWalk(5000, seed: 3);

      expect(a.reduce((double x, double y) => x < y ? x : y), 0);
      expect(a.reduce((double x, double y) => x > y ? x : y), 1);
      expect(a.last, closeTo(a.first, 1e-6));
      expect(periodicWalk(5000, seed: 3), a);
      expect(periodicWalk(5000, seed: 4), isNot(a));
    });

    test(
      'simplifying keeps at most two points per column and the extremes',
      () {
        final Float32List series = periodicWalk(8000, seed: 1);
        final Float32List xy = decimate(series, 100);
        final List<double> values = <double>[
          for (int i = 1; i < xy.length; i += 2) xy[i],
        ];

        expect(xy.length ~/ 2, lessThanOrEqualTo(200));
        expect(values, contains(0.0));
        expect(values, contains(1.0));
        for (int i = 2; i < xy.length; i += 2) {
          expect(xy[i], greaterThanOrEqualTo(xy[i - 2]));
        }
      },
    );

    test('a short series is kept whole', () {
      final Float32List series = periodicWalk(50, seed: 1);

      expect(decimate(series, 100).length, 100);
    });
  });

  group('stroke tessellation model', () {
    const double half = 0.75;
    const double scale = 3;

    test('a straight line adds no join', () {
      final int v = strokeStripVertexCount(
        points(<double>[0, 0, 10, 0, 20, 0]),
        halfWidth: half,
        scale: scale,
      );

      expect(v, 6);
      expect(stripTriangles(v), 4);
    });

    test('a corner adds a bevel join of two vertices', () {
      final int v = strokeStripVertexCount(
        points(<double>[0, 0, 10, 0, 10, 10]),
        halfWidth: half,
        scale: scale,
      );

      expect(v, 8);
      expect(stripTriangles(v), 6);
    });

    test('a zero-length segment is skipped', () {
      expect(
        strokeStripVertexCount(
          points(<double>[0, 0, 0, 0, 10, 0]),
          halfWidth: half,
          scale: scale,
        ),
        4,
      );
    });

    test('a stroke under a quarter pixel wide never gets joins', () {
      expect(
        strokeStripVertexCount(
          points(<double>[0, 0, 10, 0, 10, 10]),
          halfWidth: half,
          scale: 0.2,
        ),
        6,
      );
    });

    test('the join threshold follows the engine formula', () {
      // hypotenuse 1, threshold 0.25: cos = 2 * (1 - 0.0625) - 1.
      expect(maximumJoinCosine(1, 1), closeTo(0.875, 1e-9));
      expect(maximumJoinCosine(0.25, 1), -1.1);
    });

    test('vertices sit half the stroke width either side of the line', () {
      final Float32List v = strokeStrip(
        points(<double>[0, 0, 10, 0]),
        halfWidth: half,
        scale: scale,
      );

      expect(v, <double>[0, half, 0, -half, 10, half, 10, -half]);
    });
  });

  group('ledger', () {
    test('broken 8× records a layer per dot and a draw per strip segment', () {
      final ThrashScene scene = ThrashScene(8);
      final ThrashLedger ledger = paintScene(scene, <ThrashFix>{});

      expect(ledger.layers, scene.dotCount);
      expect(
        ledger.draws,
        scene.stripSegments + scene.lineCount + 2 * scene.dotCount,
      );
      expect(
        ledger.pathPoints,
        scene.lineCount * scene.pointsPerLine + 4 * scene.stripSegments,
      );
      expect(ledger.gridPaints, 1);
    });

    test(
      'every fix on removes layers, batches the strip and skips the grid',
      () {
        final ThrashScene scene = ThrashScene(8);
        final ThrashLedger ledger = paintScene(scene, ThrashFix.values.toSet());

        expect(ledger.layers, 0);
        expect(ledger.draws, 1 + 2 * scene.lineCount + 2 * scene.dotCount);
        expect(
          ledger.pathPoints,
          lessThan(scene.lineCount * scene.pointsPerLine ~/ 5),
        );
        expect(ledger.gridPaints, 0);
      },
    );
  });

  group('x-ray', () {
    final ThrashScene scene = ThrashScene(8);
    final ThrashLayout layout = ThrashLayout(canvasSize);

    test(
      'a full-detail line is drawn as the whole series, split at the seam',
      () {
        final List<Float32List> contours = drawnContours(
          scene,
          layout,
          ThrashLineCache(),
          0,
          0.3,
          simplified: false,
        );
        final int total = contours.fold(
          0,
          (int sum, Float32List c) => sum + c.length ~/ 2,
        );

        expect(contours, hasLength(2));
        expect(total, scene.pointsPerLine);
      },
    );

    test('simplified lines model far fewer triangles', () {
      final ThrashLineCache cache = ThrashLineCache();
      final XrayCounts full = countLineTriangles(
        scene,
        layout,
        cache,
        0.3,
        simplified: false,
        scale: 3,
      );
      final XrayCounts simple = countLineTriangles(
        scene,
        layout,
        cache,
        0.3,
        simplified: true,
        scale: 3,
      );

      expect(
        full.triangles,
        greaterThan(2 * full.points - 4 * scene.lineCount),
      );
      expect(simple.triangles * 5, lessThan(full.triangles));
    });
  });

  test('percentile reads the history', () {
    final FrameHistory history = FrameHistory()
      ..add(<FrameSample>[for (int ms = 1; ms <= 10; ms++) raster(ms)]);

    expect(
      history.percentile(0.9, (FrameSample s) => s.raster),
      const Duration(milliseconds: 9),
    );
    history.dispose();
  });

  testWidgets('the dial, the fixes and x-ray change the screen', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(412, 915));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(host());

    expect(find.text('Canvas Thrash'), findsOneWidget);
    for (final ThrashFix fix in ThrashFix.values) {
      expect(find.text(fix.label), findsOneWidget);
    }
    expect(find.textContaining('line triangles'), findsNothing);

    await tester.tap(find.text('8×'));
    await tester.tap(find.text('Batch draws'));
    await tester.tap(find.text('X-ray'));
    // One frame paints the new settings, then the counters refresh.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.textContaining('line triangles'), findsOneWidget);
    expect(find.textContaining('layers 64'), findsOneWidget);

    await tester.tap(find.text('Glow without layers'));
    // One frame paints the new settings, then the counters refresh.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.textContaining('layers 0'), findsOneWidget);

    // The canvas never stops animating; unmount it before the test ends.
    await tester.pumpWidget(const SizedBox());
  });
}
