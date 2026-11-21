"""
View の HTTP 動作テスト（認証チェック・リダイレクト・フォーム処理）。

view モジュールの import は Django が URL 解決時にレイジーに行う。
setUpTestData でコードマスターを作成してから self.client でリクエストすることで、
ClockRepository 等のクラス定義時 DB クエリが正しいデータを参照できる。
"""
import re
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
from unittest.mock import patch
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from attendance.models import Clock, CodeMaster, Department, User
from features.user.repositories import UserRepository
from features.user.usecases import UserUseCase
from util.id_generator import IDGenerator
from util.shortcuts import DEFAULT_SHORTCUTS


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

    def test_summary_table_is_rendered_inside_panel(self):
        """集計表がカード [.panel] の内側に描画されること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.get(reverse("dashboard"))
        finder = AncestorClassFinder(target_tag="table")
        finder.feed(response.content.decode())
        self.assertIn("panel", finder.ancestor_classes)

    def test_date_input_defaults_to_target_date(self):
        """日付選択の初期値が対象日であること"""
        self.client.login(username="testuser", password="SecurePass1!")
        response = self.client.get(reverse("dashboard"), {"date": "2024-04-01"})
        self.assertContains(response, 'type="date" name="date" value="2024-04-01"')


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


# ------------------------------------------------------------------ Timesheets

class TestTimesheetsView(BaseViewTestCase):
    """月次一覧画面"""

    def setUp(self):
        self.client.login(username="testuser", password="SecurePass1!")
        self.today = timezone.localdate()

    def test_get_redirects_if_not_logged_in(self):
        """未認証ユーザーはログインページへリダイレクトされること"""
        self.client.logout()
        response = self.client.get(reverse("timesheets"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_get_shows_current_month_by_default(self):
        """年月未指定の場合は当月が表示されること"""
        response = self.client.get(reverse("timesheets"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clock/timesheets.html")
        self.assertEqual(response.context["current_month"].year, self.today.year)
        self.assertEqual(response.context["current_month"].month, self.today.month)
        self.assertFalse(response.context["has_invalid_month"])

    def test_get_lists_all_days_of_month(self):
        """指定した月の日数分の行が返ること"""
        response = self.client.get(reverse("timesheets"), {"year": 2024, "month": 2})
        self.assertEqual(len(response.context["daily_records"]), 29)

    def test_get_with_invalid_month_falls_back_to_current_month(self):
        """範囲外の月は当月にフォールバックし、通知が表示されること"""
        response = self.client.get(reverse("timesheets"), {"year": 2024, "month": 13})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid month")
        self.assertEqual(response.context["current_month"].month, self.today.month)

    def test_get_with_non_numeric_month_falls_back(self):
        """数値でない年月も当月にフォールバックすること"""
        response = self.client.get(reverse("timesheets"), {"year": "abc", "month": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid month")

    def test_get_with_year_before_start_falls_back(self):
        """選択可能な範囲より前の年は当月にフォールバックすること"""
        response = self.client.get(reverse("timesheets"), {"year": 1999, "month": 4})
        self.assertContains(response, "Invalid month")

    def test_totals_reflect_clock_records(self):
        """打刻レコードが合計に反映されること"""
        Clock.objects.create(
            user=self.user, date_stamp=date(2024, 4, 1), time_stamp="09:00",
            clock=self.clock_in, break_time=Decimal("1.00"), location=self.location_office,
        )
        Clock.objects.create(
            user=self.user, date_stamp=date(2024, 4, 1), time_stamp="18:00",
            clock=self.clock_out, break_time=Decimal("1.00"), location=self.location_office,
        )

        response = self.client.get(reverse("timesheets"), {"year": 2024, "month": 4})
        self.assertAlmostEqual(response.context["totals"]["total_work_time"], 8.0, places=2)

    def test_previous_and_next_month_navigation(self):
        """前月・翌月のリンク先が正しいこと"""
        response = self.client.get(reverse("timesheets"), {"year": 2024, "month": 1})
        self.assertEqual(response.context["previous_month"], date(2023, 12, 31))
        self.assertEqual(response.context["next_month"], date(2024, 2, 1))

    def test_next_month_is_hidden_beyond_selectable_years(self):
        """選択可能な範囲を超える翌月は表示されないこと"""
        response = self.client.get(
            reverse("timesheets"), {"year": self.today.year, "month": 12}
        )
        self.assertIsNone(response.context["next_month"])

    def test_previous_month_is_hidden_before_start_year(self):
        """選択可能な範囲より前の前月は表示されないこと"""
        response = self.client.get(reverse("timesheets"), {"year": 2020, "month": 1})
        self.assertIsNone(response.context["previous_month"])

    def test_table_is_rendered_inside_panel(self):
        """表がカード [.panel] の内側に描画されること"""
        response = self.client.get(reverse("timesheets"))
        finder = AncestorClassFinder(target_tag="table")
        finder.feed(response.content.decode())
        self.assertIn("panel", finder.ancestor_classes)

    def test_weekend_cells_have_weekday_class(self):
        """土曜・日曜の日付セルにのみ曜日のクラスが付与されること"""
        response = self.client.get(reverse("timesheets"), {"year": 2024, "month": 4})
        content = response.content.decode()
        # 2024 年 4 月の土曜は 6, 13, 20, 27 日、日曜は 7, 14, 21, 28 日
        self.assertEqual(self.cell_dates(content, "saturday"), [6, 13, 20, 27])
        self.assertEqual(self.cell_dates(content, "sunday"), [7, 14, 21, 28])

    @staticmethod
    def cell_dates(content: str, weekday_class: str) -> list:
        pattern = rf'<td class="{weekday_class}">\s*<a href="[^"]*date=2024-04-(\d{{2}})"'
        return [int(day) for day in re.findall(pattern, content)]

    def test_shortcut_bindings_are_embedded(self):
        """ショートカットの割り当てがページに埋め込まれること"""
        response = self.client.get(reverse("timesheets"))
        self.assertEqual(response.context["shortcut_bindings"], DEFAULT_SHORTCUTS)
        self.assertContains(response, 'id="shortcut-bindings"')


# ------------------------------------------------------------------ Sidebar

class TestSidebar(BaseViewTestCase):
    """サイドバー [frame.html / sidebar.html] の描画"""

    MENU_LABELS = ["Dashboard", "Clock", "Timesheets", "Workflow", "Administration", "Log out"]

    def setUp(self):
        self.client.login(username="testuser", password="SecurePass1!")

    @staticmethod
    def nav_html(response) -> str:
        content = response.content.decode()
        return re.search(r'<nav class="sidebar".*?</nav>', content, flags=re.S).group(0)

    @staticmethod
    def current_labels(nav_html: str) -> list:
        pattern = r'<a class="sidebar-link"[^>]*aria-current="page"[^>]*>.*?<span>([^<]+)</span>'
        return re.findall(pattern, nav_html, flags=re.S)

    def test_toggle_and_mask_are_outside_nav(self):
        """開閉ボタンと幕がサイドバーの外に描画されること [余白のクリックで閉じる不具合の防止]"""
        response = self.client.get(reverse("timesheets"))
        nav_html = self.nav_html(response)
        self.assertContains(response, 'id="sidebar-toggle"', count=1)
        self.assertContains(response, 'id="sidebar-mask"', count=1)
        self.assertNotIn("sidebar-toggle", nav_html)
        self.assertNotIn("sidebar-mask", nav_html)

    def test_menu_labels_and_icons(self):
        """各メニューが先頭のみ大文字の表記で、左端にアイコンを持つこと"""
        nav_html = self.nav_html(self.client.get(reverse("timesheets")))
        self.assertEqual(re.findall(r"<span>([^<]+)</span>", nav_html), self.MENU_LABELS)
        self.assertEqual(nav_html.count('class="sidebar-icon"'), len(self.MENU_LABELS))

    def test_current_page_is_marked(self):
        """表示中のページのメニューにのみ aria-current が付与されること"""
        cases = [("dashboard", "Dashboard"), ("clock", "Clock"), ("timesheets", "Timesheets")]
        for url_name, label in cases:
            with self.subTest(url_name=url_name):
                nav_html = self.nav_html(self.client.get(reverse(url_name)))
                self.assertEqual(self.current_labels(nav_html), [label])

    def test_workflow_pages_mark_workflow(self):
        """ワークフロー配下の画面では Workflow が現在のページとなること"""
        self.client.login(username="admin", password="AdminPass1!")
        for url_name in ["select", "request", "approval", "paid_leave_request"]:
            with self.subTest(url_name=url_name):
                nav_html = self.nav_html(self.client.get(reverse(url_name)))
                self.assertEqual(self.current_labels(nav_html), ["Workflow"])

    def test_sidebar_state_is_restored_before_render(self):
        """固定状態の復元スクリプトが head で同期的に読み込まれること"""
        content = self.client.get(reverse("timesheets")).content.decode()
        head = content.split("</head>", 1)[0]
        self.assertIn('<html data-sidebar="closed">', content)
        self.assertRegex(head, r'<script src="[^"]*js/sidebar_state\.js"></script>')


class AncestorClassFinder(HTMLParser):
    """最初に現れた target_tag の祖先要素が持つ class を収集する"""

    VOID_TAGS = {"br", "hr", "img", "input", "link", "meta"}

    def __init__(self, target_tag):
        super().__init__()
        self.target_tag = target_tag
        self.open_tag_classes = []
        self.ancestor_classes = None

    def handle_starttag(self, tag, attrs):
        if self.ancestor_classes is not None or tag in self.VOID_TAGS:
            return
        if tag == self.target_tag:
            self.ancestor_classes = {
                name for classes in self.open_tag_classes for name in classes
            }
            return
        self.open_tag_classes.append((dict(attrs).get("class") or "").split())

    def handle_endtag(self, tag):
        if self.ancestor_classes is None and tag not in self.VOID_TAGS and self.open_tag_classes:
            self.open_tag_classes.pop()
