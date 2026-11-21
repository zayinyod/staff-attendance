# Staff Attendance

勤怠入力、ワークフロー申請が可能な勤怠管理のSaaSシステム。

## システム

| 区分 | 構成 |
|------|------|
| Environment | Docker / devcontainer（Python 3.12、Debian 13） |
| Back-end | Python + Django 5.2 LTS |
| Front-end | Next.js 16 + React 19 + Tailwind CSS 4 |
| Database | SQLite |

依存パッケージのバージョンは `.devcontainer/requirements.txt` で固定する。Django は LTS の
5.2 系を使用し、次の LTS である 6.2 の公開後に更新する。

## フロントエンドの方針

Django テンプレートと Next.js が併存する状態を解消するため、二段階で進める。

1. 第一段階：Django テンプレートで機能を完成させる。新規の画面実装は Django テンプレート側に
   集約する。Next.js、Django REST Framework、django-cors-headers は撤去せず保持する。
2. 第二段階：機能が出揃った時点で API 化を行い、Next.js を SPA として構築する。
   Django テンプレートは段階的に廃止する。

現在は第一段階である。Next.js は導入のみで、`create-next-app` のテンプレートから未着手。

## 開発環境

### セットアップ

`.env.example` を `.env` として複製し、`SECRET_KEY` を設定する。

```bash
cp .env.example .env
```

devcontainer を使用する場合は VS Code から開く。ホストから直接操作する場合は
`Makefile` のタスクを使用する。

```bash
make build   # 開発用イメージをビルドする
make seed    # 初期データを投入する（migrate + loaddata）
make serve   # 開発サーバーを起動する（http://localhost:8000）
```

`make seed` は以下を投入する。

- `CodeMaster`：打刻・勤務場所・ワークフローのステータス（マイグレーション `0016`）
- `Department`：所属部署（`attendance/fixtures/departments.json`）

`CodeMaster` は各機能が前提とする必須マスタのためマイグレーションで投入する。
`Department` は組織固有のデータのため、フィクスチャとして環境ごとに置き換える。

### タスク

`make help` で一覧を表示する。

| タスク | 内容 |
|--------|------|
| `make help` | タスク一覧を表示する |
| `make build` | 開発用イメージをビルドする |
| `make rebuild` | キャッシュを使わずにイメージを再ビルドする |
| `make test` | テストを実行する |
| `make test-file T=<path>` | 指定したテストのみ実行する |
| `make check` | Django の構成チェックを実行する |
| `make migrations-check` | 未作成のマイグレーションがないか確認する |
| `make migrations` | マイグレーションを作成する |
| `make migrate` | マイグレーションを適用する |
| `make seed` | 新規環境の初期データを投入する（migrate + loaddata） |
| `make loaddata` | 所属部署のフィクスチャを読み込む |
| `make db-backup` | DB を `backups/db/` に複製する（直近 10 世代を保持） |
| `make switch BRANCH=<name>` | DB を複製してからブランチを切り替える |
| `make createsuperuser` | 管理ユーザーを作成する（対話形式） |
| `make db-shell` | SQLite に接続する。`SQL="..."` を指定すると 1 文だけ実行する |
| `make lint` | flake8 で静的検査を実行する |
| `make serve` | 開発サーバーを起動する（http://localhost:8000） |
| `make shell` | コンテナのシェルを起動する |
| `make django-shell` | Django シェルを起動する |
| `make collectstatic` | 静的ファイルを `STATIC_ROOT` に収集する |
| `make clean` | `__pycache__` を削除する |

`make lint` は違反を検出すると flake8 の仕様により終了コード 1 を返す。

## 仕様書

実装の詳細は [docs/](docs/README.md) に記載する。

| 文書 | 内容 |
|------|------|
| [requirements.md](docs/requirements.md) | 要件、画面設計、DB 設計 |
| [architecture.md](docs/architecture.md) | レイヤー構成、ディレクトリ構成、設定と環境変数 |
| [features.md](docs/features.md) | 画面と URL、業務ルール、要件との差異 |
| [data-model.md](docs/data-model.md) | モデル、コードマスタ、マイグレーション |
| [frontend.md](docs/frontend.md) | テンプレート、CSS / JS、ショートカットキー、テーマカラー |
| [development.md](docs/development.md) | 実行環境、DB、静的ファイルの配信、テスト |

## 構築状況

### バックエンド

| 機能 | 状態 |
|------|------|
| ドメインモデルの作成 | 完了 |
| ログイン、ログアウト | 完了 |
| ユーザー登録 | 完了 |
| 打刻（IN / OUT、勤務場所、休憩時間） | 完了 |
| 日次集計 | 完了 |
| 月次集計 | 完了 |
| 有給申請、承認 | 完了 |
| 打刻修正、交通費、勤怠締め | モデルのみ。Usecase / View は未実装 |
| 承認ルート、有給の付与・管理、給与集計 | 未着手 |
| テスト | 150 件 |

### フロントエンド

| 項目 | 状態 |
|------|------|
| Next.js の導入 | 完了 |
| 画面実装 | 未着手（`create-next-app` のテンプレートのまま） |
| API（Django REST Framework） | 未着手（パッケージの導入のみ） |
