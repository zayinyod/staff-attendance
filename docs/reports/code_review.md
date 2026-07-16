# ソースコード評価レポート

**評価日**: 2026-05-19
**対象ブランチ**: feature/front-end

---

## 全体評価

DDD のアーキテクチャ（View → Usecase → Repository → Domain → Model）は概ね実装されており、基底クラスによるコードの共通化も適切。ただし、セキュリティ上のリスクや設計の一貫性に関する問題が複数存在する。

---

## 良い点

### アーキテクチャ設計

- View / Usecase / Repository / Domain / Model の層分けが守られている
- `BaseRepository`、`BaseFormView`、`BaseSuperUserView` の共通化が効いている
- `CustomLoginRequiredMixin` による認証制御が一元化されている

### セキュリティの基本

- `SECRET_KEY` は環境変数から取得
- パスワード最小長 9 文字のバリデーション（要件通り）
- CSRF ミドルウェアが有効

---

## 問題点

### セキュリティ

| 深刻度 | 場所 | 内容 |
|--------|------|------|
| **高** | `user/repositories.py:10` | `print(f"Saving User: {user_entry}")` が `UserDomain`（password フィールドを含む）を出力する。平文パスワードがログに漏洩する可能性がある |
| **中** | `settings.py:34` | `ALLOWED_HOSTS = []` は本番では全リクエストを拒否する |
| **中** | `clock/repositories.py:10-12` | クラス定義時に DB クエリを実行（後述） |

---

### バグ・ロジックの問題

#### 1. `UserEntryForm.clean_user_id()` が動作しない

`user/forms.py:38-42`

```python
def clean_user_id(self):
    cleaned_data = super().clean()          # 全フィールドの dict を返す
    cleaned_data["user_id"] = ...
    return cleaned_data                     # dict を返しているが、clean_X は単一値を返すべき
```

`user_id` はフォームの `fields` に存在しないためこのメソッドは呼ばれない。`user_id` の生成は `UserUseCase.create_user_entry()` 内で行われているので実害はないが、混乱を招くデッドコード。

---

#### 2. クラスレベルの DB クエリ

`clock/repositories.py:10-12`、`workflow/paid_leave/repositories.py:9`

```python
class ClockRepository(BaseRepository):
    code_master = CodeMasterRepository.clock_code_master()  # インポート時に DB クエリ実行
    to_in = code_master.get("to_in")
    to_out = code_master.get("to_out")
```

マイグレーション前やテスト環境で `DoesNotExist` エラーが発生する。`@classmethod` に変更して遅延評価にすることで解消できる。

---

#### 3. `user_id` 生成の競合状態

`user/usecases.py:10-13`

```python
while True:
    new_id = IDGenerator.create_id()
    if not cls.user_repository.user_id_exists(new_id):  # チェック
        return new_id                                     # ← 別リクエストが同 ID を取得する可能性
```

チェックと取得の間（TOCTOU）に別リクエストが同じ ID を取得し、重複登録が起きる可能性がある。

---

#### 4. `ApprovalView.post()` の文字列分割が脆弱

`workflow/views.py:24`

```python
_, id = key.split("_")   # "status_123" は OK だが "status_paid_leave_1" で ValueError
```

`key` にアンダースコアが 2 つ以上含まれる場合に `ValueError: too many values to unpack` が発生する。`key.split("_", 1)` で 1 回のみ分割するか、`key.removeprefix("status_")` を使うべき。

---

#### 5. `DashboardView` の日付バリデーション欠如

`clock/views/dashboard_view.py:12`

```python
date = request.GET.get("date")   # 不正な日付文字列がそのまま daily_summary に渡される
```

不正な日付文字列が渡されると `daily_summary` 内でランタイムエラーが発生する。入力値のバリデーションが必要。

---

#### 6. `IDGenerator` が数字のみでない

`util/id_generator.py:10`

```python
return get_random_string(6)  # 英数字混在
```

要件の「ユーザーID（6桁）」が数字を前提としている場合、実装と不一致になる。

---

### アーキテクチャの一貫性

#### Domain に DB モデルが混入

`clock/domains.py`、`workflow/paid_leave/domains.py`

```python
@dataclass
class ClockDomain:
    clock: CodeMaster = None    # ORM モデルをドメイン層に持ち込んでいる
    location: CodeMaster = None
```

ドメイン層が ORM モデルに依存しており、層の分離が崩れている。ドメインにはプリミティブ型または値オブジェクトを持たせるべき。

---

#### フォームがリポジトリに直接アクセス

`clock/forms/clock_form.py:8`

```python
class ClockForm(ModelForm):
    clock_status = ClockEntry.clock_repository  # Form → Repository の直接依存
```

Form はリポジトリではなく Usecase 経由でデータを取得すべき。

---

#### `BaseSuperUserView.post()` が未定義

`workflow/views.py:18-19`

```python
class ApprovalView(BaseSuperUserView):
    def post(self, request):
        if not request.user.is_superuser:   # 手動チェック
            return render(request, self.forbidden_template, status=403)
```

`get()` の superuser チェックは基底クラスで統一されているが、`post()` は各サブクラスで手動チェックが必要になっている。`BaseSuperUserView` に `post()` を追加して統一すべき。

---

### 設定

| 場所 | 内容 |
|------|------|
| `settings.py:141` | `STATICFIELDS_DIRS` → `STATICFILES_DIRS`（タイポ。静的ファイルが配信されない） |
| `settings.py:156-158` | `CORS_ALLOWED_ORIGINS` がハードコード。環境変数で制御すべき |

---

### テスト

`attendance/tests/tests.py` がプレースホルダーのみで実質テストなし。

---

## 優先対応の推奨

| 優先度 | 対応内容 | 場所 |
|--------|----------|------|
| 1 | `print` によるパスワード漏洩の削除 | `user/repositories.py:10`、`paid_leave/repositories.py:13` |
| 2 | `STATICFIELDS_DIRS` タイポ修正 | `settings.py:141` |
| 3 | クラスレベル DB クエリを遅延評価化 | `clock/repositories.py:10-12`、`paid_leave/repositories.py:9` |
| 4 | `UserEntryForm.clean_user_id()` の削除 | `user/forms.py:38-42` |
| 5 | `DashboardView` への日付入力バリデーション追加 | `clock/views/dashboard_view.py:12` |
| 6 | `ApprovalView.post()` の分割処理を堅牢化 | `workflow/views.py:24` |
| 7 | `BaseSuperUserView` に `post()` の superuser チェックを追加 | `util/base_superuser_view.py` |
