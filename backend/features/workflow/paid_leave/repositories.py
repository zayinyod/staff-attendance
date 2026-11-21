from util.base_repository import BaseRepository
from attendance.models import PaidLeave
from ..repositories import WorkflowRepository
from .domains import PaidLeaveDomain


class PaidLeaveRepository(BaseRepository):
    model = PaidLeave

    workflow_type = "paid_leave"

    @classmethod
    def workflow_codes(cls):
        return WorkflowRepository.workflow_codes()

    @classmethod
    def create(cls, paid_leave_entry: PaidLeaveDomain):
        """
        共通テーブルと詳細テーブルに保存する。呼び出し側のトランザクション内で実行する
        """
        workflow = WorkflowRepository.create(cls.workflow_type, paid_leave_entry)
        paid_leave = cls.model(
            workflow=workflow,
            start_date=paid_leave_entry.start_date,
            end_date=paid_leave_entry.end_date,
            reason=paid_leave_entry.reason,
        )
        paid_leave.save()
