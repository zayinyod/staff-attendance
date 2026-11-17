---
name: update-docs
description: 実装の完了時 [完了報告の前] に使用する。変更内容から更新すべき仕様書 [README.md、docs/] の文書と節を特定し、更新後に整合性チェック [.claude/scripts/check_docs.py] を実行する手順を規定する。コード・Makefile・設定・テンプレート・静的ファイルを変更した場合に適用する。
---

# 実装後のドキュメント更新

## 前提

- 仕様書は `README.md` と `docs/` 配下である。`memories/` は作業用ドキュメントであり、本 skill の対象外とする。
- 仕様書には決定事項のみを記載する。未決定事項を記載する場合は、ユーザーの承認を得た上で、文書の末尾に分離する。
- 実装から読み取れる事実を書く。計画や意図ではなく、コードの現状と一致させる。

## 手順

### 1. 変更したファイルを把握する

```bash
git status --short
git diff --stat {分岐元}...HEAD
```

### 2. 更新する文書を特定する

| 変更したもの | 更新する文書と節 |
|---|---|
| ファイルの追加・削除・移動 | `docs/architecture.md`「ディレクトリ構成」 |
| `util/` | `docs/architecture.md`「共通処理」 |
| `settings.py`、`.env.example` | `docs/architecture.md`「設定」 |
| `urls.py`、View、権限 | `docs/features.md`「画面と URL」と該当機能の節 |
| Form、Usecase [検証・計算・業務ルール] | `docs/features.md` の該当機能の節 |
| 要件にある機能の実装 | `docs/features.md`「要件との差異」から該当行を削除・修正する。`README.md`「構築状況」 |
| モデル、マイグレーション、フィクスチャ | `docs/data-model.md` |
| テンプレート、CSS、JS | `docs/frontend.md`。色は「テーマカラー」の採用色の表 |
| ショートカットキー | `docs/frontend.md`「ショートカットキー」 |
| `Makefile` | `README.md`「タスク」の表、`docs/development.md`「make タスク」 |
| DB の配置・バックアップ、静的ファイルの配信 | `docs/development.md` |
| テストファイルの追加 | `docs/development.md`「テスト」、`README.md`「構築状況」のテスト件数 |
| `.claude/` | `docs/development.md`「Claude Code の設定」 |

- `docs/requirements.md` は要件定義であり、実装に合わせて変更しない。要件の変更が必要な場合はユーザーに確認する。
- 同じ内容を複数の文書に書かない。詳細は docs/ に書き、`README.md` からはリンクする。

### 3. 整合性を検査する

```bash
python3 .claude/scripts/check_docs.py
```

| 検査 | 内容 |
|---|---|
| `tree` | ディレクトリ構成のパスが存在するか。子を列挙したディレクトリに、記載のない `.py` がないか |
| `make` | `Makefile` のタスクと `README.md` のタスク表の一致 |
| `env` | `settings.py` の環境変数と `.env.example`・`architecture.md` の一致 |
| `url` | `urls.py` の URL 名が `features.md` にあるか |
| `link` | 相対リンクの参照先 [ファイル・見出し] が存在するか |

- 全項目 OK になるまで修正する。
- 検査は記載の有無のみを見る。内容が実装と一致しているかは、変更箇所の文書を読み直して確認する。
- `tree` は Git 管理下のファイルを対象とする。新規ファイルは `git add` するまで検出されないため、手順 2 の表で漏れがないか確認する。

### 4. 報告する

完了報告の表に、更新した文書を行として含める。`check_docs.py` の結果を併記する。
