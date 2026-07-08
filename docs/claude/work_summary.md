# 修正作業サマリー

**作業日**: 2026-05-19
**対象ブランチ**: feature/front-end

---

## 1. ソースコード評価

`docs/requirements.md` および `docs/README.md` を参照してソースコードを評価した。
評価結果の詳細は [`code_review.md`](code_review.md) を参照。

### 主な指摘事項（優先度順）

| 優先度 | 種別 | 内容 |
|--------|------|------|
| 高 | セキュリティ | `print` によるパスワード平文ログ出力 |
| 高 | バグ | `ClockRepository` 等のクラスレベル DB クエリ（後述） |
| 中 | バグ | `BaseFormView` の IntegrityError 処理でトランザクション破壊 |
| 中 | 設定 | `STATICFIELDS_DIRS` のタイポ（静的ファイル未配信） |
| 低 | 設計 | Domain 層に ORM モデルが混入、Form からリポジトリへの直接依存 |

---

## 2. テストコード作成

`attendance/tests/` 配下に 4 ファイルを新規作成（合計 69 テスト）。

```
attendance/tests/
├── test_utils.py       # IDGenerator, RoundCalculate, Now（DB不要）
├── test_models.py      # User, Clock, CodeMaster モデル制約
├── test_clock_calc.py  # ClockCalculate 打刻計算ビジネスロジック
└── test_views.py       # Login / UserEntry / Clock / Dashboard / Approval
```

---

## 3. 修正実施

### 3-1. クラスレベル DB クエリの除去

**問題**

`manage.py test` 起動時、Django の `check` コマンドが URL を import するタイミングで
`ClockRepository` のクラス定義が実行され、DB にデータがない状態でクエリが走り
`CodeMaster.DoesNotExist` が発生してテストが起動できなかった。

```
clock/repositories.py → ClockRepository クラス定義
  code_master = CodeMasterRepository.clock_code_master()  ← ここで DB クエリ
```

同様の問題が `PaidLeaveRepository`・`PaidLeaveEntry` にも存在した。

**修正内容**

クラス属性として持っていた DB クエリ結果をクラスメソッドに移動し、呼び出し時に実行されるよう変更（遅延評価化）。

| ファイル | 変更前 | 変更後 |
|----------|--------|--------|
| `clock/repositories.py` | クラス属性 `code_master`, `to_in`, `to_out` | `_clock_codes()` クラスメソッド |
| `clock/forms/clock_form.py` | クラス属性 `clock_status`, `to_in`, `to_out` | `initialize_fields()` 内で `_clock_codes()` を呼ぶ |
| `workflow/paid_leave/repositories.py` | クラス属性 `code_master` | `_workflow_codes()` クラスメソッド |
| `workflow/paid_leave/usecases.py` | クラス属性 `pending_status` | `create_request()` 内で `_workflow_codes()` を呼ぶ |

あわせて各ファイルの `print` 文（パスワード等の情報をログ出力していた箇所）も削除。

---

### 3-2. IntegrityError 発生時のトランザクション破壊

**問題**

`BaseFormView.post()` が `IntegrityError` を `except` で捕捉した後、
フォーム再描画のために DB クエリを発行しようとするが、
IntegrityError によってトランザクションが破壊された状態のため
`TransactionManagementError` が発生していた。

これはテスト環境（Django TestCase がトランザクション内にラップ）だけでなく、
本番環境でも同様の挙動になる実装上の問題。

**修正内容**

`util/base_form_view.py` の `form_valid()` 呼び出しを `transaction.atomic()` で囲み、
savepoint を作成することで IntegrityError を隔離した。

```python
# 修正前
try:
    self.form_valid(form)
    return redirect(self.success_url)
except IntegrityError as e:
    form.add_error(None, "This record already exists.")

# 修正後
try:
    with transaction.atomic():       # savepoint を作成
        self.form_valid(form)
    return redirect(self.success_url)
except IntegrityError as e:
    form.add_error(None, "This record already exists.")
```

---

### 3-3. テストコード修正（ClockCalculate mock の後処理）

**問題**

`TestClockCalculate.setUp()` で `ClockCalculate.clock_repository` をモックに差し替えた後、
`tearDown()` で元に戻していなかったため、後続の `TestDashboardView` テストが
モックを使い続けて `TypeError: combine() argument 1 must be datetime.date, not MagicMock`
が発生していた。

**修正内容**

`test_clock_calc.py` に `tearDown()` を追加し、テスト後にリポジトリを元に戻すよう修正。

```python
def setUp(self):
    self._original_repo = ClockCalculate.clock_repository
    ClockCalculate.clock_repository = MagicMock()

def tearDown(self):
    ClockCalculate.clock_repository = self._original_repo  # 追加
```

---

## 4. 最終テスト結果

```
Ran 69 tests in 11.504s

OK
```

| テストファイル | テスト数 | 結果 |
|----------------|--------|------|
| `test_utils.py` | 15 | 全通過 |
| `test_models.py` | 13 | 全通過 |
| `test_clock_calc.py` | 19 | 全通過 |
| `test_views.py` | 22 | 全通過 |
| **合計** | **69** | **全通過** |

---

## 5. 残課題

`code_review.md` で指摘した事項のうち、今回未対応のもの。

| 項目 | 内容 |
|------|------|
| `settings.py` タイポ | `STATICFIELDS_DIRS` → `STATICFILES_DIRS` |
| UserDomain のパスワードフィールド | `user_id` 生成ロジックの整理（`clean_user_id` の削除） |
| `user_id` 生成の競合状態 | TOCTOU 問題（同時登録時に重複 ID が発行される可能性） |
| `DashboardView` 入力バリデーション | `date` クエリパラメータに不正値を渡した場合の未処理 |
| `ApprovalView.post()` の文字列分割 | `key.split("_")` が複数アンダースコアで失敗する可能性 |
| Domain 層の設計 | ORM モデルの混入、Form からリポジトリへの直接依存 |
| テスト拡充 | PaidLeave の申請・承認フロー、ワークフロー操作のテスト |
