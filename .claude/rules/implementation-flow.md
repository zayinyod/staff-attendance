# 実装完了時の流れ

コード・設定・テンプレート・静的ファイル・Makefile を変更した場合は、完了報告の前に以下を順に行う。

1. `verify-implementation` skill に従い、テスト・構成チェック・マイグレーション・静的検査を実行する。
2. `update-docs` skill に従い、仕様書 [`README.md`、`docs/`] を更新し、`.claude/scripts/check_docs.py` を実行する。
3. ユーザーのグローバル規約に従い、表形式で完了報告を行う。

- 構文は編集のたびに hook [`.claude/hooks/check_syntax.sh`] が検査する。エラーで差し戻された場合は、その場で修正する。
- 作業用ドキュメント [`memories/`] のみの変更では、本手順は不要である。
