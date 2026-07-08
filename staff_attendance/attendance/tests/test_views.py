"""
View の HTTP 動作テスト（認証チェック・リダイレクト・フォーム処理）。

view モジュールの import は Django が URL 解決時にレイジーに行う。
setUpTestData でコードマスターを作成してから self.client でリクエストすることで、
ClockRepository 等のクラス定義時 DB クエリが正しいデータを参照できる。
"""
from django.test import TestCase
from django.urls import reverse
from attendance.models import User, Department, CodeMaster


class BaseViewTestCase(TestCase):
    """コードマスター・部署・ユーザーをテスト前に準備する基底クラス"""

    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(name="Engineering")
        cls.clock_in = CodeMaster.objects.create(
            code_type="clock", code="0", description="In"
        )
        cls.clock_out = CodeMaster.objects.create(
            code_type="clock", code="1", description="Out"
        )
        cls.location_office = CodeMaster.objects.create(
            code_type="location", code="0", description="Office"
        )
        cls.location_telework = CodeMaster.objects.create(
            code_type="location", code="1", description="Telework"
        )
        CodeMaster.objects.create(
            code_type="workflow_status", code="0", description="Pending"
        )
        CodeMaster.objects.create(
            code_type="workflow_status", code="1", description="Approved"
        )
        CodeMaster.objects.create(
            code_type="workflow_status", code="2", description="Rejected"
        )
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
