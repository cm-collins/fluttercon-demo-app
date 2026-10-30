#!/usr/bin/env bash
# Repeated Shader Storm measurements for both flavors, with tracing off.
#
# usage: tool/benchmark/storm_bench.sh [rounds] [tile counts] [output.csv]
#   tool/benchmark/storm_bench.sh 3 "48 96 144" storm.csv
#
# Each round, for each tile count, runs the Skia then the Impeller flavor:
#   cold      app data cleared, first reveal
#   repeat    HIDE, then reveal again in the same process
#   relaunch  app restarted with its disk caches kept, first reveal
# Prints a median table at the end. Keep the phone awake, charging and at a fixed
# refresh rate, and do not touch it while this runs.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=storm_common.sh
source "$here/storm_common.sh"

rounds="${1:-3}"
counts="${2:-48 96 144}"
csv="${3:-storm-$(date +%Y%m%d-%H%M%S).csv}"

storm_require_device
storm_locate "$STORM_SKIA"

{
  echo "# device=$(adb shell getprop ro.product.model | tr -d '\r') api=$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
  echo "# commit=$(git -C "$here" rev-parse --short HEAD 2>/dev/null || echo unknown) date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "round,engine,tiles,scenario,worst_ms,over_budget"
} >"$csv"

record() {
  local round=$1 engine=$2 tiles=$3 scenario=$4 line worst over
  line=$(storm_wait_result) || line=""
  worst=$(sed -n 's/.*worstMs=\([0-9.]*\).*/\1/p' <<<"$line")
  over=$(sed -n 's/.*overBudget=\([0-9/]*\).*/\1/p' <<<"$line")
  echo "$round,$engine,$tiles,$scenario,${worst:-NA},${over:-NA}" | tee -a "$csv"
}

for round in $(seq 1 "$rounds"); do
  for tiles in $counts; do
    for pkg in "$STORM_SKIA" "$STORM_IMPELLER"; do
      engine=$(storm_engine "$pkg")

      adb shell pm clear "$pkg" >/dev/null
      adb logcat -c
      storm_launch "$pkg"
      storm_open "$tiles"
      storm_tap reveal
      record "$round" "$engine" "$tiles" cold

      storm_tap reveal # HIDE sits where REVEAL was
      sleep 2
      adb logcat -c
      storm_tap reveal
      record "$round" "$engine" "$tiles" repeat

      adb shell am force-stop "$pkg"
      adb logcat -c
      storm_launch "$pkg"
      storm_open "$tiles"
      storm_tap reveal
      record "$round" "$engine" "$tiles" relaunch
      adb shell am force-stop "$pkg"
    done
  done
done

echo
echo "results: $csv"
python3 -I - "$csv" <<'EOF'
import csv, statistics, sys
rows = [r for r in csv.DictReader(l for l in open(sys.argv[1]) if not l.startswith("#"))]
groups = {}
for r in rows:
    if r["worst_ms"] != "NA":
        groups.setdefault((int(r["tiles"]), r["scenario"], r["engine"]), []).append(float(r["worst_ms"]))
print(f"{'tiles':>5}  {'scenario':<9} {'skia median (range)':<26} {'impeller median (range)':<26}")
for tiles, scenario in sorted({(t, s) for t, s, _ in groups}, key=lambda k: (k[0], ["cold", "repeat", "relaunch"].index(k[1]))):
    cells = []
    for engine in ("skia", "impeller"):
        v = groups.get((tiles, scenario, engine), [])
        cells.append(f"{statistics.median(v):7.1f} ({min(v):.0f}-{max(v):.0f})" if v else "-")
    print(f"{tiles:>5}  {scenario:<9} {cells[0]:<26} {cells[1]:<26}")
EOF
