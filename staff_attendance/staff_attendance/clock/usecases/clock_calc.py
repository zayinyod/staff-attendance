import calendar
from datetime import date, datetime, timedelta
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
            "punch_in": Now.time_str(in_datetime),
            "punch_out": Now.time_str(out_datetime),
            "work_duration": work_duration,
            "night_work": night_work,
            "break_time": break_time.total_seconds() / 3600,
            "overtime_duration": overtime_duration,
        }

    @classmethod
    def month_dates(cls, year, month) -> list:
        """
        指定した年月に含まれる全ての日付を返す
        """
        days_in_month = calendar.monthrange(year, month)[1]

        return [date(year, month, day) for day in range(1, days_in_month + 1)]

    @classmethod
    def monthly_detail(cls, user, year, month) -> dict:
        """
        日ごとの集計と、それを合算した月次合計をあわせて返す
        """
        daily_records = [
            {"date": single_date, "summary": cls.daily_summary(user, single_date)}
            for single_date in cls.month_dates(year, month)
        ]

        return {
            "daily_records": daily_records,
            "totals": cls.total_of(daily_records),
        }

    @classmethod
    def total_of(cls, daily_records) -> dict:
        """
        日次集計のリストを合算する
        """
        totals = {
            "total_work_time": 0.0,
            "total_night_work": 0.0,
            "total_break_time": 0.0,
            "total_overtime": 0.0,
        }
        summary_keys = {
            "total_work_time": "work_duration",
            "total_night_work": "night_work",
            "total_break_time": "break_time",
            "total_overtime": "overtime_duration",
        }

        for record in daily_records:
            for total_key, summary_key in summary_keys.items():
                totals[total_key] += record["summary"][summary_key]

        return totals

    @classmethod
    def monthly_summary(cls, user, year, month) -> dict:
        return cls.monthly_detail(user, year, month)["totals"]
