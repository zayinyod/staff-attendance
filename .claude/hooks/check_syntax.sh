#!/usr/bin/env bash
#
# PostToolUse hook [Edit / Write / MultiEdit]
# 編集したファイルの構文を拡張子に応じて検査する。
# エラー時は終了コード 2 で標準エラーに結果を出力し、Claude に差し戻す。
#
# 数秒以内で終わる検査のみを対象とする。テストと flake8 は verify-implementation skill で実行する。

set -uo pipefail

file_path="$(jq -r '.tool_input.file_path // empty')"
[[ -n "$file_path" && -f "$file_path" ]] || exit 0

case "$file_path" in
  */memories/*|*/node_modules/*|*/.next/*) exit 0 ;;
esac

run_check() {
  local output
  if ! output="$("$@" 2>&1)"; then
    printf '構文エラー: %s\n$ %s\n%s\n' "$file_path" "$*" "$output" >&2
    exit 2
  fi
}

case "$file_path" in
  *.py)
    run_check python3 -c 'import ast, sys; ast.parse(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1])' "$file_path"
    ;;
  *.js|*.mjs)
    if command -v node >/dev/null; then
      # ES Modules は拡張子 .js のままでは import 文を解釈できないため、モジュールとして検査する
      if grep -qE '^\s*(import|export)\s' "$file_path"; then
        run_check node --input-type=module --check < "$file_path"
      else
        run_check node --check "$file_path"
      fi
    fi
    ;;
  *.sh)
    run_check bash -n "$file_path"
    if command -v shellcheck >/dev/null; then
      run_check shellcheck "$file_path"
    fi
    ;;
  *.json)
    run_check jq empty "$file_path"
    ;;
esac

exit 0
