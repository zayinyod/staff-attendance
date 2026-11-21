from dataclasses import dataclass
from attendance.models import CodeMaster


@dataclass
class BaseDomain:
    """全種別に共通するワークフローの項目"""

    user: str = None
    status: CodeMaster = None
    approver: str = None
