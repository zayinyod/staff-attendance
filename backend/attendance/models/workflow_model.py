from django.db import models
from django.conf import settings
from util.now import Now
from .code_master import CodeMaster


class Workflow(models.Model):
    """
    全種別に共通するワークフローの項目を持つテーブル
    種別ごとの項目は、OneToOne で結び付く詳細テーブルが持つ
    """

    workflow_type = models.ForeignKey(
        CodeMaster,
        on_delete=models.PROTECT,
        limit_choices_to={"code_type": "workflow_type"},
        related_name="workflows_by_type",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workflows_requested",
    )
    status = models.ForeignKey(
        CodeMaster,
        on_delete=models.PROTECT,
        limit_choices_to={"code_type": "workflow_status"},
        related_name="workflows_by_status",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflows_approved",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.id}] {self.workflow_type.description} ({self.user.username})"


class WorkflowDetailBase(models.Model):
    # 逆参照は workflow.paidleave のように小文字のクラス名となる
    workflow = models.OneToOneField(
        Workflow,
        on_delete=models.CASCADE,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True


class PaidLeave(WorkflowDetailBase):
    start_date = models.DateField(default=Now.date_str)
    end_date = models.DateField(default=Now.date_str)
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"[{self.workflow.user.username}] {self.start_date} - {self.end_date}"


class ClockCorrect(WorkflowDetailBase):
    original_time = models.TimeField()
    corrected_time = models.TimeField()
    date = models.DateField()
    reason = models.TextField(null=True, blank=True)


class Fare(WorkflowDetailBase):
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    route = models.CharField(max_length=255)


class PayPeriod(WorkflowDetailBase):
    month = models.DateField()
