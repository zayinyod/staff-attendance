"""
静的ファイルの配信設定のテスト。
DB 接続が不要なため SimpleTestCase を使用。
"""

import json
import re
import tempfile
from pathlib import Path
from django.conf import settings
from django.core.management import call_command, get_commands
from django.templatetags.static import static
from django.test import RequestFactory, SimpleTestCase, override_settings
from attendance.management.commands.runserver import Command as RunserverCommand
from util.static_handlers import NoCacheStaticFilesHandler

PRODUCTION_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "util.storages.ModuleAwareManifestStaticFilesStorage"},
}


class TestNoCacheStaticFilesHandler(SimpleTestCase):

    def test_static_response_has_no_cache_header(self):
        """静的ファイルの応答に Cache-Control: no-cache が付与されること"""
        handler = NoCacheStaticFilesHandler(application=None)
        request = RequestFactory().get(f"/{settings.STATIC_URL}js/toggle.js")

        response = handler.get_response(request)
        response.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-cache")


class TestRunserverCommand(SimpleTestCase):

    def test_runserver_is_provided_by_attendance(self):
        """runserver は attendance の拡張版が使用されること"""
        self.assertEqual(get_commands()["runserver"], "attendance")

    def test_handler_is_replaced(self):
        """静的ファイルの配信ハンドラが no-cache 版に差し替えられること"""
        handler = RunserverCommand().get_handler(use_static_handler=True, insecure_serving=True)
        self.assertIsInstance(handler, NoCacheStaticFilesHandler)


class TestManifestStaticFilesStorage(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.static_root = tempfile.TemporaryDirectory()
        cls.storage_override = override_settings(
            STATIC_ROOT=cls.static_root.name, STORAGES=PRODUCTION_STORAGES
        )
        cls.storage_override.enable()
        call_command("collectstatic", interactive=False, verbosity=0)
        manifest = json.loads((Path(cls.static_root.name) / "staticfiles.json").read_text())
        cls.hashed_names = manifest["paths"]

    @classmethod
    def tearDownClass(cls):
        cls.storage_override.disable()
        cls.static_root.cleanup()
        super().tearDownClass()

    def test_static_url_contains_hash(self):
        """static タグがハッシュ付きの URL を返すこと"""
        self.assertRegex(static("js/toggle.js"), r"js/toggle\.[0-9a-f]{12}\.js$")

    def test_module_import_points_to_hashed_file(self):
        """ES Modules の import 先がハッシュ付きの名前に書き換えられること"""
        hashed_toggle = Path(self.static_root.name) / self.hashed_names["js/toggle.js"]
        hashed_actions = Path(self.hashed_names["js/shortcuts/actions.js"]).name

        # 書き換え後の参照先は二重引用符で出力される
        imports = re.findall(r"from [\"']([^\"']+)[\"']", hashed_toggle.read_text())
        self.assertEqual(imports, [f"./shortcuts/{hashed_actions}"])
