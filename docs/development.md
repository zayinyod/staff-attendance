# 開発

## 実行環境

`.devcontainer/Dockerfile` からビルドしたイメージ [`staff-attendance-dev`] で、ホストから Django を実行する。リポジトリをコンテナの `/workspaces/staff_attendance` にマウントし、ホストのユーザー ID で実行する。

- ベースイメージは `mcr.microsoft.com/devcontainers/python:3-3.12-trixie` [Python 3.12、Debian 13、SQLite 3.46] とする。先頭の `3-` はイメージのメジャーバージョンを固定する。
- 依存パッケージのバージョンは `.devcontainer/requirements.txt` で固定する。
- `Dockerfile`・`requirements.txt` を変更した場合は `make build` でイメージを作り直す。
- devcontainer の features [Node] は Makefile の実行では適用されない。

## make タスク

`make help` で一覧を表示する。各タスクの用途は [README](../README.md#タスク) の表を参照する。

| 区分 | タスク | 補足 |
|---|---|---|
| イメージ | `build` / `rebuild` | `rebuild` はキャッシュを使わない |
| 検証 | `test` / `test-file` / `check` / `migrations-check` / `lint` | `lint` は実行のたびにコンテナへ flake8 を導入する。違反があると終了コード 1 を返す |
| DB | `migrations` / `migrate` / `seed` / `loaddata` / `db-backup` / `db-shell` / `createsuperuser` | `seed` は `migrate` と `loaddata` を続けて実行する |
| 実行 | `serve` / `shell` / `django-shell` / `collectstatic` | `serve` は 8000 番を公開する |
| Git | `switch` | DB を複製してからブランチを切り替える |

## DB

DB は `backend/data/db.sqlite3` に置く。配置先とバックアップ先は `.env` の `DB_PATH`・`DB_BACKUP_DIR` で変更できる。

- 旧コミットは `staff_attendance/db.sqlite3` を Git で追跡している。Git は ignore 対象のファイルを checkout 時に警告なく上書き・削除するため、DB はこの場所に置かない。
- Django プロジェクトのディレクトリは `staff_attendance/` から `backend/` に改名した。改名前のブランチへ切り替えると `backend/data/` の DB を参照できないため、両方のブランチで同じ DB を使う場合は `.env` の `DB_PATH` に固定のパスを指定する。
- ブランチの切り替えは `make switch BRANCH=<name>` を使用する。`git switch` を直接使う場合は、事前に `make db-backup` を実行する。
- `make db-backup` [`backup_db` コマンド] は SQLite のオンラインバックアップ API で複製するため、サーバーの稼働中でも実行できる。ファイル名は `db-YYYYmmdd-HHMMSS-ffffff.sqlite3` とし、直近 10 世代 [`--keep`] を超えた古い複製を削除する。出力先の表示はコンテナ内のパスとなる。
- コンテナに `sqlite3` コマンドがないため、`make db-shell` は Python 標準の `python -m sqlite3` で接続する。`manage.py dbshell` は使用できない。

## 静的ファイルの配信

ブラウザが変更前のファイルをキャッシュから読み込むことを防ぐため、環境ごとに以下の対策を取る。

| 環境 | 対策 | 実装 |
|---|---|---|
| 開発 [DEBUG=True] | `runserver` が静的ファイルの応答に `Cache-Control: no-cache` を付与する。未変更のファイルには 304 を返す | `attendance/management/commands/runserver.py`、`util/static_handlers.py` |
| 本番 [DEBUG=False] | ファイル名に内容のハッシュを付与して配信する。ES Modules の import 先もハッシュ付きの名前に書き換える | `util/storages.py` [ManifestStaticFilesStorage を継承] |

- DEBUG=False で起動する前に `make collectstatic` を実行し、`STATIC_ROOT` にファイルとマニフェストを生成する。未収集のファイルを参照するとページの描画時に例外となる。
- DEBUG=False では Django は静的ファイルを配信しない。本番の配信方法は未定義である。
- no-cache の導入前にブラウザが保存したファイルは、Ctrl+Shift+R で再読み込みするまで使われ続ける場合がある。

## テスト

`attendance/tests/` に置き、`make test` で実行する。

| ファイル | 対象 |
|---|---|
| `test_models.py` | モデルの文字列表現、一意制約、削除時の挙動 |
| `test_clock_calc.py` | 勤務時間・深夜勤務・残業の計算、日次・月次集計 |
| `test_views.py` | 各画面の表示、権限、入力の検証、ユーザー ID の再生成、テンプレートの構造、サイドバーの描画 |
| `test_workflow.py` | 有給の申請、承認画面の一覧・権限・一括処理・ロールバック、`PaidLeaveEntry`、`PaidLeave` の削除時の挙動 |
| `test_utils.py` | `IDGenerator`、`RoundCalculate`、`Now`、ショートカットキーの割り当て |
| `test_static_files.py` | no-cache の付与、`runserver` の差し替え、ハッシュ付きのファイル名と import の書き換え |
| `test_backup_db.py` | `backup_db` の複製・世代削除・DB 不在時の挙動 |

- テストは DEBUG=False で実行されるため、テストランナー [`util/test_runner.py`] がストレージを `StaticFilesStorage` に切り替える。
- `make lint` の違反は 0 件とする [PEP8 に準拠。1 行の最大長は 120 文字]。Django が自動生成する `migrations/` は対象外とする [`.devcontainer/.flake8`]

## Claude Code の設定 [.claude/]

| 種類 | 名前 | 内容 |
|---|---|---|
| hook | `check_syntax.sh` | ファイルの編集後に、拡張子に応じて構文を検査する |
| skill | `verify-implementation` | 実装完了時のテスト・構成チェック・静的検査 |
| skill | `update-docs` | 実装完了時のドキュメント更新と整合性チェック [`.claude/scripts/check_docs.py`] |
| skill | `theme-color` | Light / Dark の配色の決定と確認 |
| rule | `implementation-flow.md` | 実装完了時に上記 2 skill を実行する |
| rule | `theme-color.md` | CSS・テンプレートの編集時に `theme-color` skill を参照する |
