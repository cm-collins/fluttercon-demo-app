import 'dart:ui';

enum StormFill { linear, radial, sweep, solid }

enum StormShape { rect, rrect, circle, star }

enum StormBlur { none, normal, outer, inner }

enum StormFilter { none, matrix, mode }

const List<int> stormStops = <int>[2, 3, 5];

/// Grid sizes offered before the first reveal.
const List<int> stormTileCounts = <int>[48, 96, 144];

/// A mask blur is an extra render pass on Impeller every frame. Capping the
/// count keeps the per-frame cost flat when the grid grows, so a larger storm
/// adds first-use work without adding drawing work.
const int stormMaxBlurred = 12;

const List<TileMode> stormTileModes = <TileMode>[
  TileMode.clamp,
  TileMode.repeated,
  TileMode.mirror,
  TileMode.decal,
];

/// Porter-Duff modes only. Advanced blends such as screen and multiply make
/// Impeller read back the destination on every frame, which turns this into a
/// drawing-cost demo. Modulate with a mask blur draws black boxes on Impeller.
const List<BlendMode> stormBlendModes = <BlendMode>[
  BlendMode.srcOver,
  BlendMode.plus,
  BlendMode.srcATop,
];

/// One tile of the Shader Storm grid: a combination of built-in paint effects.
///
/// Skia generates and compiles a GPU program the first time it meets a new
/// combination like this. Impeller draws every combination with shaders that
/// were compiled when the engine was built.
class StormTileSpec {
  const StormTileSpec({
    required this.fill,
    required this.stops,
    required this.tileMode,
    required this.blendMode,
    required this.blur,
    required this.filter,
    required this.shape,
    required this.stroke,
  });

  final StormFill fill;
  final int stops;
  final TileMode tileMode;
  final BlendMode blendMode;
  final StormBlur blur;
  final StormFilter filter;
  final StormShape shape;

  /// Outline instead of fill. Skia uses different geometry code for each.
  final bool stroke;

  /// Identity of the effect combination. A solid fill ignores stops and tile
  /// mode, so they are left out rather than counted as a different effect.
  String get key {
    final String fillKey = fill == StormFill.solid
        ? 'solid'
        : '${fill.name}:$stops:${tileMode.name}';
    final String style = stroke ? 'stroke' : 'fill';
    return '$fillKey/${blendMode.name}/${blur.name}/${filter.name}/${shape.name}/$style';
  }
}

/// [count] distinct effect combinations, in the same order on every run.
List<StormTileSpec> stormTiles(int count) {
  final Set<String> seen = <String>{};
  final List<StormTileSpec> tiles = <StormTileSpec>[];
  int blurred = 0;
  // The dimension cycles repeat every 5040 indices.
  for (int i = 0; tiles.length < count && i < 5040; i++) {
    // One tile in four has a blur, up to [stormMaxBlurred].
    final StormBlur blur = i % 4 == 1 && blurred < stormMaxBlurred
        ? StormBlur.values[1 + (i ~/ 4) % 3]
        : StormBlur.none;
    final StormTileSpec spec = StormTileSpec(
      fill: StormFill.values[i % 4],
      stops: stormStops[(i ~/ 4) % 3],
      tileMode: stormTileModes[(i * 3 + i ~/ 7) % 4],
      blendMode: stormBlendModes[(i * 2 + 1) % 3],
      blur: blur,
      filter: StormFilter.values[(i ~/ 3) % 3],
      shape: StormShape.values[(i ~/ 5) % 4],
      stroke: (i ~/ 2).isOdd,
    );
    if (seen.add(spec.key)) {
      tiles.add(spec);
      if (blur != StormBlur.none) {
        blurred++;
      }
    }
  }
  return tiles;
}
