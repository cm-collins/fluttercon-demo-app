# Shared helpers for the Shader Storm scripts. Source this file; do not run it.
#
# Buttons are found by their on-screen text through `uiautomator dump`, once per session.
# Reading the screen turns on Flutter's accessibility tree, which adds work to every
# frame, so measured runs only replay the stored coordinates in a fresh app process.

STORM_ACTIVITY="dev.fluttercon.kiln.MainActivity"
STORM_SKIA="dev.fluttercon.kiln.skia"
STORM_IMPELLER="dev.fluttercon.kiln"

declare -gA STORM_TAP=()

storm_require_device() {
  command -v adb >/dev/null 2>&1 || { echo "adb is required and must be on PATH" >&2; exit 1; }
  local count
  count=$(adb devices | awk 'NR > 1 && $2 == "device"' | wc -l)
  if [[ $count -ne 1 ]]; then
    echo "expected exactly one connected device, found $count (set ANDROID_SERIAL to pick one)" >&2
    exit 1
  fi
}

storm_engine() {
  [[ $1 == "$STORM_SKIA" ]] && echo skia || echo impeller
}

# Prints "x y" for the centre of the smallest on-screen element whose text or
# content description has a line equal to $1. Prints nothing if there is none.
storm_find_text() {
  adb exec-out uiautomator dump /dev/tty 2>/dev/null | python3 -I -c '
import re, sys
target = sys.argv[1]
best = None
for node in re.findall(r"<node [^>]*>", sys.stdin.read()):
    attrs = dict(re.findall(r"([\w-]+)=\"([^\"]*)\"", node))
    labels = (attrs.get("text", "") + "&#10;" + attrs.get("content-desc", "")).split("&#10;")
    if target not in (label.strip() for label in labels):
        continue
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", attrs.get("bounds", ""))
    if not m:
        continue
    x1, y1, x2, y2 = map(int, m.groups())
    area = (x2 - x1) * (y2 - y1)
    if best is None or area < best[0]:
        best = (area, (x1 + x2) // 2, (y1 + y2) // 2)
if best:
    print(best[1], best[2])
' "$1"
}

# Waits up to 10 s for $1 to appear on screen and prints its centre.
storm_wait_text() {
  local found
  for _ in $(seq 1 20); do
    found=$(storm_find_text "$1")
    if [[ -n $found ]]; then
      echo "$found"
      return 0
    fi
    sleep 0.5
  done
  echo "could not find \"$1\" on screen" >&2
  return 1
}

storm_launch() {
  adb shell input keyevent KEYCODE_WAKEUP
  adb shell am start -W -n "$1/$STORM_ACTIVITY" "${@:2}" >/dev/null
}

# Finds the home entry, the grid-size chips and the reveal button on $1.
# Leaves the app stopped. KILN_TAPS can supply the coordinates instead, for example
# KILN_TAPS="home=600,450 c48=426,2047 c96=602,2047 c144=789,2047 reveal=612,2547"
storm_locate() {
  if [[ -n ${KILN_TAPS:-} ]]; then
    local pair
    for pair in $KILN_TAPS; do
      STORM_TAP[${pair%%=*}]="${pair#*=}"
      STORM_TAP[${pair%%=*}]="${STORM_TAP[${pair%%=*}]/,/ }"
    done
    return 0
  fi
  echo "locating buttons on $1 ..." >&2
  adb shell pm clear "$1" >/dev/null
  storm_launch "$1"
  STORM_TAP[home]=$(storm_wait_text "Shader Storm") || return 1
  # shellcheck disable=SC2086
  adb shell input tap ${STORM_TAP[home]}
  STORM_TAP[reveal]=$(storm_wait_text "REVEAL 48 EFFECTS") || return 1
  local n
  for n in 48 96 144; do
    STORM_TAP[c$n]=$(storm_wait_text "$n") || return 1
  done
  adb shell am force-stop "$1"
  local key out=""
  for key in home c48 c96 c144 reveal; do
    out+="$key=${STORM_TAP[$key]/ /,} "
  done
  echo "buttons: KILN_TAPS=\"${out% }\"" >&2
}

storm_tap() {
  # shellcheck disable=SC2086
  adb shell input tap ${STORM_TAP[$1]}
}

# Opens Shader Storm on a running app and selects $1 tiles.
storm_open() {
  sleep 3
  storm_tap home
  sleep 2
  storm_tap "c$1"
  sleep 1
}

# Waits up to 15 s for the next KILN::Storm::result line and prints its fields.
storm_wait_result() {
  local line
  for _ in $(seq 1 30); do
    line=$(adb logcat -d -s flutter:I | grep -o 'KILN::Storm::result.*' | tail -1)
    if [[ -n $line ]]; then
      echo "$line"
      return 0
    fi
    sleep 0.5
  done
  echo "no KILN::Storm::result in logcat" >&2
  return 1
}
