from datetime import datetime, timedelta
from decimal import Decimal
from .domains import ClockDomain
from .repositories import ClockRepository

class ClockUseCase:
    clock_repository = ClockRepository()
    WORK_HOURS_PER_DAY = 7.75

    @classmethod
    def create_clock_entry(cls, user, cleaned_data):
        clock_entry = ClockDomain(
            user=user,
            date_stamp=cleaned_data["date_stamp"],
            time_stamp=cleaned_data["time_stamp"],
            clock=cleaned_data["clock"],
            break_time=cleaned_data["break_time"],
            location=cleaned_data["location"],
        )
        cls.clock_repository.save(clock_entry)

    @classmethod
    def get_in_breaktime_and_location(cls, user):
        in_record = cls.clock_repository.get_today_in_record(user)
        if in_record:
            return in_record.break_time, in_record.location, True
        else:
            return None, None, False

    @classmethod
    def calculate_work_time(cls, user, date):
        clocks = cls.clock_repository.get_clock(user, date)
        in_clock = clocks.get("in_clock")
        out_clock = clocks.get("out_clock")

        if not in_clock or not out_clock:
            return timedelta(0)

        base_date = in_clock.date_stamp
        in_time = datetime.combine(base_date, in_clock.time_stamp)
        out_time = datetime.combine(base_date, out_clock.time_stamp)

        work_duration = out_time - in_time
        break_time = timedelta(hours=float(out_clock.break_time))
        work_duration -= break_time
        work_hours = work_duration.total_seconds() / 3600
        work_hours = round(work_hours / 0.25) * 0.25

        return work_hours

    @classmethod
    def daily_summary(cls, user, date):
        work_duration = cls.calculate_work_time(user, date)
        is_overtime = work_duration > cls.WORK_HOURS_PER_DAY

        summary = {
            "work_duration": work_duration,
            "is_overtime": is_overtime,
            "overtime_duration": work_duration - cls.WORK_HOURS_PER_DAY if is_overtime else 0.0,
        }
        return summary
