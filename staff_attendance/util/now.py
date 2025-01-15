from datetime import datetime, date, time
from django.utils import timezone

class Now:
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"

    @classmethod
    def date(cls, dt: date = None, str: bool = True):
        dt = dt or timezone.localdate()
        if str:
            return dt.strftime(cls.date_format)
        return dt

    @classmethod
    def time(cls, dt: time = None, str: bool = True):
        dt = dt or timezone.localtime().time()
        if str:
            return dt.strftime(cls.time_format)
        return dt

    @classmethod
    def datetime(cls, dt: datetime = None, str: bool = True):
        dt = dt or timezone.localtime()
        if str:
            return f"{cls.date(dt)} {cls.time(dt)}"
        return dt
