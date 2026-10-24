/// Broken and fixed rendering samples for the Kiln talk.
///
/// Each scenario exports a `...Broken` widget (the anti-pattern) and a
/// `...Fixed` widget (the pit stop) with the same constructor shape.
library;

export 'src/core/geometry.dart';
export 'src/core/kiln_colors.dart';
export 'src/core/kiln_trace.dart';
export 'src/frame_budget/frame_budget_monitor.dart';
export 'src/glass/glass_cards_broken.dart';
export 'src/glass/glass_cards_fixed.dart';
export 'src/glass/kpi_card.dart';
export 'src/race_control/race_control_broken.dart';
export 'src/race_control/race_control_fixed.dart';
export 'src/race_control/race_control_message.dart';
export 'src/shaders/speed_ramp_painter.dart';
export 'src/speed_ribbon/ribbon_geometry.dart';
export 'src/speed_ribbon/speed_ribbon_broken.dart';
export 'src/speed_ribbon/speed_ribbon_fixed.dart';
export 'src/telemetry_duel/telemetry_duel_broken.dart';
export 'src/telemetry_duel/telemetry_duel_fixed.dart';
export 'src/telemetry_duel/telemetry_trace.dart';
export 'src/tower/tower_row.dart';
export 'src/tower/tower_row_broken.dart';
export 'src/tower/tower_row_fixed.dart';
export 'src/track_map/track_map_broken.dart' show TrackMapBroken;
export 'src/track_map/track_map_fixed.dart';
