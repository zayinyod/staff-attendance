from .repositories import WorkflowRepository


class WorkflowApproval:
    """
    種別を問わないワークフローの承認処理
    """

    workflow_repository = WorkflowRepository()

    approvable_codes = ("1", "2")

    @classmethod
    def approve(cls, id, status_code, approver) -> bool:
        if status_code not in cls.approvable_codes:
            raise ValueError("Invalid code. Must be 'approved' or 'rejected'.")

        return cls.workflow_repository.update_status(id, status_code, approver)

    @classmethod
    def pending(cls):
        return cls.workflow_repository.get_pending()
