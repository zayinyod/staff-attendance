from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

@dataclass
class ClockDomain:
    user: str = None
    date_stamp: date = None
    time_stamp: time = None
    clock: str = None
    break_time: Decimal = None
    location: str = None
