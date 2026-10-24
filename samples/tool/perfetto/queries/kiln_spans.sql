-- Cost of every Kiln scenario span (requires flutter run --trace-systrace).
SELECT
  name,
  COUNT(*) AS calls,
  ROUND(AVG(dur) / 1e6, 3) AS avg_ms,
  ROUND(MAX(dur) / 1e6, 3) AS max_ms
FROM slice
WHERE name LIKE 'KILN::%'
GROUP BY name
ORDER BY avg_ms DESC;
