from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from attendance.models import CodeMaster

@dataclass
class BaseDomain:
    user: str = None
    status: CodeMaster = None
    approver: str = None

@dataclass
class PaidLeaveDomain(BaseDomain):
    start_date: date = None
    end_date: date = None
    reason: str = None
