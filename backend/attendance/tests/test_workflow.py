"""
ワークフロー [有給の申請・承認] のテスト。
"""
from datetime import date
from django.urls import reverse
from attendance.models import CodeMaster, PaidLeave
from attendance.tests.test_views import BaseViewTestCase


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
