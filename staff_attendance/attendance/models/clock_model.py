from django.db import models
from django.conf import settings
from decimal import Decimal
from util.now import Now
from .code_master import CodeMaster

class Clock(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clocks",
        verbose_name="username",
    )
    date_stamp = models.DateField(
        default=Now.date_str,
        verbose_name="date",
    )
    time_stamp = models.TimeField(
        default=Now.time_str,
        verbose_name="time",
    )
    clock = models.ForeignKey(
        CodeMaster,
        on_delete=models.PROTECT,
        limit_choices_to={"code_type": "clock"},
        default="0",
        related_name="clock_codes",
        verbose_name="in/out",
    )
    break_time = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("1.00"),
        verbose_name="breaktime",
    )
    location = models.ForeignKey(
        CodeMaster,
        on_delete=models.PROTECT,
        limit_choices_to={"code_type": "location"},
        default="0",
        related_name="location_codes",
    )

    class Meta:
        unique_together = ("user", "date_stamp", "clock")

    def __str__(self):
        return f"[{self.clock.description}] {self.date_stamp}: {self.user.username}"
