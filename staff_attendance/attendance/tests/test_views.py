"""
View の HTTP 動作テスト（認証チェック・リダイレクト・フォーム処理）。

view モジュールの import は Django が URL 解決時にレイジーに行う。
setUpTestData でコードマスターを作成してから self.client でリクエストすることで、
ClockRepository 等のクラス定義時 DB クエリが正しいデータを参照できる。
"""
from datetime import date
from unittest.mock import patch
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from attendance.models import Clock, CodeMaster, Department, PaidLeave, User
from staff_attendance.user.repositories import UserRepository
from staff_attendance.user.usecases import UserUseCase
from util.id_generator import IDGenerator


class BaseViewTestCase(TestCase):
    """コードマスター・部署・ユーザーをテスト前に準備する基底クラス"""

    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(name="Engineering")
        # コードマスターはマイグレーション 0016 で投入済みのものを参照する
        cls.clock_in = CodeMaster.objects.get(code_type="clock", code="0")
        cls.clock_out = CodeMaster.objects.get(code_type="clock", code="1")
        cls.location_office = CodeMaster.objects.get(code_type="location", code="0")
        cls.location_telework = CodeMaster.objects.get(code_type="location", code="1")
        cls.user = User.objects.create_user(
            user_id="U00001",
            username="testuser",
            password="SecurePass1!",
            department=cls.dept,
        )
        cls.admin = User.objects.create_user(
            user_id="A00001",
            username="admin",
            password="AdminPass1!",
            is_superuser=True,
            is_staff=True,
        )


# ------------------------------------------------------------------ Login / Logout

class TestLoginView(BaseViewTestCase):
    def test_get_shows_form(self):
        """GET でログインフォームが表示されること"""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/login.html")

    def test_post_valid_credentials_redirects_to_dashboard(self):
        """正しい認証情報でダッシュボードへリダイレクトされること"""
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "SecurePass1!",
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_post_invalid_password_shows_error(self):
        """誤ったパスワードでエラーが表示されること"""
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "WrongPassword!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incorrect")

    def test_post_unknown_user_shows_error(self):
        """存在しないユーザーでエラーが表示されること"""
        response = self.client.post(reverse("login"), {
            "username": "nobody",
            "password": "SecurePass1!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incorrect")


class TestLogoutView(BaseViewTestCase):
    def test_logout_redirects_to_login(self):
        """ログアウト後にログインページへリダイレクトされること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"))


# ------------------------------------------------------------------ UserEntry

class TestUserEntryView(BaseViewTestCase):
    def test_get_shows_registration_form(self):
        """GET でユーザー登録フォームが表示されること"""
        response = self.client.get(reverse("user_entry"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_entry.html")

    def test_post_creates_user_and_redirects(self):
        """有効なフォームデータで新規ユーザーが作成されリダイレクトされること"""
        response = self.client.post(reverse("user_entry"), {
            "username": "newuser",
            "email": "new@example.com",
            "department": self.dept.pk,
            "password1": "UniquePass9!",
            "password2": "UniquePass9!",
        })
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_post_duplicate_username_shows_error(self):
        """重複ユーザー名で登録するとエラーが表示されること"""
        response = self.client.post(reverse("user_entry"), {
            "username": "testuser",  # 既存ユーザー
            "email": "dup@example.com",
            "department": self.dept.pk,
            "password1": "UniquePass9!",
            "password2": "UniquePass9!",
        })
        self.assertEqual(response.status_code, 200)

    def test_post_short_password_shows_error(self):
        """9文字未満のパスワードはバリデーションエラーになること（要件: 9桁以上）"""
        response = self.client.post(reverse("user_entry"), {
            "username": "shortpwuser",
            "email": "short@example.com",
            "department": self.dept.pk,
            "password1": "Pass1!",  # 6文字
            "password2": "Pass1!",
        })
        self.assertEqual(response.status_code, 200)


# ------------------------------------------------------------------ Clock

class TestClockView(BaseViewTestCase):
    def test_get_redirects_if_not_logged_in(self):
        """未認証ユーザーはログインページへリダイレクトされること"""
        response = self.client.get(reverse("clock"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_get_shows_form_when_logged_in(self):
        """認証済みユーザーには打刻フォームが表示されること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.get(reverse("clock"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clock/clock.html")

    def test_post_clock_in_creates_record(self):
        """打刻 IN を POST すると打刻レコードが作成されリダイレクトされること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.post(reverse("clock"), {
            "date_stamp": "2024-04-01",
            "time_stamp": "09:00",
            "clock": self.clock_in.pk,
            "break_time": "1.00",
            "location": self.location_office.pk,
        })
        self.assertRedirects(response, reverse("clock"))

    def test_post_duplicate_clock_shows_error(self):
        """同一日・同一打刻種別の重複登録はエラーになること"""
        self.client.login(username="testuser", password="SecurePass1!")
        data = {
            "date_stamp": "2024-04-02",
            "time_stamp": "09:00",
            "clock": self.clock_in.pk,
            "break_time": "1.00",
            "location": self.location_office.pk,
        }
        self.client.post(reverse("clock"), data)
        response = self.client.post(reverse("clock"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_post_invalid_break_time_step_shows_error(self):
        """0.25 刻み以外の休憩時間はバリデーションエラーになること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.post(reverse("clock"), {
            "date_stamp": "2024-04-03",
            "time_stamp": "09:00",
            "clock": self.clock_in.pk,
            "break_time": "1.10",  # 0.25 刻みでない
            "location": self.location_office.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0.25")


# ------------------------------------------------------------------ Dashboard

class TestDashboardView(BaseViewTestCase):
    def test_get_redirects_if_not_logged_in(self):
        """未認証ユーザーはログインページへリダイレクトされること"""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_get_shows_dashboard_when_logged_in(self):
        """認証済みユーザーにはダッシュボードが表示されること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clock/dashboard.html")

    def test_get_with_date_param(self):
        """date クエリパラメータを指定してもダッシュボードが表示されること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.get(reverse("dashboard"), {"date": "2024-04-01"})
        self.assertEqual(response.status_code, 200)


# ------------------------------------------------------------------ Approval

class TestApprovalView(BaseViewTestCase):
    def test_get_returns_403_for_general_user(self):
        """一般ユーザーは承認画面にアクセスできないこと"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.get(reverse("approval"))
        self.assertEqual(response.status_code, 403)

    def test_get_shows_approval_page_for_superuser(self):
        """スーパーユーザーは承認画面を閲覧できること"""
        self.client.login(username="admin", password="AdminPass1!")
        response = self.client.get(reverse("approval"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "workflow/approval.html")

    def test_get_redirects_if_not_logged_in(self):
        """未認証ユーザーはリダイレクトされること"""
        response = self.client.get(reverse("approval"))
        self.assertEqual(response.status_code, 302)


# ------------------------------------------------------------------ Dashboard 日付検証

class TestDashboardDateResolution(BaseViewTestCase):
    """DashboardView の date クエリパラメータ検証"""

    def setUp(self):
        self.client.login(username="testuser", password="SecurePass1!")

    def test_get_with_malformed_date_falls_back_to_today(self):
        """書式が不正な日付は当日にフォールバックし、通知が表示されること"""
        response = self.client.get(reverse("dashboard"), {"date": "not-a-date"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid date")
        self.assertEqual(response.context["date"], timezone.localdate())

    def test_get_with_out_of_range_date_falls_back_to_today(self):
        """書式は正しいが存在しない日付も当日にフォールバックすること"""
        response = self.client.get(reverse("dashboard"), {"date": "2024-13-45"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid date")
        self.assertEqual(response.context["date"], timezone.localdate())

    def test_get_with_valid_date_is_converted_to_date_object(self):
        """有効な日付は date 型に変換され、通知が表示されないこと"""
        response = self.client.get(reverse("dashboard"), {"date": "2024-04-01"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Invalid date")
        self.assertEqual(response.context["date"], date(2024, 4, 1))

    def test_get_without_date_uses_today(self):
        """未指定の場合は当日が使用されること"""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["date"], timezone.localdate())
        self.assertFalse(response.context["has_invalid_date"])


# ------------------------------------------------------------------ 打刻バリデーション

class TestClockOutValidation(BaseViewTestCase):
    """IN 打刻のない日の OUT 打刻を拒否すること"""

    def setUp(self):
        self.client.login(username="testuser", password="SecurePass1!")

    def clock_payload(self, clock, date_stamp, time_stamp):
        return {
            "date_stamp": date_stamp,
            "time_stamp": time_stamp,
            "clock": clock.pk,
            "break_time": "1.00",
            "location": self.location_office.pk,
        }

    def test_post_clock_out_without_clock_in_shows_error(self):
        """IN 打刻がない日に OUT 打刻を行うとエラーになること"""
        response = self.client.post(
            reverse("clock"),
            self.clock_payload(self.clock_out, "2024-05-01", "18:00"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "without a clock-in record")
        self.assertFalse(Clock.objects.filter(date_stamp="2024-05-01").exists())

    def test_post_clock_out_after_clock_in_succeeds(self):
        """同一日に IN 打刻があれば OUT 打刻できること"""
        self.client.post(
            reverse("clock"),
            self.clock_payload(self.clock_in, "2024-05-02", "09:00"),
        )
        response = self.client.post(
            reverse("clock"),
            self.clock_payload(self.clock_out, "2024-05-02", "18:00"),
        )
        self.assertRedirects(response, reverse("clock"))
        self.assertTrue(
            Clock.objects.filter(date_stamp="2024-05-02", clock=self.clock_out).exists()
        )


# ------------------------------------------------------------------ 承認処理

class TestApprovalPost(BaseViewTestCase):
    """ApprovalView の POST 処理"""

    def setUp(self):
        self.pending = CodeMaster.objects.get(code_type="workflow_status", code="0")
        self.approved = CodeMaster.objects.get(code_type="workflow_status", code="1")
        self.rejected = CodeMaster.objects.get(code_type="workflow_status", code="2")
        self.paid_leave = PaidLeave.objects.create(
            user=self.user,
            status=self.pending,
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 2),
            reason="test",
        )

    def test_post_returns_403_for_general_user(self):
        """一般ユーザーの POST は 403 になること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.post(reverse("approval"), {})
        self.assertEqual(response.status_code, 403)

    def test_post_redirects_if_not_logged_in(self):
        """未認証ユーザーの POST はリダイレクトされること"""
        response = self.client.post(reverse("approval"), {})
        self.assertEqual(response.status_code, 302)

    def test_post_approves_request(self):
        """承認するとステータスと承認者が更新されること"""
        self.client.login(username="admin", password="AdminPass1!")
        response = self.client.post(reverse("approval"), {
            f"status_{self.paid_leave.id}": "1",
        })
        self.assertRedirects(response, reverse("approval"))

        self.paid_leave.refresh_from_db()
        self.assertEqual(self.paid_leave.status, self.approved)
        self.assertEqual(self.paid_leave.approver, self.admin)

    def test_post_rejects_request(self):
        """却下するとステータスが更新されること"""
        self.client.login(username="admin", password="AdminPass1!")
        self.client.post(reverse("approval"), {f"status_{self.paid_leave.id}": "2"})

        self.paid_leave.refresh_from_db()
        self.assertEqual(self.paid_leave.status, self.rejected)

    def test_post_ignores_pending_value(self):
        """Pending のままの項目は更新されないこと"""
        self.client.login(username="admin", password="AdminPass1!")
        self.client.post(reverse("approval"), {f"status_{self.paid_leave.id}": "0"})

        self.paid_leave.refresh_from_db()
        self.assertEqual(self.paid_leave.status, self.pending)
        self.assertIsNone(self.paid_leave.approver)

    def test_post_ignores_non_numeric_id(self):
        """数値でない ID を含むキーは無視されること"""
        self.client.login(username="admin", password="AdminPass1!")
        response = self.client.post(reverse("approval"), {
            "status_paid_leave_1": "1",
            "csrfmiddlewaretoken": "dummy",
        })
        self.assertRedirects(response, reverse("approval"))

        self.paid_leave.refresh_from_db()
        self.assertEqual(self.paid_leave.status, self.pending)

    def test_post_ignores_unknown_id(self):
        """存在しない ID は無視され、エラーにならないこと"""
        self.client.login(username="admin", password="AdminPass1!")
        response = self.client.post(reverse("approval"), {"status_999999": "1"})
        self.assertRedirects(response, reverse("approval"))

    def test_post_ignores_unrelated_key(self):
        """status_ 以外のキーは無視されること"""
        self.client.login(username="admin", password="AdminPass1!")
        response = self.client.post(reverse("approval"), {"comment_1": "1"})
        self.assertRedirects(response, reverse("approval"))


# ------------------------------------------------------------------ user_id 生成

class TestUserIdGeneration(BaseViewTestCase):
    """user_id の一意性確保"""

    def test_regenerates_user_id_on_collision(self):
        """事前確認をすり抜けた重複は再生成によって解消されること"""
        User.objects.create_user(
            user_id="123456", username="existing", password="SecurePass1!"
        )

        cleaned_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "SecurePass1!",
            "department": self.dept,
        }

        with patch.object(
            IDGenerator, "create_id", side_effect=["123456", "654321"]
        ), patch.object(
            UserRepository, "user_id_exists", side_effect=[False, True, False]
        ):
            UserUseCase.create_user_entry(cleaned_data)

        self.assertTrue(User.objects.filter(user_id="654321").exists())

    def test_raises_when_other_constraint_is_violated(self):
        """user_id 以外の一意制約違反はそのまま送出されること"""
        cleaned_data = {
            "username": "testuser",  # 既存ユーザーと重複
            "email": "dup@example.com",
            "password1": "SecurePass1!",
            "department": self.dept,
        }

        with self.assertRaises(IntegrityError):
            UserUseCase.create_user_entry(cleaned_data)
