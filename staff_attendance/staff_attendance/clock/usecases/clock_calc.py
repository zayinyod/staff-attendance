from datetime import datetime, timedelta
from django.utils import timezone
from ..repositories import ClockRepository

class ClockCalculate:
    clock_repository = ClockRepository()
    WORK_HOURS_PER_DAY = 7.75

    @classmethod
    def round_time(cls, hours):
        return round(hours / 0.25) * 0.25

    @classmethod
    def get_base_time(cls, user, date):
        clocks = cls.clock_repository.get_clock(user, date)
        in_clock = clocks.get("in_clock")
        out_clock = clocks.get("out_clock")

        if not in_clock or not out_clock:
            return {"in_datetime": None, "out_datetime": None, "break_time": timedelta(0)}

        in_base_date = in_clock.date_stamp
        in_datetime = datetime.combine(in_base_date, in_clock.time_stamp)
        out_base_date = out_clock.date_stamp
        out_datetime = datetime.combine(out_base_date, out_clock.time_stamp)

        if out_datetime < in_datetime:
            out_datetime += timedelta(days=1)

        break_time = timedelta(hours=float(out_clock.break_time))

        result = {
            "in_datetime": in_datetime,
            "out_datetime": out_datetime,
            "break_time": break_time,
        }

        return result

    @classmethod
    def calculate_work_time(cls, user, date):
        base_time = cls.get_base_time(user, date)

        in_datetime = base_time["in_datetime"]
        out_datetime = base_time["out_datetime"]
        break_time = base_time["break_time"]

        if in_datetime is None or out_datetime is None:
            return 0.0

        work_duration = out_datetime - in_datetime
        work_duration -= break_time
        work_hours = work_duration.total_seconds() / 3600
        work_hours = cls.round_time(work_hours)

        return work_hours

    @classmethod
    def calculate_night_work(cls, start_time: datetime, end_time: datetime):
        night_start = datetime(start_time.year, start_time.month, start_time.day, 22, 0)
        night_end = night_start + timedelta(hours=7)

        if end_time <= night_start or start_time >= night_end:
            return 0.0

        night_work_start = max(start_time, night_start)
        night_work_end = min(end_time, night_end)

        night_work_duration = night_work_end - night_work_start
        night_work_hours = night_work_duration.total_seconds() / 3600
        result = cls.round_time(night_work_hours)

        return result

    @classmethod
    def daily_summary(cls, user, date):
        base_time = cls.get_base_time(user, date)
        work_duration = cls.calculate_work_time(user, date)

        start_time = base_time["in_datetime"]
        end_time = base_time["out_datetime"]

        if start_time is None or end_time is None:
            night_work = 0.0
            break_time = 0.0
            is_overtime = False
        else:
            night_work = cls.calculate_night_work(start_time, end_time)
            break_time = float(base_time["break_time"].total_seconds() / 3600)
            is_overtime = work_duration > cls.WORK_HOURS_PER_DAY

        summary = {
            "work_duration": work_duration,
            "night_work": night_work,
            "break_time": break_time,
            "overtime_duration": work_duration - cls.WORK_HOURS_PER_DAY if is_overtime else 0.0,
        }

        return summary

    @classmethod
    def monthly_summary(cls, user, year, month):
        start_date = timezone.datetime(year, month, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        total_work_time = 0.0
        total_night_work = 0.0
        total_break_time = 0.0
        total_overtime = 0.0

        for single_date in (start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)):
            daily_data = cls.daily_summary(user, single_date.date())
            total_work_time += daily_data["work_duration"]
            total_night_work += daily_data["night_work"]
            total_break_time += daily_data["break_time"]
            total_overtime += daily_data["overtime_duration"]

        summary = {
            "total_work_time": total_work_time,
            "total_night_work": total_night_work,
            "total_break_time": total_break_time,
            "total_overtime": total_overtime,
        }

        return summary
