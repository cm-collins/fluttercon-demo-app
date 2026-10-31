#!/usr/bin/env bash
# Canvas Thrash at 8x: frame times with no fixes, each fix alone, and the fixes added
# top to bottom as on stage. Tracing off, X-ray off.
#
# usage: tool/benchmark/thrash_bench.sh [rounds] [output.csv] [impeller|skia]
#   tool/benchmark/thrash_bench.sh 3 thrash.csv
#
# Each round starts a fresh app process, opens Canvas Thrash, selects 8x and steps through
# the settings. For each setting it drops the first KILN::Thrash::sample line, keeps the
# next five and records their medians. Every sample names its own level and fixes; a sample
# that does not match the intended setting stops the run instead of being recorded.
#
# KILN_THRASH_TAPS skips the on-screen lookup, for example
# KILN_THRASH_TAPS="home=612,682 x8=1110,1974 simplifyPaths=612,2109 batchDraws=612,2211 glowWithoutLayers=612,2313 isolateRepaints=612,2415"
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=storm_common.sh
source "$here/storm_common.sh"

rounds="${1:-3}"
csv="${2:-thrash-$(date +%Y%m%d-%H%M%S).csv}"
case "${3:-impeller}" in
  impeller) pkg="$STORM_IMPELLER" ;;
  skia) pkg="$STORM_SKIA" ;;
  *) echo "usage: $0 [rounds] [output.csv] [impeller|skia]" >&2; exit 2 ;;
esac
engine=$(storm_engine "$pkg")

# Fix names in the order the screen lists them and the sample line prints them.
fixes=(simplifyPaths batchDraws glowWithoutLayers isolateRepaints)
labels=("Simplify paths" "Batch draws" "Glow without layers" "Isolate repaints")
configs=(
  none
  simplifyPaths
  batchDraws
  glowWithoutLayers
  isolateRepaints
  simplifyPaths,batchDraws
  simplifyPaths,batchDraws,glowWithoutLayers
  simplifyPaths,batchDraws,glowWithoutLayers,isolateRepaints
)
samples_kept=5

declare -A TAP=()

locate() {
  if [[ -n ${KILN_THRASH_TAPS:-} ]]; then
    local pair
    for pair in $KILN_THRASH_TAPS; do
      TAP[${pair%%=*}]="${pair#*=}"
      TAP[${pair%%=*}]="${TAP[${pair%%=*}]/,/ }"
    done
    return 0
  fi
  echo "locating buttons on $pkg ..." >&2
  adb shell am force-stop "$pkg"
  storm_launch "$pkg"
  TAP[home]=$(storm_wait_text "Canvas Thrash") || return 1
  # shellcheck disable=SC2086
  adb shell input tap ${TAP[home]}
  TAP[x8]=$(storm_wait_text "8×") || return 1
  local i
  for i in "${!fixes[@]}"; do
    TAP[${fixes[$i]}]=$(storm_wait_text "${labels[$i]}") || return 1
  done
  adb shell am force-stop "$pkg"
  local key out=""
  for key in home x8 "${fixes[@]}"; do
    out+="$key=${TAP[$key]/ /,} "
  done
  echo "buttons: KILN_THRASH_TAPS=\"${out% }\"" >&2
}

tap() {
  # shellcheck disable=SC2086
  adb shell input tap ${TAP[$1]}
}

# Prints "ui raster" medians of the samples for the current setting, or fails if a sample
# shows a different level or fix set.
measure() {
  local want=$1
  python3 -I - "$want" "$samples_kept" <<'EOF'
import re, statistics, subprocess, sys, time
want, keep = sys.argv[1], int(sys.argv[2])
pattern = re.compile(r"KILN::Thrash::sample level=(\d+) fixes=(\S+) xray=(\S+) uiP90Ms=([\d.]+) rasterP90Ms=([\d.]+)")
deadline = time.time() + 60
seen = []
while time.time() < deadline and len(seen) < keep + 1:
    out = subprocess.run(["adb", "logcat", "-d", "-s", "flutter:I"], capture_output=True, text=True).stdout
    seen = [m.groups() for m in pattern.finditer(out)]
    time.sleep(1)
if len(seen) < keep + 1:
    sys.exit(f"only {len(seen)} samples for {want} within 60 s")
for level, fixes, xray, _, _ in seen:
    if level != "8" or fixes != want or xray != "false":
        sys.exit(f"expected level=8 fixes={want} xray=false, got level={level} fixes={fixes} xray={xray}")
kept = seen[1 : keep + 1]
ui = statistics.median(float(s[3]) for s in kept)
raster = statistics.median(float(s[4]) for s in kept)
print(f"{ui:.1f} {raster:.1f}")
EOF
}

storm_require_device
locate

{
  echo "# device=$(adb shell getprop ro.product.model | tr -d '\r') api=$(adb shell getprop ro.build.version.sdk | tr -d '\r') engine=$engine level=8"
  echo "# commit=$(git -C "$here" rev-parse --short HEAD 2>/dev/null || echo unknown) date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "round,engine,fixes,ui_p90_ms,raster_p90_ms"
} >"$csv"

for round in $(seq 1 "$rounds"); do
  adb shell am force-stop "$pkg"
  storm_launch "$pkg"
  sleep 3
  tap home
  sleep 2
  tap x8
  declare -A on=()
  for config in "${configs[@]}"; do
    # Tap only the fixes whose state differs from the target.
    for fix in "${fixes[@]}"; do
      want_on=0
      [[ ",$config," == *",$fix,"* ]] && want_on=1
      if [[ $want_on -ne ${on[$fix]:-0} ]]; then
        tap "$fix"
        on[$fix]=$want_on
        sleep 0.3
      fi
    done
    adb logcat -c
    result=$(measure "$config")
    echo "$round,$engine,${config//,/+},${result% *},${result#* }" | tee -a "$csv"
  done
  unset on
  adb shell am force-stop "$pkg"
done

echo
echo "results: $csv"
python3 -I - "$csv" <<'EOF'
import csv, statistics, sys
rows = list(csv.DictReader(l for l in open(sys.argv[1]) if not l.startswith("#")))
order = list(dict.fromkeys(r["fixes"] for r in rows))
print(f"{'fixes':<62} {'ui p90 median (range)':<24} {'raster p90 median (range)':<24}")
for fixes in order:
    cells = []
    for key in ("ui_p90_ms", "raster_p90_ms"):
        v = [float(r[key]) for r in rows if r["fixes"] == fixes]
        cells.append(f"{statistics.median(v):5.1f} ({min(v):.1f}-{max(v):.1f})")
    print(f"{fixes:<62} {cells[0]:<24} {cells[1]:<24}")
EOF
