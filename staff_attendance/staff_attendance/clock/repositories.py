from staff_attendance.clock.now import Now
from attendance.models import Clock
from .domains import ClockDomain

class ClockRepository:
    def save(self, clock_entry: ClockDomain):
        clock = Clock(
            user=clock_entry.user,
            date_stamp=clock_entry.date_stamp,
            time_stamp=clock_entry.time_stamp,
            clock=clock_entry.clock,
            break_time=clock_entry.break_time,
            location=clock_entry.location,
        )
        clock.save()

    def get_today_in_record(self, user):
        today = Now.date()
        return Clock.objects.filter(
            user=user,
            date_stamp=today,
            clock="IN",
        ).first()
