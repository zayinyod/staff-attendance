from util.base_repository import BaseRepository
from attendance.models import CodeMaster


class CodeMasterRepository(BaseRepository):
    """
    CodeMasterモデルのリポジトリクラス
    """

    model = CodeMaster

    @classmethod
    def clock_code_master(cls) -> dict:
        to_in = cls.get(code_type="clock", code="0")
        to_out = cls.get(code_type="clock", code="1")
        clock_code = {"to_in": to_in, "to_out": to_out}

        return clock_code

    @classmethod
    def workflow_code_master(cls) -> dict:
        pending = cls.get(code_type="workflow_status", code="0")
        approved = cls.get(code_type="workflow_status", code="1")
        rejected = cls.get(code_type="workflow_status", code="2")
        workflow_code = {
            "pending": pending, "0": pending,
            "approved": approved, "1": approved,
            "rejected": rejected, "2": rejected,
        }

        return workflow_code

    @classmethod
    def workflow_type_code_master(cls) -> dict:
        paid_leave = cls.get(code_type="workflow_type", code="0")
        clock_correct = cls.get(code_type="workflow_type", code="1")
        fare = cls.get(code_type="workflow_type", code="2")
        pay_period = cls.get(code_type="workflow_type", code="3")
        workflow_type_code = {
            "paid_leave": paid_leave,
            "clock_correct": clock_correct,
            "fare": fare,
            "pay_period": pay_period,
        }

        return workflow_type_code
