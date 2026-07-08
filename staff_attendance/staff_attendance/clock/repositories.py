from util.base_repository import BaseRepository
from util.code_master_repository import CodeMasterRepository
from util.now import Now
from attendance.models import Clock
from .domains import ClockDomain

class ClockRepository(BaseRepository):
    model = Clock

    @classmethod
    def _clock_codes(cls):
        return CodeMasterRepository.clock_code_master()

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
        today = Now.date_str()
        to_in = cls._clock_codes().get("to_in")
        return cls.filter(user=user, date_stamp=today, clock=to_in).first()

    @classmethod
    def get_clock(cls, user, date):
        codes = cls._clock_codes()
        in_clock = cls.filter(user=user, date_stamp=date, clock=codes["to_in"]).first()
        out_clock = cls.filter(user=user, date_stamp=date, clock=codes["to_out"]).first()
        return {"in_clock": in_clock, "out_clock": out_clock}
