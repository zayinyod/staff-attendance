from django.db import models
from django.conf import settings

class WorkflowBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_workflows",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class PaidLeave(WorkflowBase):
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(null=True, blank=True)

class ClockCorrect(WorkflowBase):
    original_time = models.DateTimeField()
    corrected_time = models.DateTimeField()
    reason = models.TextField(null=True, blank=True)

class Fare(WorkflowBase):
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    destination = models.CharField(max_length=255)

class MonthlyPayPeriod(WorkflowBase):
    month = models.DateField()
