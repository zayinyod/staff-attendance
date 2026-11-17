from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from attendance.models import CodeMaster

@dataclass
class ClockDomain:
    user: str = None
    date_stamp: date = None
    time_stamp: time = None
    clock: CodeMaster = None
    break_time: Decimal = None
    location: CodeMaster = None
