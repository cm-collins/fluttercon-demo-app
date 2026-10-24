-- Longest slices on Flutter's raster thread (named "1.raster").
SELECT
  s.name,
  s.ts,
  ROUND(s.dur / 1e6, 3) AS dur_ms
FROM slice AS s
JOIN thread_track AS tt ON s.track_id = tt.id
JOIN thread AS t USING (utid)
WHERE t.name LIKE '%raster%'
ORDER BY s.dur DESC
LIMIT 50;
