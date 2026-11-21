"""
PaidLeave の共通項目を Workflow に移す。

承認画面に表示する ID を変えないため、Workflow.id は PaidLeave.id と同じ値とする。
ClockCorrect / Fare / PayPeriod はデータがないため対象外とする [移行前に件数を確認する]
"""
from django.db import migrations

PAID_LEAVE_TYPE_CODE = "0"


def move_paid_leave_to_workflow(apps, schema_editor):
    CodeMaster = apps.get_model("attendance", "CodeMaster")
    Workflow = apps.get_model("attendance", "Workflow")
    PaidLeave = apps.get_model("attendance", "PaidLeave")

    for model_name in ["ClockCorrect", "Fare", "PayPeriod"]:
        if apps.get_model("attendance", model_name).objects.exists():
            raise RuntimeError(f"{model_name} has rows; data migration for it is not implemented.")

    paid_leave_type = CodeMaster.objects.get(code_type="workflow_type", code=PAID_LEAVE_TYPE_CODE)

    for paid_leave in PaidLeave.objects.all():
        workflow = Workflow.objects.create(
            id=paid_leave.id,
            workflow_type=paid_leave_type,
            user_id=paid_leave.user_id,
            status_id=paid_leave.status_id,
            approver_id=paid_leave.approver_id,
        )
        # auto_now_add / auto_now は保存時に現在時刻で上書きするため、作成後に元の日時を設定する
        Workflow.objects.filter(id=workflow.id).update(
            created_at=paid_leave.created_at,
            updated_at=paid_leave.updated_at,
        )
        PaidLeave.objects.filter(id=paid_leave.id).update(workflow=workflow)


def move_workflow_to_paid_leave(apps, schema_editor):
    Workflow = apps.get_model("attendance", "Workflow")
    PaidLeave = apps.get_model("attendance", "PaidLeave")

    for paid_leave in PaidLeave.objects.select_related("workflow"):
        workflow = paid_leave.workflow
        PaidLeave.objects.filter(id=paid_leave.id).update(
            user_id=workflow.user_id,
            status_id=workflow.status_id,
            approver_id=workflow.approver_id,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            workflow=None,
        )
    Workflow.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0018_workflow"),
    ]

    operations = [
        migrations.RunPython(move_paid_leave_to_workflow, move_workflow_to_paid_leave),
    ]
