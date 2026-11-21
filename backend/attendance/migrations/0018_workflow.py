"""
ワークフローの共通テーブルを作成し、種別のコードを投入する。

詳細テーブルの workflow は、既存データを 0019 で移行するまで NULL を許可する。
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


WORKFLOW_TYPE_SEEDS = [
    ("workflow_type", "0", "Paid Leave"),
    ("workflow_type", "1", "Clock Correct"),
    ("workflow_type", "2", "Fare"),
    ("workflow_type", "3", "Pay Period"),
]

DETAIL_MODEL_NAMES = ["paidleave", "clockcorrect", "fare", "payperiod"]


def seed_workflow_type(apps, schema_editor):
    CodeMaster = apps.get_model("attendance", "CodeMaster")

    for code_type, code, description in WORKFLOW_TYPE_SEEDS:
        CodeMaster.objects.get_or_create(
            code_type=code_type,
            code=code,
            defaults={"description": description},
        )


def add_workflow_field(model_name):
    return migrations.AddField(
        model_name=model_name,
        name="workflow",
        field=models.OneToOneField(
            null=True,
            on_delete=django.db.models.deletion.CASCADE,
            related_name="%(class)s",
            to="attendance.workflow",
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0017_alter_clock_clock_alter_clock_location"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 逆操作は行わない。0016 と同じく、参照中のコードを削除すると ProtectedError となるため
        migrations.RunPython(seed_workflow_type, migrations.RunPython.noop),
        migrations.CreateModel(
            name="Workflow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "approver",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="workflows_approved",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "status",
                    models.ForeignKey(
                        limit_choices_to={"code_type": "workflow_status"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workflows_by_status",
                        to="attendance.codemaster",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workflows_requested",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "workflow_type",
                    models.ForeignKey(
                        limit_choices_to={"code_type": "workflow_type"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workflows_by_type",
                        to="attendance.codemaster",
                    ),
                ),
            ],
        ),
        *[add_workflow_field(model_name) for model_name in DETAIL_MODEL_NAMES],
    ]
