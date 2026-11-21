"""
ワークフロー [有給の申請・承認] のテスト。

申請データの作成と、ステータス・承認者の取得はヘルパー関数に集約する。
テーブル構成を変更する際は、ヘルパー関数のみを修正すればよいようにするため。
"""
from datetime import date, datetime, timezone as dt_timezone
from unittest.mock import patch
from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models import ProtectedError
from django.test import TransactionTestCase
from django.urls import reverse
from attendance.models import CodeMaster, PaidLeave, User, Workflow
from attendance.tests.test_views import BaseViewTestCase
from features.workflow.paid_leave.usecases import PaidLeaveEntry
from features.workflow.usecases import WorkflowApproval


PENDING = "0"
APPROVED = "1"
REJECTED = "2"
PAID_LEAVE_TYPE = "0"


def workflow_status(code: str) -> CodeMaster:
    return CodeMaster.objects.get(code_type="workflow_status", code=code)


def workflow_type(code: str) -> CodeMaster:
    return CodeMaster.objects.get(code_type="workflow_type", code=code)


def create_paid_leave(user, status_code=PENDING, start_date=date(2024, 6, 1),
                      end_date=date(2024, 6, 2), reason="test", approver=None) -> Workflow:
    """申請を作成する。戻り値の id は承認画面の POST キーに使う ID である"""
    workflow = Workflow.objects.create(
        workflow_type=workflow_type(PAID_LEAVE_TYPE),
        user=user,
        status=workflow_status(status_code),
        approver=approver,
    )
    PaidLeave.objects.create(
        workflow=workflow,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )
    return workflow


def find_paid_leaves(user):
    return PaidLeave.objects.filter(workflow__user=user)


def status_and_approver(record) -> tuple:
    """DB の最新のステータスと承認者を返す。record は Workflow または PaidLeave とする"""
    workflow = record.workflow if isinstance(record, PaidLeave) else record
    workflow.refresh_from_db()
    return workflow.status, workflow.approver


class WorkflowTestCase(BaseViewTestCase):
    def login_as_user(self):
        self.client.login(username="testuser", password="SecurePass1!")

    def login_as_admin(self):
        self.client.login(username="admin", password="AdminPass1!")


# ------------------------------------------------------------------ 申請

class TestPaidLeaveRequestView(WorkflowTestCase):
    """PaidLeaveRequestView の申請処理"""

    url_name = "paid_leave_request"

    def valid_payload(self, **overrides) -> dict:
        payload = {"start_date": "2024-07-01", "end_date": "2024-07-03", "reason": "vacation"}
        payload.update(overrides)
        return payload

    def test_get_redirects_if_not_logged_in(self):
        """未認証ユーザーはログイン画面にリダイレクトされること"""
        response = self.client.get(reverse(self.url_name))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_get_shows_form(self):
        """申請フォームが表示されること"""
        self.login_as_user()
        response = self.client.get(reverse(self.url_name))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "workflow/paid_leave/request.html")
        for field in ["start_date", "end_date", "reason"]:
            self.assertContains(response, f'name="{field}"')

    def test_post_creates_pending_request(self):
        """申請者はログイン中のユーザー、ステータスは Pending、承認者は空で作成されること"""
        self.login_as_user()
        response = self.client.post(reverse(self.url_name), self.valid_payload())
        self.assertRedirects(response, reverse(self.url_name))

        paid_leaves = find_paid_leaves(self.user)
        self.assertEqual(paid_leaves.count(), 1)
        paid_leave = paid_leaves.get()
        self.assertEqual(paid_leave.start_date, date(2024, 7, 1))
        self.assertEqual(paid_leave.end_date, date(2024, 7, 3))
        self.assertEqual(paid_leave.reason, "vacation")
        self.assertEqual(status_and_approver(paid_leave), (workflow_status(PENDING), None))

    def test_post_without_reason_creates_request(self):
        """理由が空でも申請でき、空文字として保存されること"""
        self.login_as_user()
        response = self.client.post(reverse(self.url_name), self.valid_payload(reason=""))
        self.assertRedirects(response, reverse(self.url_name))
        self.assertEqual(find_paid_leaves(self.user).get().reason, "")

    def test_post_invalid_date_shows_error(self):
        """存在しない日付はエラーとなり、申請は作成されないこと"""
        self.login_as_user()
        response = self.client.post(reverse(self.url_name), self.valid_payload(start_date="2024-13-45"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["start_date"])
        self.assertFalse(find_paid_leaves(self.user).exists())

    def test_post_missing_required_field_shows_error(self):
        """必須項目が欠けている場合はエラーとなり、申請は作成されないこと"""
        self.login_as_user()
        payload = self.valid_payload()
        del payload["end_date"]
        response = self.client.post(reverse(self.url_name), payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["end_date"])
        self.assertFalse(find_paid_leaves(self.user).exists())

    def test_post_by_superuser_creates_request(self):
        """スーパーユーザーも申請できること"""
        self.login_as_admin()
        response = self.client.post(reverse(self.url_name), self.valid_payload())
        self.assertRedirects(response, reverse(self.url_name))
        self.assertEqual(find_paid_leaves(self.admin).count(), 1)


# ------------------------------------------------------------------ 承認画面の表示

class TestApprovalView(WorkflowTestCase):
    def test_get_returns_403_for_general_user(self):
        """一般ユーザーは承認画面にアクセスできないこと"""
        self.login_as_user()
        response = self.client.get(reverse("approval"))
        self.assertEqual(response.status_code, 403)

    def test_get_shows_approval_page_for_superuser(self):
        """スーパーユーザーは承認画面を閲覧できること"""
        self.login_as_admin()
        response = self.client.get(reverse("approval"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "workflow/approval.html")

    def test_get_redirects_if_not_logged_in(self):
        """未認証ユーザーはリダイレクトされること"""
        response = self.client.get(reverse("approval"))
        self.assertEqual(response.status_code, 302)

    def test_get_lists_only_pending_requests(self):
        """Pending の申請のみ一覧に含まれ、Approved・Rejected は含まれないこと"""
        pending = create_paid_leave(self.user, PENDING)
        create_paid_leave(self.user, APPROVED, approver=self.admin)
        create_paid_leave(self.user, REJECTED, approver=self.admin)

        self.login_as_admin()
        response = self.client.get(reverse("approval"))
        listed_ids = [data.id for data in response.context["pending_list"]]
        self.assertEqual(listed_ids, [pending.id])

    def test_get_shows_requests_of_any_user(self):
        """申請者を問わず一覧に含まれ、申請者名・期間・理由が表示されること"""
        create_paid_leave(self.user, start_date=date(2024, 8, 5), end_date=date(2024, 8, 7), reason="trip")
        create_paid_leave(self.admin, reason="own request")

        self.login_as_admin()
        response = self.client.get(reverse("approval"))
        self.assertEqual(len(response.context["pending_list"]), 2)
        for text in ["testuser", "2024/08/05", "2024/08/07", "trip", "own request"]:
            self.assertContains(response, text)

    def test_get_without_requests_shows_empty_list(self):
        """申請がない場合も表示できること"""
        self.login_as_admin()
        response = self.client.get(reverse("approval"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["pending_list"]), 0)


# ------------------------------------------------------------------ 承認処理

class TestApprovalPost(WorkflowTestCase):
    """ApprovalView の POST 処理"""

    def setUp(self):
        self.paid_leave = create_paid_leave(self.user)

    def test_post_returns_403_for_general_user(self):
        """一般ユーザーの POST は 403 になること"""
        self.login_as_user()
        response = self.client.post(reverse("approval"), {})
        self.assertEqual(response.status_code, 403)

    def test_post_redirects_if_not_logged_in(self):
        """未認証ユーザーの POST はリダイレクトされること"""
        response = self.client.post(reverse("approval"), {})
        self.assertEqual(response.status_code, 302)

    def test_post_approves_request(self):
        """承認するとステータスと承認者が更新されること"""
        self.login_as_admin()
        response = self.client.post(reverse("approval"), {
            f"status_{self.paid_leave.id}": APPROVED,
        })
        self.assertRedirects(response, reverse("approval"))
        self.assertEqual(
            status_and_approver(self.paid_leave), (workflow_status(APPROVED), self.admin)
        )

    def test_post_rejects_request(self):
        """却下するとステータスが更新されること"""
        self.login_as_admin()
        self.client.post(reverse("approval"), {f"status_{self.paid_leave.id}": REJECTED})

        status, _ = status_and_approver(self.paid_leave)
        self.assertEqual(status, workflow_status(REJECTED))

    def test_post_ignores_pending_value(self):
        """Pending のままの項目は更新されないこと"""
        self.login_as_admin()
        self.client.post(reverse("approval"), {f"status_{self.paid_leave.id}": PENDING})

        self.assertEqual(status_and_approver(self.paid_leave), (workflow_status(PENDING), None))

    def test_post_ignores_non_numeric_id(self):
        """数値でない ID を含むキーは無視されること"""
        self.login_as_admin()
        response = self.client.post(reverse("approval"), {
            "status_paid_leave_1": APPROVED,
            "csrfmiddlewaretoken": "dummy",
        })
        self.assertRedirects(response, reverse("approval"))

        status, _ = status_and_approver(self.paid_leave)
        self.assertEqual(status, workflow_status(PENDING))

    def test_post_ignores_unknown_id(self):
        """存在しない ID は無視され、エラーにならないこと"""
        self.login_as_admin()
        response = self.client.post(reverse("approval"), {"status_999999": APPROVED})
        self.assertRedirects(response, reverse("approval"))

    def test_post_ignores_unrelated_key(self):
        """status_ 以外のキーは無視されること"""
        self.login_as_admin()
        response = self.client.post(reverse("approval"), {"comment_1": APPROVED})
        self.assertRedirects(response, reverse("approval"))

    def test_post_processes_multiple_requests(self):
        """一度の POST で承認と却下を混在させて処理できること"""
        other = create_paid_leave(self.user)

        self.login_as_admin()
        self.client.post(reverse("approval"), {
            f"status_{self.paid_leave.id}": APPROVED,
            f"status_{other.id}": REJECTED,
        })

        self.assertEqual(
            status_and_approver(self.paid_leave), (workflow_status(APPROVED), self.admin)
        )
        self.assertEqual(status_and_approver(other), (workflow_status(REJECTED), self.admin))

    def test_processed_request_disappears_from_list(self):
        """承認した申請は、次の表示で一覧から消えること"""
        self.login_as_admin()
        self.client.post(reverse("approval"), {f"status_{self.paid_leave.id}": APPROVED})

        response = self.client.get(reverse("approval"))
        self.assertEqual(len(response.context["pending_list"]), 0)

    def test_post_rolls_back_when_processing_fails(self):
        """途中で例外が発生した場合、先に処理した申請の変更も取り消されること"""
        other = create_paid_leave(self.user)
        original_approve = WorkflowApproval.approve
        call_count = {"value": 0}

        def approve_then_fail(request_id, status_code, approver):
            call_count["value"] += 1
            if call_count["value"] == 2:
                raise RuntimeError("simulated failure")
            return original_approve(request_id, status_code, approver)

        self.login_as_admin()
        with patch.object(WorkflowApproval, "approve", side_effect=approve_then_fail):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse("approval"), {
                    f"status_{self.paid_leave.id}": APPROVED,
                    f"status_{other.id}": APPROVED,
                })

        self.assertEqual(call_count["value"], 2)
        self.assertEqual(status_and_approver(self.paid_leave), (workflow_status(PENDING), None))
        self.assertEqual(status_and_approver(other), (workflow_status(PENDING), None))


# ------------------------------------------------------------------ Usecase

class TestPaidLeaveEntry(WorkflowTestCase):
    """PaidLeaveEntry の申請処理"""

    def test_create_request_creates_pending_request(self):
        """ステータス Pending、承認者なしで作成されること"""
        PaidLeaveEntry.create_request(self.user, {
            "start_date": date(2024, 9, 1),
            "end_date": date(2024, 9, 2),
            "reason": "rest",
        })

        paid_leave = find_paid_leaves(self.user).get()
        self.assertEqual(status_and_approver(paid_leave), (workflow_status(PENDING), None))

    def test_create_request_sets_paid_leave_type(self):
        """種別が Paid Leave の共通テーブルと、詳細テーブルが 1 件ずつ作成されること"""
        PaidLeaveEntry.create_request(self.user, {
            "start_date": date(2024, 9, 1),
            "end_date": date(2024, 9, 2),
            "reason": "",
        })

        workflow = Workflow.objects.get(user=self.user)
        self.assertEqual(workflow.workflow_type, workflow_type(PAID_LEAVE_TYPE))
        self.assertEqual(workflow.paidleave.start_date, date(2024, 9, 1))


class TestWorkflowApproval(WorkflowTestCase):
    """WorkflowApproval の承認処理"""

    def test_approve_rejects_invalid_code(self):
        """承認・却下以外のコードでは ValueError を送出し、何も変更しないこと"""
        paid_leave = create_paid_leave(self.user)

        for code in [PENDING, "3"]:
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    WorkflowApproval.approve(paid_leave.id, code, self.admin)

        self.assertEqual(status_and_approver(paid_leave), (workflow_status(PENDING), None))

    def test_approve_unknown_id_returns_false(self):
        """存在しない ID では False を返すこと"""
        self.assertFalse(WorkflowApproval.approve(999999, APPROVED, self.admin))

    def test_pending_returns_only_pending_requests(self):
        """Pending の申請のみを返すこと"""
        pending = create_paid_leave(self.user, PENDING)
        create_paid_leave(self.user, APPROVED, approver=self.admin)
        create_paid_leave(self.user, REJECTED, approver=self.admin)

        self.assertEqual([data.id for data in WorkflowApproval.pending()], [pending.id])


# ------------------------------------------------------------------ Model

class TestPaidLeaveModel(WorkflowTestCase):
    """PaidLeave の表示と、参照先の削除時の動作"""

    def test_str(self):
        """[申請者] 開始日 - 終了日 の形式であること"""
        paid_leave = create_paid_leave(self.user)
        self.assertEqual(str(paid_leave.paidleave), "[testuser] 2024-06-01 - 2024-06-02")

    def test_deleting_applicant_deletes_request(self):
        """申請者を削除すると申請も削除されること"""
        applicant = User.objects.create_user(user_id="U00002", username="applicant", password="SecurePass1!")
        create_paid_leave(applicant)

        applicant.delete()
        self.assertFalse(Workflow.objects.filter(user_id="U00002").exists())
        self.assertFalse(PaidLeave.objects.filter(workflow__user_id="U00002").exists())

    def test_deleting_approver_keeps_request(self):
        """承認者を削除しても申請は残り、承認者が空になること"""
        approver = User.objects.create_user(user_id="A00002", username="approver", password="SecurePass1!")
        paid_leave = create_paid_leave(self.user, APPROVED, approver=approver)

        approver.delete()
        self.assertEqual(status_and_approver(paid_leave), (workflow_status(APPROVED), None))

    def test_status_in_use_cannot_be_deleted(self):
        """申請が参照しているステータスは削除できないこと"""
        create_paid_leave(self.user)
        with self.assertRaises(ProtectedError):
            workflow_status(PENDING).delete()


class TestWorkflowModel(WorkflowTestCase):
    """Workflow と詳細テーブルの関係"""

    def test_str(self):
        """[ID] 種別 (申請者) の形式であること"""
        workflow = create_paid_leave(self.user)
        self.assertEqual(str(workflow), f"[{workflow.id}] Paid Leave (testuser)")

    def test_detail_is_one_to_one(self):
        """1 件のワークフローに同じ種別の詳細を 2 件結び付けられないこと"""
        workflow = create_paid_leave(self.user)
        with self.assertRaises(IntegrityError):
            PaidLeave.objects.create(workflow=workflow)

    def test_deleting_workflow_deletes_detail(self):
        """ワークフローを削除すると詳細も削除されること"""
        workflow = create_paid_leave(self.user)

        workflow.delete()
        self.assertFalse(PaidLeave.objects.exists())

    def test_workflow_type_in_use_cannot_be_deleted(self):
        """ワークフローが参照している種別は削除できないこと"""
        create_paid_leave(self.user)
        with self.assertRaises(ProtectedError):
            workflow_type(PAID_LEAVE_TYPE).delete()


# ------------------------------------------------------------------ データ移行

class TestWorkflowDataMigration(TransactionTestCase):
    """0018〜0020 で PaidLeave の共通項目が Workflow に移ること"""

    # 終了時の flush で消えるマイグレーション投入データ [CodeMaster] を復元する
    serialized_rollback = True

    migrate_from = [("attendance", "0017_alter_clock_clock_alter_clock_location")]
    migrate_to = [("attendance", "0020_remove_workflow_fields_from_details")]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        self.old_apps = executor.loader.project_state(self.migrate_from).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

    def migrate_to_latest(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.migrate_to)
        return executor.loader.project_state(self.migrate_to).apps

    def test_paid_leave_is_moved_to_workflow(self):
        """ID・申請者・ステータス・承認者・作成日時が引き継がれること"""
        OldUser = self.old_apps.get_model("attendance", "User")
        OldCodeMaster = self.old_apps.get_model("attendance", "CodeMaster")
        OldPaidLeave = self.old_apps.get_model("attendance", "PaidLeave")

        applicant = OldUser.objects.create(user_id="U00009", username="applicant", password="x")
        approver = OldUser.objects.create(user_id="A00009", username="approver", password="x")
        pending = OldCodeMaster.objects.get(code_type="workflow_status", code=PENDING)
        approved = OldCodeMaster.objects.get(code_type="workflow_status", code=APPROVED)

        old_pending = OldPaidLeave.objects.create(
            id=5, user=applicant, status=pending,
            start_date=date(2024, 6, 1), end_date=date(2024, 6, 2), reason="first",
        )
        old_approved = OldPaidLeave.objects.create(
            id=8, user=applicant, status=approved, approver=approver,
            start_date=date(2024, 7, 1), end_date=date(2024, 7, 1), reason=None,
        )
        created_at = datetime(2024, 5, 1, 9, 0, tzinfo=dt_timezone.utc)
        updated_at = datetime(2024, 5, 2, 10, 0, tzinfo=dt_timezone.utc)
        OldPaidLeave.objects.filter(id=old_approved.id).update(created_at=created_at, updated_at=updated_at)

        new_apps = self.migrate_to_latest()
        NewWorkflow = new_apps.get_model("attendance", "Workflow")
        NewPaidLeave = new_apps.get_model("attendance", "PaidLeave")

        self.assertEqual(list(NewWorkflow.objects.order_by("id").values_list("id", flat=True)), [5, 8])

        moved_pending = NewWorkflow.objects.get(id=old_pending.id)
        self.assertEqual(moved_pending.workflow_type.code_type, "workflow_type")
        self.assertEqual(moved_pending.workflow_type.code, PAID_LEAVE_TYPE)
        self.assertEqual(moved_pending.user_id, "U00009")
        self.assertEqual(moved_pending.status.code, PENDING)
        self.assertIsNone(moved_pending.approver_id)

        moved_approved = NewWorkflow.objects.get(id=old_approved.id)
        self.assertEqual(moved_approved.status.code, APPROVED)
        self.assertEqual(moved_approved.approver_id, "A00009")
        self.assertEqual(moved_approved.created_at, created_at)
        self.assertEqual(moved_approved.updated_at, updated_at)

        detail = NewPaidLeave.objects.get(workflow_id=old_approved.id)
        self.assertEqual(detail.start_date, date(2024, 7, 1))
        self.assertIsNone(detail.reason)

        # 移行後の採番が既存の ID と重複しないこと
        new_workflow = NewWorkflow.objects.create(
            workflow_type=moved_pending.workflow_type, user_id="U00009", status=moved_pending.status,
        )
        self.assertGreater(new_workflow.id, 8)
