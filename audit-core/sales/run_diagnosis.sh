#!/bin/sh
# 無償診断の 1 本分: 書類(有価証券報告書)の ZIP と文章の .txt から、お客さま向けの診断レポート(HTML と PDF)を作る。
# 0 USD(鍵を全部外して走る。生成 AI は呼ばない)。文章・添え書き・出力先は repo の外に置く(お客さまの文章を repo に入れないため。repo は公開)。
# 使い方(audit-core の中で): sh sales/run_diagnosis.sh <書類.zip> <文章.txt> <出力先のフォルダ> [添え書き.txt]
set -eu
if [ $# -lt 3 ] || [ $# -gt 4 ]; then
  echo "使い方: sh sales/run_diagnosis.sh <書類.zip> <文章.txt> <出力先のフォルダ> [添え書き.txt]" >&2; exit 2
fi
ZIP=$1; TXT=$2; OUT=$3; COVER=${4:-}
[ -f adapters/xbrl/verify_document.py ] || { echo "audit-core の中で走らせてください" >&2; exit 2; }
[ -f "$ZIP" ] || { echo "書類の ZIP が在りません: $ZIP" >&2; exit 2; }
[ -s "$TXT" ] || { echo "文章のファイルが在りません(か空です): $TXT" >&2; exit 2; }
[ -z "$COVER" ] || [ -f "$COVER" ] || { echo "添え書きのファイルが在りません: $COVER" >&2; exit 2; }
REPO=$(git -C .. rev-parse --show-toplevel 2>/dev/null || (cd .. && pwd -P))
abs_file() { (cd "$(dirname "$1")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$1")"); }
for f in "$TXT" ${COVER:+"$COVER"}; do
  [ ! -L "$f" ] || { echo "文章と添え書きは、リンクでなく実体のファイルを置いてください: $f" >&2; exit 2; }
  case "$(abs_file "$f")" in "$REPO"/*) echo "文章と添え書きは repo の外に置いてください: $f" >&2; exit 2;; esac
done
# 出力先: 親のフォルダは在ること(新しく作るのは 1 段だけ)。作る前に、道筋を確かめる。
if [ -d "$OUT" ]; then
  OUTABS=$(cd "$OUT" && pwd -P)
else
  PARENT=$(cd "$(dirname "$OUT")" 2>/dev/null && pwd -P) || { echo "出力先を作れません(親のフォルダを先に作ってください): $OUT" >&2; exit 2; }
  OUTABS="$PARENT/$(basename "$OUT")"
fi
case "$OUTABS/" in "$REPO"/*) echo "出力先は repo の外にしてください: $OUTABS" >&2; exit 2;; esac
case "$OUTABS" in *[#%?]*) echo "出力先の道筋に # % ? を入れないでください(PDF を作れません): $OUTABS" >&2; exit 2;; esac
LABELS="$HOME/.cache/audit-core/edinet-taxonomy/2025-11-01"
RUN="env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY -u GOOGLE_API_KEY -u GEMINI_API_KEY -u EDINET_API_KEY -u EDINETDB_API_KEY python3 -B"
# 組む道具の約束を先に確かめる(外れたら、何も作らずにここで止まる)
$RUN sales/customer_report_selfcheck.py
MADE=0
if [ ! -d "$OUT" ]; then
  mkdir "$OUT" || { echo "出力先を作れません: $OUT" >&2; exit 2; }
  MADE=1
fi
# 途中で止まったら、自分が作った 1 段が空のときだけ消す(中身が在れば残す)
trap 'rc=$?; if [ "$rc" -ne 0 ] && [ "$MADE" -eq 1 ]; then rmdir "$OUTABS" 2>/dev/null || true; fi; exit "$rc"' EXIT
$RUN -m adapters.xbrl.verify_document --zip "$ZIP" --text "$TXT" --profile P33E --out "$OUT/out.json"
$RUN -m adapters.xbrl.report_customer --in "$OUT/out.json" --out "$OUT/report.md" --labels "$LABELS" --zip "$ZIP" --full
rm -f "$OUTABS/report.html" "$OUTABS/report.pdf"
if [ -n "$COVER" ]; then
  $RUN sales/customer_report_build.py "$OUT/report.md" "$OUT/report.html" "$COVER"
else
  $RUN sales/customer_report_build.py "$OUT/report.md" "$OUT/report.html"
fi
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ -x "$CHROME" ]; then
  PROF=$(mktemp -d "$OUTABS/chrome.XXXXXX")
  "$CHROME" --headless=new --disable-gpu --user-data-dir="$PROF" --no-pdf-header-footer --print-to-pdf="$OUTABS/report.pdf" "file://$OUTABS/report.html" 2>/dev/null || true
  rm -rf "$PROF"
  if [ -s "$OUTABS/report.pdf" ]; then
    echo "できたもの: $OUTABS/report.pdf(送る用)・report.html・report.md・out.json"
  else
    echo "PDF を作れませんでした。report.html は在ります(Chrome で開いて PDF に保存できます): $OUTABS/report.html" >&2; exit 1
  fi
else
  echo "Chrome が無いので PDF は作っていません。できたもの: $OUTABS/report.html・report.md・out.json"
fi
