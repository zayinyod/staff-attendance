"""
静的ファイルのストレージ
"""

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ModuleAwareManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    ファイル名に内容のハッシュを付与して配信する。
    ES Modules の import 文の参照先もハッシュ付きの名前に書き換え、
    import 先の古いファイルが読み込まれることを防ぐ。
    """

    support_js_module_import_aggregation = True
