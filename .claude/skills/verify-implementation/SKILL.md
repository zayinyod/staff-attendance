---
name: verify-implementation
description: 実装の完了時 [完了報告の前] に使用する。テスト・Django の構成チェック・マイグレーションの作成漏れ・flake8 を実行し、結果の判定と失敗時の切り分け、テスト追加の要否、完了報告への記載方法を規定する。Python・テンプレート・静的ファイル・Makefile を変更した場合に適用する。
---

# 実装後の検証

構文は編集のたびに hook [`.claude/hooks/check_syntax.sh`] が検査している。本 skill は、時間のかかる検証を実装の完了時にまとめて行う。

## 手順

### 1. 検証を実行する

リポジトリのルートで、以下を順に実行する。

```bash
make test 2>&1 | grep -E "^(Ran|OK|FAILED)|^(FAIL|ERROR):"
make check
make migrations-check
make lint
```

| 項目 | 合格の条件 |
|---|---|
| `make test` | `OK`。件数は変更前より減っていないこと |
| `make check` | `System check identified no issues` |
| `make migrations-check` | `No changes detected`。モデルを変更した場合は `make migrations` で作成したマイグレーションを含める |
| `make lint` | 違反が 0 件 [出力なし、終了コード 0] であること。違反は出力のファイル名・行番号から特定して修正する。`migrations/` は対象外 [`.devcontainer/.flake8`] |

### 2. 失敗時に切り分ける

| 症状 | 確認すること |
|---|---|
| テストが失敗する | 失敗したテストを `make test-file T=...` で再実行し、テストの対象と変更箇所の関係を読んで、今回の変更による失敗か既存の不具合かを判定する |
| テンプレートの例外 | `{% url %}` の名前、`{% static %}` のパス、ブロック名の誤り |
| 静的ファイルの例外 [`ValueError: Missing staticfiles manifest entry`] | テストランナーの差し替え [`util/test_runner.py`] が効いているか |
| マイグレーションの差分 | 意図した変更か。意図しない場合はモデルの `default` / `choices` の変更を疑う |

既存の不具合と判断した場合は、修正せずにユーザーへ報告する。

### 3. テストの追加を判断する

次のいずれかに該当する変更は、テストを追加する。

- 業務ルール [計算・検証・権限] の追加・変更
- 画面の構造に関わる変更で、回帰を検出したいもの [e.g. 表がカード内にあること、特定のクラスが付くこと]
- 不具合の修正 [再現するテストを先に書く]

見た目のみの変更 [色・余白] はテストの対象とせず、撮影や目視で確認する [配色は `theme-color` skill]

### 4. 報告する

完了報告に、以下を記載する。

- テスト: 成功件数と追加件数
- 構成チェック・マイグレーション: 指摘の有無
- 静的検査: 違反の件数 [0 件であること]
- ブラウザでの確認が必要な事項 [見た目・操作]。確認時は Ctrl+Shift+R で再読み込みするよう添える。
