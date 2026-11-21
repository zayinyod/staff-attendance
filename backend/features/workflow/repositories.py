from util.base_repository import BaseRepository
from util.code_master_repository import CodeMasterRepository
from attendance.models import Workflow
from .domains import BaseDomain


class WorkflowRepository(BaseRepository):
    """
    全種別に共通するワークフローの項目を扱うリポジトリ
    """

    model = Workflow

    # 一覧で詳細テーブルを結合して取得する。種別を追加した際はここに加える
    detail_relations = ("paidleave",)

    @classmethod
    def workflow_codes(cls) -> dict:
        return CodeMasterRepository.workflow_code_master()

    @classmethod
    def workflow_type_codes(cls) -> dict:
        return CodeMasterRepository.workflow_type_code_master()

    @classmethod
    def create(cls, workflow_type: str, workflow_entry: BaseDomain) -> Workflow:
        return cls.model.objects.create(
            workflow_type=cls.workflow_type_codes()[workflow_type],
            user=workflow_entry.user,
            status=workflow_entry.status,
            approver=workflow_entry.approver,
        )

    @classmethod
    def update_status(cls, id, status, approver) -> bool:
        workflow = cls.filter(id=id).first()
        if workflow is None:
            return False

        workflow.status = cls.workflow_codes().get(status)
        workflow.approver = approver
        workflow.save()
        return True

    @classmethod
    def get_pending(cls):
        status = cls.workflow_codes().get("pending")
        return (
            cls.filter(status=status)
            .select_related("user", "workflow_type", *cls.detail_relations)
            .order_by("id")
        )
