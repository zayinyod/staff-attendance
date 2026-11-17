"""
backup_db コマンドのテスト。
一時ディレクトリの SQLite を対象とするため SimpleTestCase を使用。
"""

import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings


class TestBackupDbCommand(SimpleTestCase):

    def setUp(self):
        working_dir = tempfile.TemporaryDirectory()
        self.addCleanup(working_dir.cleanup)
        self.db_path = Path(working_dir.name) / "db.sqlite3"
        self.backup_dir = Path(working_dir.name) / "backups"

        settings_override = override_settings(DB_PATH=self.db_path, DB_BACKUP_DIR=self.backup_dir)
        settings_override.enable()
        self.addCleanup(settings_override.disable)

    def create_database(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute("CREATE TABLE sample (name TEXT)")
        connection.execute("INSERT INTO sample VALUES ('admin')")
        connection.commit()
        connection.close()

    def run_backup(self, *args):
        call_command("backup_db", *args, stdout=StringIO())

    def list_backups(self):
        return sorted(self.backup_dir.glob("db-*.sqlite3"))

    def test_backup_contains_same_data(self):
        """複製に元の DB と同じデータが含まれること"""
        self.create_database()

        self.run_backup()

        backups = self.list_backups()
        self.assertEqual(len(backups), 1)
        connection = sqlite3.connect(backups[0])
        self.assertEqual(connection.execute("SELECT name FROM sample").fetchall(), [("admin",)])
        connection.close()

    def test_old_backups_are_removed_beyond_keep(self):
        """指定した世代数を超えた古い複製が削除されること"""
        self.create_database()
        self.backup_dir.mkdir()
        for name in ["db-20260101-000000-000000.sqlite3", "db-20260102-000000-000000.sqlite3"]:
            (self.backup_dir / name).touch()

        self.run_backup("--keep", "2")

        names = [path.name for path in self.list_backups()]
        self.assertEqual(len(names), 2)
        self.assertNotIn("db-20260101-000000-000000.sqlite3", names)
        self.assertIn("db-20260102-000000-000000.sqlite3", names)

    def test_missing_database_is_skipped(self):
        """DB が存在しない場合は複製を作成しないこと"""
        self.run_backup()

        self.assertFalse(self.backup_dir.exists())
        self.assertFalse(self.db_path.exists())

    def test_keep_must_be_positive(self):
        """--keep に 0 以下を指定した場合はエラーとなること"""
        with self.assertRaises(CommandError):
            self.run_backup("--keep", "0")
