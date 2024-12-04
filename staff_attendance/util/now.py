from datetime import datetime, date, time
from django.utils import timezone

class Now:
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"

    @classmethod
    def date(cls, dt: date = None):
        dt = dt or timezone.localtime()
        return dt.strftime(cls.date_format)

    @classmethod
    def time(cls, dt: time = None):
        dt = dt or timezone.localtime()
        return dt.strftime(cls.time_format)

    @classmethod
    def datetime(cls, dt: datetime = None):
        return f"{cls.date(dt)} {cls.time(dt)}"
