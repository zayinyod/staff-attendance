from util.base_repository import BaseRepository
from util.code_master_repository import CodeMasterRepository
from attendance.models import PaidLeave
from .domains import PaidLeaveDomain

class PaidLeaveRepository(BaseRepository):
    model = PaidLeave

    @classmethod
    def workflow_codes(cls):
        return CodeMasterRepository.workflow_code_master()

    @classmethod
    def create(cls, paid_leave_entry: PaidLeaveDomain):
        paid_leave = cls.model(
            user=paid_leave_entry.user,
            status=paid_leave_entry.status,
            approver=paid_leave_entry.approver,
            start_date=paid_leave_entry.start_date,
            end_date=paid_leave_entry.end_date,
            reason=paid_leave_entry.reason,
        )
        paid_leave.save()

    @classmethod
    def update(cls, id, status, approver) -> bool:
        this_paid_leave = cls.filter(id=id).first()
        if this_paid_leave is None:
            return False

        this_paid_leave.status = cls.workflow_codes().get(status)
        this_paid_leave.approver = approver
        this_paid_leave.save()
        return True

    @classmethod
    def get_pending(cls):
        status = cls.workflow_codes().get("pending")
        return cls.filter(status=status)
