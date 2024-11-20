from util.base_repository import BaseRepository
from util.now import Now
from attendance.models import Clock
from .domains import ClockDomain

class ClockRepository(BaseRepository):
    model = Clock

    @classmethod
    def save(cls, clock_entry: ClockDomain):
        clock = cls.model(
            user=clock_entry.user,
            date_stamp=clock_entry.date_stamp,
            time_stamp=clock_entry.time_stamp,
            clock=clock_entry.clock,
            break_time=clock_entry.break_time,
            location=clock_entry.location,
        )
        clock.save()

    @classmethod
    def get_today_in_record(cls, user):
        today = Now.date()
        return cls.filter(user=user, date_stamp=today, clock="IN").first()

    @classmethod
    def get_clock(cls, user, date):
        in_clock = cls.filter(user=user, date_stamp=date, clock="IN").first()
        out_clock = cls.filter(user=user, date_stamp=date, clock="OUT").first()
        return {"in_clock": in_clock, "out_clock": out_clock}
