"""
CodeMasterの初期データを投入する。

打刻・ワークフローの各機能はこれらのコードを前提とするため、
環境固有のデータではなくシステムの必須マスタとして扱う。
"""
from django.db import migrations


CODE_MASTER_SEEDS = [
    ("clock", "0", "In"),
    ("clock", "1", "Out"),
    ("location", "0", "Office"),
    ("location", "1", "Telework"),
    ("workflow_status", "0", "Pending"),
    ("workflow_status", "1", "Approved"),
    ("workflow_status", "2", "Rejected"),
]


def seed_code_master(apps, schema_editor):
    """
    既存環境にはデータが存在するため、get_or_createで冪等に投入する
    """
    CodeMaster = apps.get_model("attendance", "CodeMaster")

    for code_type, code, description in CODE_MASTER_SEEDS:
        CodeMaster.objects.get_or_create(
            code_type=code_type,
            code=code,
            defaults={"description": description},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0015_alter_clockcorrect_approver_and_more"),
    ]

    operations = [
        # 逆操作は行わない。打刻・申請データがPROTECTで参照しているため、
        # 削除するとProtectedErrorとなり、成功しても参照先を失う。
        migrations.RunPython(seed_code_master, migrations.RunPython.noop),
    ]
