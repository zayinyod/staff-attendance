"""
テストランナー
"""

from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


class StaticFilesTestRunner(DiscoverRunner):
    """
    テストは DEBUG=False で実行され、ManifestStaticFilesStorage では
    collectstatic で生成したマニフェストが必要になる。
    テスト中は収集を前提としないストレージに切り替える。
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.storage_override = override_settings(STORAGES=TEST_STORAGES)
        self.storage_override.enable()

    def teardown_test_environment(self, **kwargs):
        self.storage_override.disable()
        super().teardown_test_environment(**kwargs)
