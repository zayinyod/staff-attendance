"""
詳細テーブルの workflow を必須とし、Workflow に移した共通項目を削除する。

逆方向には適用できない [NULL 不可の外部キーを既存の行に戻せないため]
戻す場合は、適用前に複製した DB から復元する。
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0019_move_paid_leave_to_workflow"),
    ]

    operations = [
        migrations.AlterField(
            model_name="paidleave",
            name="workflow",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="attendance.workflow",
            ),
        ),
        migrations.RemoveField(model_name="paidleave", name="user"),
        migrations.RemoveField(model_name="paidleave", name="status"),
        migrations.RemoveField(model_name="paidleave", name="approver"),
        migrations.RemoveField(model_name="paidleave", name="created_at"),
        migrations.RemoveField(model_name="paidleave", name="updated_at"),
        migrations.AlterField(
            model_name="clockcorrect",
            name="workflow",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="attendance.workflow",
            ),
        ),
        migrations.RemoveField(model_name="clockcorrect", name="user"),
        migrations.RemoveField(model_name="clockcorrect", name="status"),
        migrations.RemoveField(model_name="clockcorrect", name="approver"),
        migrations.RemoveField(model_name="clockcorrect", name="created_at"),
        migrations.RemoveField(model_name="clockcorrect", name="updated_at"),
        migrations.AlterField(
            model_name="fare",
            name="workflow",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="attendance.workflow",
            ),
        ),
        migrations.RemoveField(model_name="fare", name="user"),
        migrations.RemoveField(model_name="fare", name="status"),
        migrations.RemoveField(model_name="fare", name="approver"),
        migrations.RemoveField(model_name="fare", name="created_at"),
        migrations.RemoveField(model_name="fare", name="updated_at"),
        migrations.AlterField(
            model_name="payperiod",
            name="workflow",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="attendance.workflow",
            ),
        ),
        migrations.RemoveField(model_name="payperiod", name="user"),
        migrations.RemoveField(model_name="payperiod", name="status"),
        migrations.RemoveField(model_name="payperiod", name="approver"),
        migrations.RemoveField(model_name="payperiod", name="created_at"),
        migrations.RemoveField(model_name="payperiod", name="updated_at"),
    ]
