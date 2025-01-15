from datetime import datetime, timedelta
import math

class RoundCalculate:
    @classmethod
    def truncate_to_minutes(cls, dt):
        return dt.replace(second=0, microsecond=0)

    @classmethod
    def round_up_seconds(cls, dt, base=15 * 60):
        delta = dt - datetime.min
        result = math.ceil(delta.total_seconds() / base) * base

        return datetime.min + timedelta(seconds=result)

    @classmethod
    def round_down_seconds(cls, dt, base=15 * 60):
        delta = dt - datetime.min
        result = math.floor(delta.total_seconds() / base) * base

        return datetime.min + timedelta(seconds=result)

    @classmethod
    def round_up_hours(cls, dt, base=0.25):
        base_hour = (base * 3600)
        delta = dt - datetime.min
        result = math.ceil(delta.total_seconds() / base_hour) * base_hour

        return datetime.min + timedelta(seconds=result)

    @classmethod
    def round_down_hours(cls, dt, base=0.25):
        base_hour = (base * 3600)
        delta = dt - datetime.min
        result = math.floor(delta.total_seconds() / base_hour) * base_hour

        return datetime.min + timedelta(seconds=result)
