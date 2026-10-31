#!/usr/bin/env bash
# Records a system trace of Canvas Thrash at 8x with a chosen set of fixes.
#
# usage: tool/benchmark/thrash_trace.sh <fixes> [seconds] [output.txt] [impeller|skia]
#   tool/benchmark/thrash_trace.sh none 5 broken.txt
#   tool/benchmark/thrash_trace.sh simplifyPaths,batchDraws 5 no-glow-fix.txt
#   tool/benchmark/thrash_trace.sh all 5 fixed.txt
#
# <fixes> is none, all, or a comma list of simplifyPaths, batchDraws,
# glowWithoutLayers, isolateRepaints. The script waits until the app logs a sample with
# exactly that setting, then traces. Open the result in https://ui.perfetto.dev and look
# at 1.raster: SurfaceFrame::Encode, Canvas::saveLayer, AllocateCommandBuffers.
# KILN_THRASH_TAPS works as in thrash_bench.sh.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=storm_common.sh
source "$here/storm_common.sh"

all=simplifyPaths,batchDraws,glowWithoutLayers,isolateRepaints
want="${1:?usage: $0 <fixes> [seconds] [output.txt] [impeller|skia]}"
[[ $want == all ]] && want=$all
seconds="${2:-5}"
out="${3:-thrash-${1//,/+}-$(date +%Y%m%d-%H%M%S).txt}"
case "${4:-impeller}" in
  impeller) pkg="$STORM_IMPELLER"; extra=() ;;
  skia) pkg="$STORM_SKIA"; extra=(--ez trace-skia true) ;;
  *) echo "engine must be impeller or skia" >&2; exit 2 ;;
esac

declare -A TAP=()
if [[ -z ${KILN_THRASH_TAPS:-} ]]; then
  echo "set KILN_THRASH_TAPS (printed by thrash_bench.sh)" >&2
  exit 2
fi
for pair in $KILN_THRASH_TAPS; do
  TAP[${pair%%=*}]="${pair#*=}"
  TAP[${pair%%=*}]="${TAP[${pair%%=*}]/,/ }"
done
tap() {
  # shellcheck disable=SC2086
  adb shell input tap ${TAP[$1]}
}

storm_require_device
adb shell am force-stop "$pkg"
storm_launch "$pkg" "${extra[@]}" --ez trace-systrace true
sleep 3
tap home
sleep 2
tap x8
for fix in ${want//,/ }; do
  [[ $fix == none ]] && continue
  tap "$fix"
  sleep 0.3
done

adb logcat -c
for _ in $(seq 1 30); do
  line=$(adb logcat -d -s flutter:I | grep -o 'KILN::Thrash::sample.*' | tail -1 || true)
  [[ -n $line ]] && break
  sleep 1
done
if [[ $line != *"level=8 fixes=$want xray=false"* ]]; then
  echo "app is not at the requested setting: ${line:-no sample}" >&2
  exit 1
fi

adb shell atrace --async_start -b 65536 -a "$pkg" gfx view sched freq >/dev/null
sleep "$seconds"
adb shell atrace --async_stop >"$out"
adb shell am force-stop "$pkg"

echo "trace: $out ($line)"
python3 -I "$here/thrash_trace_summary.py" "$out"
