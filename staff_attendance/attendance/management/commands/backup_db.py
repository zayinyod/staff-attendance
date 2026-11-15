"""
SQLite の DB を日時付きのファイル名で複製する。

オンラインバックアップ API を使うため、開発サーバーの稼働中でも整合した複製を取得できる。
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

BACKUP_PREFIX = "db-"
BACKUP_SUFFIX = ".sqlite3"


class Command(BaseCommand):
    help = "SQLite の DB を DB_BACKUP_DIR に複製し、指定した世代数を超えた古い複製を削除する"

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep", type=int, default=10, help="保持する世代数 [既定: 10]"
        )

    def handle(self, *args, **options):
        keep = options["keep"]
        if keep < 1:
            raise CommandError("--keep には 1 以上を指定する")

        source = Path(settings.DB_PATH)
        if not source.exists():
            self.stdout.write(f"DB が存在しないため、バックアップを省略した: {source}")
            return

        backup_dir = Path(settings.DB_BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)
        destination = backup_dir / self.build_backup_name(datetime.now())

        self.copy_database(source, destination)
        removed = self.remove_old_backups(backup_dir, keep)

        self.stdout.write(self.style.SUCCESS(f"バックアップを作成した: {destination}"))
        for path in removed:
            self.stdout.write(f"古いバックアップを削除した: {path}")

    @staticmethod
    def build_backup_name(timestamp):
        # 同一秒内の重複を避けるためマイクロ秒まで含める
        return f"{BACKUP_PREFIX}{timestamp:%Y%m%d-%H%M%S-%f}{BACKUP_SUFFIX}"

    @staticmethod
    def copy_database(source, destination):
        source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
            source_connection.close()

    @staticmethod
    def remove_old_backups(backup_dir, keep):
        # ファイル名が日時順となるため、名前の降順で新しい順に並ぶ
        backups = sorted(
            backup_dir.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"), reverse=True
        )
        expired_backups = backups[keep:]
        for path in expired_backups:
            path.unlink()
        return expired_backups
