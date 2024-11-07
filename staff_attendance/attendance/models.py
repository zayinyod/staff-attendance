from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django.utils import timezone
from decimal import Decimal
from staff_attendance.clock.now import Now

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="department")

    def __str__(self):
        return f"[{self.id}] {self.name}"

def create_id():
    while True:
        new_id = get_random_string(6)
        if not User.objects.filter(user_id=new_id).exists():
            return new_id

class User(AbstractUser):
    user_id = models.CharField(
        primary_key=True,
        default=create_id,
        max_length=6,
        editable=False,
        verbose_name="user id",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name="users",
        verbose_name="department",
    )

    def __str__(self):
        return f"[{self.user_id}] {self.username}"

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

# class workflow:
