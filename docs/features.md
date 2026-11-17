# 機能

## 画面と URL

| URL | 名前 [`name=`] | 画面 | 権限 | View |
|---|---|---|---|---|
| `/` | `login` | ログイン | - | `user.views.Login` |
| `/logout/` | `logout` | ログアウト [画面なし] | - | `user.views.Logout` |
| `/user_entry/` | `user_entry` | ユーザー登録 | - | `user.views.UserEntry` |
| `/clock/` | `clock` | 打刻 | 認証済み | `clock.views.ClockView` |
| `/clock/dashboard/` | `dashboard` | ダッシュボード [日次集計] | 認証済み | `clock.views.DashboardView` |
| `/clock/timesheets/` | `timesheets` | 勤怠一覧 [月次集計] | 認証済み | `clock.views.TimesheetsView` |
| `/workflow/` | `select` | ワークフロー選択 | スーパーユーザー | `workflow.views.WorkflowSelectView` |
| `/workflow/request/` | `request` | 申請メニュー | 認証済み | `workflow.views.RequestView` |
| `/workflow/request/paid_leave/` | `paid_leave_request` | 有給申請 | 認証済み | `workflow.paid_leave.views.PaidLeaveRequestView` |
| `/workflow/approval/` | `approval` | 承認 | スーパーユーザー | `workflow.views.ApprovalView` |
| `/admin/` | - | Django 管理画面 | スタッフ | Django 標準 |

- 未認証で「認証済み」「スーパーユーザー」の画面にアクセスすると、ログイン画面へリダイレクトする。
- スーパーユーザー向けの画面に一般ユーザーがアクセスすると、`403.html` を status 403 で返す。
- サイドバーの WORKFLOW は、スーパーユーザーには `select`、一般ユーザーには `request` へのリンクとなる。

## ユーザー

### ログイン / ログアウト

- `username` と `password` で認証する。成功時は `dashboard` へ、失敗時は「Your login details are incorrect.」を表示する。
- ログアウトはセッションを破棄して `/` へリダイレクトする。

### ユーザー登録

| 項目 | 内容 |
|---|---|
| Form | `UserEntryForm` [`UserCreationForm` を継承]。名前・所属部署・メールアドレス・パスワード [確認入力あり] を入力する |
| ユーザー ID | 数字 6 桁をランダムに生成する [`IDGenerator`]。登録時に一意制約違反を検知した場合は再生成し、最大 5 回まで試行する |
| 保存 | `UserRepository.save` は `force_insert=True` で保存する。ユーザー ID が自動採番でない主キーのため、既存ユーザーの上書きを防ぐ |
| 失敗時 | ユーザー ID 以外の一意制約違反 [ユーザー名の重複] は「Username already exists.」を表示する |
| 成功時 | `login` へリダイレクトする |

## 打刻

### 打刻の登録 [`/clock/`]

| 項目 | 内容 |
|---|---|
| Form | `ClockForm`。日付・時刻・IN / OUT・休憩時間・勤務場所を入力する |
| 初期値 | 当日の IN 打刻がある場合は OUT を選択し、休憩時間と勤務場所を IN 打刻の値で埋める。ない場合は IN を選択する |
| 休憩時間 | 0.00〜24.00、0.25 刻み。刻みに合わない値はエラーとする。既定値は 1.00 |
| 検証 | 同じ日付に IN 打刻がない場合、OUT 打刻は登録できない |
| 重複 | 同じユーザー・日付・打刻種別の重複は登録できない [一意制約。「This record already exists.」] |
| 送信時 | `confirm.js` で確認ダイアログを表示する |

### 勤務時間の計算 [`ClockCalculate`]

| 項目 | 規則 |
|---|---|
| 対象 | 指定日の IN 打刻と OUT 打刻。どちらかがない日は全項目を 0 とする |
| 日付またぎ | OUT が IN より前の時刻の場合、OUT を翌日として扱う |
| 端数処理 | 秒以下を切り捨てた上で、IN を 15 分単位で切り上げ、OUT を 15 分単位で切り捨てる |
| 勤務時間 | 端数処理後の [OUT − IN] から休憩時間を引いた時間 |
| 休憩時間 | OUT 打刻に記録した休憩時間 |
| 深夜勤務 | 22:00〜翌 7:00 と勤務時間帯の重なり。開始を 15 分単位で切り上げ、終了を切り捨てる。休憩時間は差し引かない |
| 残業時間 | 勤務時間のうち 7.75 時間 [`WORK_HOURS_PER_DAY`] を超えた分 |
| 月次合計 | 月の全日の日次集計を合算する [勤務・深夜・休憩・残業] |

### ダッシュボード [`/clock/dashboard/`]

- クエリパラメータ `date` [`YYYY-MM-DD`] の日の集計を表で表示する。未指定は当日とする。
- 不正な日付は当日の集計を表示し、「Invalid date. Showing today's summary.」を表示する。
- 表示項目: In / Out [打刻がない場合は `-`]、Work / Night / Break / Overtime [時間。小数 2 桁]
- 対象月の Timesheets へのリンクを持つ。

### 勤怠一覧 [`/clock/timesheets/`]

- クエリパラメータ `year` / `month` の月の日次集計と月次合計を表示する。未指定は当月とする。
- 選択できる年は 2020 年 [`MonthSelectForm.START_YEAR`] から当年まで。範囲外・不正な値は当月を表示し、「Invalid month. Showing the current month.」を表示する。
- 前月・翌月へのリンクは、選択できる範囲内の場合のみ表示する。
- 日付のセルは Dashboard へのリンクとし、土曜に `saturday`、日曜に `sunday` のクラスを付ける。

## ワークフロー

### 有給申請 [`/workflow/request/paid_leave/`]

- 開始日・終了日・理由 [任意] を入力し、ステータス「Pending」で登録する。
- 送信時に `confirm.js` で確認ダイアログを表示する。

### 承認 [`/workflow/approval/`]

- ステータスが「Pending」の有給申請を一覧で表示する。
- 申請ごとに Pending / Approved / Rejected を選択して送信する。POST のキーは `status_{申請 ID}` とする。
- Approved [`1`] / Rejected [`2`] のみを反映し、承認者に操作したユーザーを記録する。Pending のまま、数値でない ID、存在しない ID、無関係なキーは無視する。
- 全件を 1 つのトランザクションで更新し、`approval` へリダイレクトする。

### 申請メニュー・ワークフロー選択

- 申請メニューは Paid Leave へのリンクを持つ。Clock Correct / Fare / Pay Period はリンク先が未実装 [`#`]
- ワークフロー選択は Request / Approval へのリンクを持つ。

## 要件との差異

[requirements.md](requirements.md) に記載し、実装と異なる、または未実装の事項。

| 区分 | 要件 | 実装 |
|---|---|---|
| ログイン | ユーザー ID でのログインを想定 [ログイン画面の入力欄の表示も `user id`] | `username` で認証する |
| ユーザー | 登録情報の確認・変更、アイコン、メール通知、削除、パスワード再設定 | 未実装 [ログイン画面の「Forgotten password?」はリンク先なし] |
| 認証 | アクセス履歴 | 未実装 |
| 打刻 | 打刻の修正、交通費、勤怠締めの申請 | モデル [`ClockCorrect` / `Fare` / `PayPeriod`] のみ。画面は未実装 |
| 打刻 | 定時・休憩時間・交通費の設定 | 定時は 7.75 時間で固定。設定画面は未実装 |
| 集計 | 給与、有給、交通費 | 未実装 |
| ワークフロー | 管理者権限の追加・削除、承認ルート、有給の付与・管理・通知 | 未実装。承認はスーパーユーザーが行う |
| 画面 | Administration | サイドバーの項目のみ [リンク先なし] |
| DB | ユーザーのアイコン・有給・二要素認証 | 未実装 |
