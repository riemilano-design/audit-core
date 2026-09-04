#!/bin/bash
# PostToolUse(Write|Edit)フック。
# data/配下のJSONファイルが編集されたときだけ scripts/validate-data.mjs を実行する。
# Node.jsが無い場合は案内メッセージを出すだけで、絶対に編集をブロックしない(常にexit 0)。
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$(cat)"

FILE_PATH="$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    ti = d.get("tool_input") or {}
    tr = d.get("tool_response") or {}
    print(ti.get("file_path") or tr.get("filePath") or "")
except Exception:
    print("")
' 2>/dev/null)"

case "$FILE_PATH" in
  */data/*.json)
    if command -v node >/dev/null 2>&1; then
      node "$SCRIPT_DIR/../validate-data.mjs"
    else
      echo "[hook] Node未インストールのためデータ検証をスキップしました(Phase 0で環境構築後に有効化)"
    fi
    ;;
esac

exit 0
