from django.db import models
from django.conf import settings
from decimal import Decimal
from util.now import Now

class Clock(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clocks",
        verbose_name="username",
    )
    date_stamp = models.DateField(
        default=Now.date,
        verbose_name="date",
    )
    time_stamp = models.TimeField(
        default=Now.time,
        verbose_name="time",
    )
    clock = models.CharField(
        max_length=20,
        default="In",
        choices=[
            ("IN", "In"),
            ("OUT", "Out"),
        ],
        verbose_name="in/out",
    )
    break_time = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("1.00"),
        verbose_name="breaktime",
    )
    location = models.CharField(
        max_length=20,
        default="Office",
        choices=[
            ("office", "Office"),
            ("telework", "Telework"),
        ],
        verbose_name="location",
    )

    class Meta:
        unique_together = ("user", "date_stamp", "clock")

    def __str__(self):
        return f"[{self.clock}] {self.date_stamp}: {self.user.username}"
