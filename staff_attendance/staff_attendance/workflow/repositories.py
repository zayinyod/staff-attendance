from util.base_repository import BaseRepository
from util.code_master_repository import CodeMasterRepository
from attendance.models import PaidLeave
from .domains import PaidLeaveDomain

class PaidLeaveRepository(BaseRepository):
    model = PaidLeave

    code_master = CodeMasterRepository.workflow_code_master()

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
    def update(cls, id, status, approver):
        this_paid_leave = cls.get(id=id)
        new_status = cls.code_master.get(status)
        this_paid_leave.status = new_status
        this_paid_leave.approver = approver
        this_paid_leave.save()

    @classmethod
    def get_pending(cls):
        status = cls.code_master.get("pending")
        return cls.filter(status=status)
