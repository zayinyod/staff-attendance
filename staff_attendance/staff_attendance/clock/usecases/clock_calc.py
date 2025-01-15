from datetime import datetime, timedelta
from django.utils import timezone
from util.now import Now
from util.round_calc import RoundCalculate
from ..repositories import ClockRepository

class ClockCalculate:
    clock_repository = ClockRepository()
    round_calc = RoundCalculate()

    WORK_HOURS_PER_DAY = 7.75

    @classmethod
    def round_hour(cls, dt, calc="up"):
        if calc == "up":
            return cls.round_calc.round_up_hours(dt)
        elif calc == "down":
            return cls.round_calc.round_down_hours(dt)
        else:
            raise ValueError("Invalid argument: must be 'up' or 'down'.")

    @classmethod
    def get_base_datetime(cls, user, date):
        clocks = cls.clock_repository.get_clock(user, date)
        in_clock = clocks.get("in_clock")
        out_clock = clocks.get("out_clock")

        if not in_clock or not out_clock:
            return {"in_datetime": None, "out_datetime": None, "break_time": timedelta(0)}

        in_datetime = datetime.combine(in_clock.date_stamp, in_clock.time_stamp)
        out_datetime = datetime.combine(out_clock.date_stamp, out_clock.time_stamp)

        if out_datetime < in_datetime:
            out_datetime += timedelta(days=1)

        break_time = timedelta(hours=float(out_clock.break_time))

        return {
            "in_datetime": cls.round_calc.truncate_to_minutes(in_datetime),
            "out_datetime": cls.round_calc.truncate_to_minutes(out_datetime),
            "break_time": break_time,
        }

    @classmethod
    def calculate_work_time(cls, base_time):
        in_datetime = base_time["in_datetime"]
        out_datetime = base_time["out_datetime"]
        break_time = base_time["break_time"]

        if not in_datetime or not out_datetime:
            return 0.0

        rounded_in = cls.round_hour(in_datetime, calc="up")
        rounded_out = cls.round_hour(out_datetime, calc="down")
        work_duration = (rounded_out - rounded_in) - break_time

        return work_duration.total_seconds() / 3600

    @classmethod
    def calculate_night_work(cls, start_time, end_time):
        night_start = start_time.replace(hour=22, minute=0, second=0, microsecond=0)
        night_end = night_start + timedelta(hours=7)

        rounded_start = cls.round_hour(max(start_time, night_start), calc="up")
        rounded_end = cls.round_hour(min(end_time, night_end), calc="down")

        if rounded_end <= rounded_start:
            return 0.0

        night_work_duration = rounded_end - rounded_start
        return night_work_duration.total_seconds() / 3600

    @classmethod
    def daily_summary(cls, user, date):
        base_time = cls.get_base_datetime(user, date)
        in_datetime = base_time["in_datetime"]
        out_datetime = base_time["out_datetime"]
        break_time = base_time["break_time"]

        if not in_datetime or not out_datetime:
            return {
                "punch_in": 0.0,
                "punch_out": 0.0,
                "work_duration": 0.0,
                "night_work": 0.0,
                "break_time": 0.0,
                "overtime_duration": 0.0,
            }

        work_duration = cls.calculate_work_time(base_time)
        night_work = cls.calculate_night_work(in_datetime, out_datetime)
        is_overtime = work_duration > cls.WORK_HOURS_PER_DAY
        overtime_duration = work_duration - cls.WORK_HOURS_PER_DAY if is_overtime else 0.0

        return {
            "punch_in": Now.time(in_datetime),
            "punch_out": Now.time(out_datetime),
            "work_duration": work_duration,
            "night_work": night_work,
            "break_time": break_time.total_seconds() / 3600,
            "overtime_duration": overtime_duration,
        }

    @classmethod
    def monthly_summary(cls, user, year, month):
        start_date = timezone.datetime(year, month, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        date_range = [start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)]

        total_work_time = 0.0
        total_night_work = 0.0
        total_break_time = 0.0
        total_overtime = 0.0

        for single_date in date_range:
            daily_data = cls.daily_summary(user, single_date.date())
            total_work_time += daily_data["work_duration"]
            total_night_work += daily_data["night_work"]
            total_break_time += daily_data["break_time"]
            total_overtime += daily_data["overtime_duration"]

        return {
            "total_work_time": total_work_time,
            "total_night_work": total_night_work,
            "total_break_time": total_break_time,
            "total_overtime": total_overtime,
        }
