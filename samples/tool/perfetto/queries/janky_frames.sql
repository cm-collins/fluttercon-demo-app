-- Frames that SurfaceFlinger's frame timeline marked as janky (Android 12+).
-- Replace the package name with the app's application ID.
SELECT
  a.name AS frame,
  ROUND(a.dur / 1e6, 3) AS actual_ms,
  a.jank_type
FROM actual_frame_timeline_slice AS a
JOIN process AS p USING (upid)
WHERE p.name LIKE 'dev.fluttercon.kiln%'
  AND a.jank_type != 'None'
ORDER BY a.ts;
