#!/bin/sh
# 営業資料の PDF を組む(HTML → Chrome headless)。はみ出しが 0 でなければ止まる。
set -e
D="$(cd "$(dirname "$0")" && pwd)"
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
P="${TMPDIR:-/tmp}/chrome-deck-$$"
OVF=$("$C" --headless=new --disable-gpu --user-data-dir="$P" --window-size=1123,794 --virtual-time-budget=3000 --dump-dom "file://$D/deck.html" 2>/dev/null | grep -o 'data-overflow="[^"]*"' | head -1)
echo "$OVF"
[ "$OVF" = 'data-overflow="none"' ] || { echo "はみ出しあり"; exit 1; }
"$C" --headless=new --disable-gpu --user-data-dir="$P" --no-pdf-header-footer --print-to-pdf="$D/AuditCore_ご紹介資料_2026-11-10.pdf" "file://$D/deck.html" 2>/dev/null
rm -rf "$P"
ls -la "$D"/*.pdf
