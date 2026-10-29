#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <package-id> [output-file]" >&2
  exit 2
fi

package_id="$1"
output_file="${2:-renderer-evidence-${package_id}.log}"

command -v adb >/dev/null 2>&1 || {
  echo "adb is required and must be on PATH" >&2
  exit 1
}

adb get-state >/dev/null
adb logcat -c
adb shell am force-stop "$package_id"
adb shell monkey -p "$package_id" 1 >/dev/null
sleep 2

{
  echo "package=$package_id"
  echo "captured=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  adb logcat -v threadtime -d | rg -i 'impeller|vulkan|opengl|skia|renderer'
} >"$output_file"

echo "Renderer evidence written to $output_file"
