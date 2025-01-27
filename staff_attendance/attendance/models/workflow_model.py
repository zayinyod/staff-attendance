from django.db import models
from django.conf import settings
from util.now import Now
from .code_master import CodeMaster

class WorkflowBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_workflows_requested",
    )
    status = models.ForeignKey(
        CodeMaster,
        on_delete=models.PROTECT,
        limit_choices_to={"code_type": "workflow_status"},
        default="0",
        related_name="%(class)s_workflows_status",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_workflows_approved",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class PaidLeave(WorkflowBase):
    start_date = models.DateField(default=Now.date_str)
    end_date = models.DateField(default=Now.date_str)
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"[{self.user.username}] {self.start_date} - {self.end_date}"

class ClockCorrect(WorkflowBase):
    original_time = models.TimeField()
    corrected_time = models.TimeField()
    date = models.DateField()
    reason = models.TextField(null=True, blank=True)

class Fare(WorkflowBase):
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    route = models.CharField(max_length=255)

class PayPeriod(WorkflowBase):
    month = models.DateField()
