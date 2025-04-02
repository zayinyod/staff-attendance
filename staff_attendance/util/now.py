from django.utils import timezone

class Now:
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"

    @classmethod
    def date_str(cls, dt=None):
        dt = dt or timezone.localdate()
        return dt.strftime(cls.date_format)

    @classmethod
    def date_dt(cls, dt=None):
        dt = dt or timezone.localdate()
        return dt

    @classmethod
    def time_str(cls, dt=None):
        dt = dt or timezone.localtime().time()
        return dt.strftime(cls.time_format)

    @classmethod
    def time_dt(cls, dt=None):
        dt = dt or timezone.localtime().time()
        return dt

    @classmethod
    def datetime_str(cls, dt=None):
        return f"{cls.date_str(dt)} {cls.time_str(dt)}"

    @classmethod
    def datetime_dt(cls, dt=None):
        dt = dt or timezone.localtime()
        return dt
