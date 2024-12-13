from django.db import models
from django.contrib.auth.models import AbstractUser

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="department")

    def __str__(self):
        return f"[{self.id}] {self.name}"

class User(AbstractUser):
    user_id = models.CharField(
        primary_key=True,
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
