from .domains import PaidLeaveDomain
from .repositories import PaidLeaveRepository

class PaidLeaveEntry:
    paid_leave_repository = PaidLeaveRepository()

    @classmethod
    def create_request(cls, user, cleaned_data):
        pending_status = cls.paid_leave_repository.workflow_codes().get("pending")
        paid_leave_request = PaidLeaveDomain(
            user=user,
            status=pending_status,
            start_date=cleaned_data["start_date"],
            end_date=cleaned_data["end_date"],
            reason=cleaned_data["reason"],
        )
        cls.paid_leave_repository.create(paid_leave_request)

    @classmethod
    def approve(cls, id, status_code, approver) -> bool:
        if status_code not in ["1", "2"]:
            raise ValueError("Invalid code. Must be 'approved' or 'rejected'.")

        return cls.paid_leave_repository.update(id, status_code, approver)

    @classmethod
    def pending(cls):
        return cls.paid_leave_repository.get_pending()
