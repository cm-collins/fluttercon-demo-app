/// What the Canvas Thrash painters asked the engine to draw, counted while
/// they paint.
///
/// Painters must not notify listeners during paint, so this is a plain object
/// that the screen reads a few times a second.
class ThrashLedger {
  /// Draw calls recorded by the last scene paint (`drawPath`, `drawCircle`,
  /// `drawVertices`, …), not counting the grid.
  int draws = 0;

  /// `saveLayer` calls in the last scene paint.
  int layers = 0;

  /// Path points handed to the engine by the last scene paint.
  int pathPoints = 0;

  /// Every time the grid has been painted since the screen opened.
  int gridPaints = 0;

  void beginScene() {
    draws = 0;
    layers = 0;
    pathPoints = 0;
  }
}
