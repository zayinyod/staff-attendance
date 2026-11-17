# 仕様書

| 文書 | 内容 |
|---|---|
| [requirements.md](requirements.md) | 要件、画面設計、DB 設計 |
| [architecture.md](architecture.md) | レイヤー構成、ディレクトリ構成、共通処理、設定と環境変数 |
| [features.md](features.md) | 画面と URL、機能ごとの業務ルール、要件との差異 |
| [data-model.md](data-model.md) | モデル、コードマスタ、マイグレーションの経緯 |
| [frontend.md](frontend.md) | テンプレートの継承、CSS / JS、ショートカットキー、テーマカラー |
| [development.md](development.md) | 実行環境、make タスク、DB、静的ファイルの配信、テスト、Claude Code の設定 |

- 実装から読み取れる事実と決定事項のみを記載する。
- 実装を変更した場合は、`update-docs` skill に従って該当する文書を更新する。
