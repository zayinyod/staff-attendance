#!/usr/bin/env bash
#
# HTML 断片を Light / Dark で撮影し、左右に並べた 1 枚の画像として出力する。
#
# 稼働中の開発サーバーから CSS を読み込み、darkmode-js で Dark Mode を再現する。
# 撮影には WSL から Windows 側の Edge [headless] を使う。
#
# Usage:
#   capture_theme.sh -f FRAGMENT -o OUTPUT [-c CSS]... [-W WIDTH] [-H HEIGHT] [-u BASE_URL]
#
#   -f  <body> 内に置く HTML 断片のファイル
#   -o  出力する PNG のパス
#   -c  読み込む CSS [STATIC_URL からの相対パス。e.g. css/base.css]。複数指定可
#   -W  撮影幅 [既定: 700]
#   -H  撮影高さ [既定: 500]
#   -u  開発サーバーの URL [既定: http://localhost:8000]

set -euo pipefail

EDGE="/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
WINDOWS_WORK_DIR="/mnt/c/Temp/capture_theme"
DARKMODE_JS="https://cdn.jsdelivr.net/npm/darkmode-js@1.5.7/lib/darkmode-js.min.js"
# static/js/darkmode.js と同じ背景色を指定する
PAGE_BACKGROUND="#e1e1d7"

fragment=""
output=""
width=700
height=500
base_url="http://localhost:8000"
stylesheets=()

usage() {
  sed -n '3,17p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

while getopts "f:o:c:W:H:u:" option; do
  case "$option" in
    f) fragment="$OPTARG" ;;
    o) output="$OPTARG" ;;
    c) stylesheets+=("$OPTARG") ;;
    W) width="$OPTARG" ;;
    H) height="$OPTARG" ;;
    u) base_url="$OPTARG" ;;
    *) usage ;;
  esac
done

[[ -n "$fragment" && -n "$output" ]] || usage
[[ -f "$fragment" ]] || { echo "HTML 断片が見つからない: $fragment" >&2; exit 1; }
[[ -x "$EDGE" ]] || { echo "Edge が見つからない: $EDGE" >&2; exit 1; }
curl -s -o /dev/null -m 5 "$base_url/" \
  || { echo "開発サーバーに接続できない: $base_url [make serve で起動する]" >&2; exit 1; }

page_dir="$(mktemp -d)"
mkdir -p "$WINDOWS_WORK_DIR"
server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then kill "$server_pid" 2>/dev/null || true; fi
  rm -rf "$page_dir"
  [[ -n "${port:-}" ]] && rm -rf "$WINDOWS_WORK_DIR"/profile-*-"$port"
  return 0
}
trap cleanup EXIT

links=""
for stylesheet in "${stylesheets[@]}"; do
  links+="<link rel=\"stylesheet\" href=\"$base_url/static/$stylesheet\">"
done

for mode in light dark; do
  enabled=$([[ "$mode" == dark ]] && echo true || echo false)
  cat > "$page_dir/$mode.html" <<HTML
<!doctype html>
<html><head><meta charset="utf-8">$links
<script>localStorage.setItem('darkmode', '$enabled')</script>
</head><body>
$(cat "$fragment")
<script src="$DARKMODE_JS"></script>
<script>new Darkmode({ backgroundColor: '$PAGE_BACKGROUND', time: '0s' }).showWidget();</script>
</body></html>
HTML
done

port="$(python3 -c 'import socket; s = socket.socket(); s.bind(("", 0)); print(s.getsockname()[1])')"
python3 -m http.server "$port" --directory "$page_dir" >/dev/null 2>&1 &
server_pid=$!
for _ in $(seq 20); do
  curl -sf -o /dev/null "http://localhost:$port/light.html" && break
  python3 -c 'import time; time.sleep(0.2)'
done

captured=()
for mode in light dark; do
  # プロファイルを分け、localStorage の値を撮影ごとに独立させる
  timeout 60 "$EDGE" --headless --disable-gpu --hide-scrollbars \
    --user-data-dir="C:\\Temp\\capture_theme\\profile-$mode-$port" \
    --virtual-time-budget=3000 --window-size="$width,$height" \
    --screenshot="C:\\Temp\\capture_theme\\$mode-$port.png" \
    "http://localhost:$port/$mode.html" >/dev/null 2>&1 || true
  [[ -f "$WINDOWS_WORK_DIR/$mode-$port.png" ]] || { echo "$mode の撮影に失敗した" >&2; exit 1; }
  mv "$WINDOWS_WORK_DIR/$mode-$port.png" "$page_dir/$mode.png"
  captured+=("$page_dir/$mode.png")
done

mkdir -p "$(dirname "$output")"
python3 - "$output" "${captured[@]}" <<'PYTHON'
import sys
from PIL import Image

output, *paths = sys.argv[1:]
images = [Image.open(path) for path in paths]
combined = Image.new("RGB", (sum(image.width for image in images), max(image.height for image in images)))
offset = 0
for image in images:
    combined.paste(image, (offset, 0))
    offset += image.width
combined.save(output)
PYTHON

echo "撮影した [左: Light / 右: Dark]: $output"
