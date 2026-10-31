#!/usr/bin/env bash
# Records a system trace of one cold Shader Storm reveal, with Flutter engine events.
#
# usage: tool/benchmark/storm_trace.sh <skia|impeller> [tiles] [output.txt]
#   tool/benchmark/storm_trace.sh skia 144 skia-144.txt
#
# Tracing slows every frame, so use traces to see *what* happens and storm_bench.sh
# for the numbers. Summarise the result with trace_summary.py, or open it in
# https://ui.perfetto.dev and search for GrGLProgramBuilder::finalize or
# PipelineVK::Create on the 1.raster thread.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=storm_common.sh
source "$here/storm_common.sh"

case "${1:-}" in
  skia) pkg="$STORM_SKIA"; extra=(--ez trace-skia true) ;;
  impeller) pkg="$STORM_IMPELLER"; extra=() ;;
  *) echo "usage: $0 <skia|impeller> [tiles] [output.txt]" >&2; exit 2 ;;
esac
tiles="${2:-144}"
out="${3:-$1-$tiles-$(date +%Y%m%d-%H%M%S).txt}"

storm_require_device
storm_locate "$pkg"

adb shell pm clear "$pkg" >/dev/null
adb logcat -c
storm_launch "$pkg" "${extra[@]}" --ez trace-systrace true
storm_open "$tiles"

adb shell atrace --async_start -b 131072 -a "$pkg" gfx view sched freq >/dev/null
sleep 1
storm_tap reveal
storm_wait_result >/dev/null || true
sleep 1
adb shell atrace --async_stop >"$out"
adb shell am force-stop "$pkg"

echo "trace: $out"
python3 -I "$here/trace_summary.py" "$out"
