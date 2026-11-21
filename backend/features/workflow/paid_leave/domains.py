from dataclasses import dataclass
from datetime import date
from ..domains import BaseDomain


@dataclass
class PaidLeaveDomain(BaseDomain):
    start_date: date = None
    end_date: date = None
    reason: str = None
