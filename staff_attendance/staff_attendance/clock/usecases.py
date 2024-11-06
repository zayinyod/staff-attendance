from .domains import ClockDomain
from .repositories import ClockRepository

class ClockUseCase:
    def __init__(self, user):
        self.user = user
        self.clock_repository = ClockRepository()

    def create_clock_entry(self, cleaned_data):
        clock_entry = ClockDomain(
            user=self.user,
            date_stamp=cleaned_data["date_stamp"],
            time_stamp=cleaned_data["time_stamp"],
            clock=cleaned_data["clock"],
            break_time=cleaned_data["break_time"],
            location=cleaned_data["location"],
        )
        self.clock_repository.save(clock_entry)

    def get_in_breaktime_and_location(self):
        in_record = self.clock_repository.get_today_in_record(self.user)
        if in_record:
            return in_record.break_time, in_record.location
        return None, None
