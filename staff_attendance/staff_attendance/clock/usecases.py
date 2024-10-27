from .domains import ClockDomain
from .repositories import ClockRepository

class ClockUsecase:
    def __init__(self):
        self.clock_repository = ClockRepository()

    def create_clock_entry(self, cleaned_data):
        clock_entry = ClockDomain(
            user=cleaned_data['user'],
            date_stamp=cleaned_data['date_stamp'],
            time_stamp=cleaned_data['time_stamp'],
            clock=cleaned_data['clock'],
            break_time=cleaned_data['break_time'],
            location=cleaned_data['location']
        )
        self.clock_repository.save(clock_entry)
