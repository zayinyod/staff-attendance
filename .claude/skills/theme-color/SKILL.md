---
name: theme-color
description: Django テンプレートの画面で配色 [文字色・背景色・枠線・リンク色] を追加・変更する際に使用する。darkmode-js の反転方式を前提に、Light / Dark 両方の色の決定、コントラスト比の検証、反転の対象外となる指定の検出、両モードの撮影確認までの手順を規定する。staff_attendance/attendance/static/css/ 配下の CSS、またはテンプレートで色に関わるクラスを編集する場合に適用する。
---

# テーマカラー [Light / Dark] の調整

## 前提の確認

作業前に `README.md` の「テーマカラー」節を読む。反転方式・背景色・上書きの方式・コントラスト比の基準はそちらに定義されている。本 skill は手順と判断基準のみを示す。

要点:
- Dark Mode は darkmode-js が画面全体を反転して表示する。Dark で見える色は「指定した色の反転色」となる。
- 無彩色 [白・黒・灰] は反転しても自然に見えるため、上書きは不要である。
- 有彩色は反転で色相が変わる [赤 → シアン、青 → 橙]。色相を保つ必要がある場合のみ、`body.darkmode--activated` で上書きする。

スクリプトは `.claude/skills/theme-color/scripts/` にある。以下はリポジトリのルートで実行する。

## 手順

### 1. 色の役割を決める

色ごとに、反転後の色相の変化を許容するかを判断する。

| 区分 | 例 | 対応 |
|---|---|---|
| 意味を持つ色 | エラー・警告 [赤]、土日 [赤 / 青] | Dark で同じ色相に見えるよう上書きする |
| 装飾の色 | リンクのアクセント色 | 反転後の色が両モードで読みやすければ許容してよい。判断に迷う場合はユーザーに確認する |

### 2. 値を算出する

Light で表示する色と、Dark で表示したい色を決め、`pair` で検証する。

```bash
python3 .claude/skills/theme-color/scripts/theme_color.py pair b3261e ff6b61              # ページの背景上
python3 .claude/skills/theme-color/scripts/theme_color.py pair ff8a8a b71c1c --on table   # 表のセル上
```

- 全行が OK [4.5:1 以上] になるまで色を調整する。NG のまま採用しない。
- `--on` に該当しない背景の上に置く場合は、`--background` で Light の背景色を指定する。
- 出力の「darkmode--activated に指定する値」を Dark の上書きに使う。

### 3. CSS に記述する

```css
:root {
  --{file}_{role}: #b3261e;  /* 背景 #e1e1d7 に対する色 */
}

body.darkmode--activated {
  --{file}_{role}: #00949e;  /* 反転後 #ff6b61 */
}

.selector {
  color: var(--{file}_{role});
}
```

- 色は変数で指定し、変数名は `--{ファイル名}_{役割}` とする [e.g. `--timesheets_sunday`、`--panel_link_on_table`]。`base.css` の共通色は `--{役割}` とする [e.g. `--alert_color`]
- コメントには、Light の値に背景色を、Dark の値に反転後の色を記す。
- `isolation: isolate` で反転を止めて色を固定する方式は使わない。Light / Dark で同じ見た目になる。
- 反転後の色相の変化を許容した変数には、同じ行に `/* theme-color: allow */` を付ける [lint の対象外となる]
- 既存の CSS ファイルの改行コードは LF である [`.gitattributes` で固定]

### 4. 検査する

```bash
python3 .claude/skills/theme-color/scripts/theme_color.py lint staff_attendance/attendance/static/css
```

- 今回変更した箇所が一覧に出ないことを確認する。既存分は対象外とし、修正する場合はユーザーの承認を得る。
- `isolation: isolate` が残っている要素は、Light / Dark で同じ色となる。変更対象の画面で使われている場合は報告する。

### 5. 両モードを撮影して確認する

開発サーバー [`make serve`] の稼働中に、確認したい部分の HTML 断片を用意して撮影する。

```bash
.claude/skills/theme-color/scripts/capture_theme.sh \
  -f {scratchpad}/fragment.html -c css/base.css -c css/panel.css -o {scratchpad}/capture.png
```

- `-c` には、対象のテンプレートが読み込む CSS を同じ順序で指定する。
- 出力画像 [左: Light / 右: Dark] を Read で確認し、色相・コントラスト・枠線の有無を目視する。
- HTML 断片は scratchpad に置き、リポジトリに保存しない。

### 6. ユーザーに確認を依頼する

ブラウザに変更前の CSS が残っている場合があるため、Ctrl+Shift+R で再読み込みした上で、Light / Dark の両方を確認するよう依頼する。

「表示が変わらない」「要素が消えた」と報告された場合は、まず次を確認する。
- 開発サーバーが新しい CSS を返しているか [`curl -s http://localhost:8000/static/css/{file}.css`]
- ブラウザのキャッシュ [Ctrl+Shift+R で解消するか]

### 7. 報告する

ユーザーのグローバル規約に従い、表形式で完了報告を行う。採用した色は、Light の値・Dark の上書き値・反転後の色・コントラスト比を表で示す。
