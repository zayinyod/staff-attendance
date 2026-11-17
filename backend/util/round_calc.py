from datetime import datetime, timedelta
import math


class RoundCalculate:
    """
    時刻の切り捨てや切り上げを行うユーティリティクラス
    """

    @classmethod
    def truncate_to_minutes(cls, dt: datetime) -> datetime:
        """
        分単位に切り捨てる
        """
        return dt.replace(second=0, microsecond=0)

    @classmethod
    def round_up_seconds(cls, dt: datetime, base: int = 15 * 60) -> datetime:
        """
        秒単位で切り上げる
        """
        delta = dt - datetime.min
        result = math.ceil(delta.total_seconds() / base) * base

        return datetime.min + timedelta(seconds=result)

    @classmethod
    def round_down_seconds(cls, dt: datetime, base: int = 15 * 60) -> datetime:
        """
        秒単位で切り捨てる
        """
        delta = dt - datetime.min
        result = math.floor(delta.total_seconds() / base) * base

        return datetime.min + timedelta(seconds=result)

    @classmethod
    def round_up_hours(cls, dt: datetime, base: float = 0.25) -> datetime:
        """
        時間単位で切り上げる
        """
        base_hour = (base * 3600)
        delta = dt - datetime.min
        result = math.ceil(delta.total_seconds() / base_hour) * base_hour

        return datetime.min + timedelta(seconds=result)

    @classmethod
    def round_down_hours(cls, dt: datetime, base: float = 0.25) -> datetime:
        """
        時間単位で切り捨てる
        """
        base_hour = (base * 3600)
        delta = dt - datetime.min
        result = math.floor(delta.total_seconds() / base_hour) * base_hour

        return datetime.min + timedelta(seconds=result)
