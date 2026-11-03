#!/usr/bin/env bash
# usage: render.sh page output.png
cd "$(dirname "$0")"
timeout 170 google-chrome --headless=new --use-angle=swiftshader --hide-scrollbars --force-device-scale-factor=2 --window-size=1280,720 --virtual-time-budget=60000 --screenshot="$PWD/$2" "file://$PWD/$1" 2>&1 | tail -1 | cut -c1-160
ls -la "$2" | cut -c24-
