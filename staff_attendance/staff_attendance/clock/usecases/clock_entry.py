from ..domains import ClockDomain
from ..repositories import ClockRepository

class ClockEntry:
    clock_repository = ClockRepository()

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
    def clock_codes(cls) -> dict:
        return cls.clock_repository.clock_codes()

    @classmethod
    def has_in_record(cls, user, date) -> bool:
        """
        指定日にIN打刻が存在するかを判定する
        """
        return cls.clock_repository.get_clock(user, date).get("in_clock") is not None

    @classmethod
    def get_in_breaktime_and_location(cls, user):
        in_record = cls.clock_repository.get_today_in_record(user)
        if in_record:
            return in_record.break_time, in_record.location, True
        else:
            return None, None, False
